from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch, Mock
from uuid import uuid4

from django.db import DatabaseError, transaction
from django.test import SimpleTestCase, RequestFactory
from django.utils import timezone
from fastapi import HTTPException
from fastapi.testclient import TestClient

from apps.api.backend_api import integrity_service
from apps.api.backend_api.db import get_connection
from apps.api.backend_api.main import app, _market_lifecycle_engine
from apps.api.backend_api.schemas import AdminMarketResolvePayload
from apps.web.django.accounts import api_client
from apps.web.django.markets.models import Market, MarketResolutionRequest, IntegrityLedgerEvent, Prediction, UserNotification
from apps.web.django.markets.views import integrity
from tests.test_cases import AppendOnlyTransactionTestCase
from tests import test_integrity_ledger as fixtures


class ResolutionReliabilityTests(AppendOnlyTransactionTestCase):
    setUp = fixtures.IntegrityLedgerIntegrationTests.setUp
    tearDown = fixtures.IntegrityLedgerIntegrationTests.tearDown
    _register = fixtures.IntegrityLedgerIntegrationTests._register

    def prepare(self, stake_amount=25):
        self.market = Market.objects.get(slug='openai-gpt6-2026')
        self.option = self.market.options.order_by('display_order', 'id').first()
        response = self.client.post(f'/markets/{self.market.slug}/predict', headers=self.user_headers,
                                    json={'option_id': self.option.id, 'stake_amount': stake_amount, 'client_locale': 'pt-br'})
        self.assertEqual(response.status_code, 201, response.text)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM gotrendlabs_markets WHERE id=%s FOR UPDATE', (self.market.id,))
                _market_lifecycle_engine(cursor, None).lock_market_automatically(cursor.fetchone(), self.market.slug, now=timezone.now())
        self.url = f'/admin/markets/{self.market.slug}/resolve'
        self.payload = dict(expected_market_id=self.market.id, idempotency_key=str(uuid4()),
                            winning_option_id=self.option.id, note='Resultado conferido',
                            resolved_at=(timezone.now()-timedelta(days=2)).isoformat(), resolution_timezone='UTC')
        return self.payload

    def resolve(self, payload=None, headers=None):
        return self.client.post(self.url, json=payload or self.payload, headers=headers or self.staff_headers)

    def receipt(self, headers=None):
        return self.client.get(f'/admin/markets/{self.market.slug}/resolution-requests/{self.payload["idempotency_key"]}',
                               params={'expected_market_id': self.market.id}, headers=headers or self.staff_headers)

    def test_replay_and_confirmation_do_not_duplicate_effects_and_keep_full_window(self):
        self.prepare()
        before = timezone.now()
        first = self.resolve()
        self.assertEqual(first.status_code, 200, first.text)
        self.market.refresh_from_db()
        event = IntegrityLedgerEvent.objects.get(market=self.market, event_type='market_resolved')
        self.assertGreaterEqual(event.occurred_at, before)
        self.assertEqual(self.market.seal_due_at, event.occurred_at+timedelta(hours=12))
        self.assertLess(self.market.resolved_at, before-timedelta(days=1))
        second = self.resolve()
        self.assertEqual(second.status_code, 200, second.text)
        self.assertEqual(self.receipt().status_code, 200)
        from apps.api.backend_api.daemon_services import seal_due_markets
        sealed = seal_due_markets(now=self.market.seal_due_at+timedelta(seconds=1))
        self.assertEqual(len(sealed['sealed']), 1)
        self.assertEqual(self.resolve().json()['status'], 'sealed')
        self.assertEqual(self.receipt().json()['status'], 'sealed')
        self.assertEqual(MarketResolutionRequest.objects.filter(market=self.market).count(), 1)
        with self.assertRaises(DatabaseError), transaction.atomic():
            MarketResolutionRequest.objects.filter(market=self.market).update(request_hash='0'*64)
        self.assertEqual(IntegrityLedgerEvent.objects.filter(market=self.market, event_type='market_resolved').count(), 1)
        self.assertEqual(UserNotification.objects.filter(market=self.market, event_type='market_resolved').count(), 1)
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT entry_type,count(*) AS n FROM gotrendlabs_wallet_ledger WHERE reference_type='prediction' AND reference_id IN (SELECT id::text FROM gotrendlabs_predictions WHERE market_id=%s) GROUP BY entry_type", (self.market.id,))
                self.assertEqual({r['entry_type']:r['n'] for r in cursor.fetchall()}, {'prediction_stake_lock':1,'prediction_refund':1,'prediction_payout':1})

    def test_conflicting_payload_key_identity_and_auth_are_rejected(self):
        self.prepare()
        self.assertEqual(self.receipt().status_code, 404)
        self.assertEqual(self.receipt(self.user_headers).status_code, 403)
        self.assertEqual(self.resolve(headers=self.user_headers).status_code, 403)
        self.assertEqual(self.resolve({**self.payload, 'expected_market_id': self.market.id+999}).status_code, 409)
        self.assertEqual(self.resolve().status_code, 200)
        changed = self.resolve({**self.payload, 'note':'Outro resultado'})
        self.assertEqual(changed.status_code, 409)
        self.assertEqual(changed.json()['detail']['code'], 'resolution_request_conflict')
        self.assertEqual(self.resolve({**self.payload, 'idempotency_key':str(uuid4())}).status_code, 409)

    def test_same_key_after_undo_cannot_reapply_and_new_resolution_gets_new_window(self):
        self.prepare()
        self.assertEqual(self.resolve().status_code, 200)
        first_due = Market.objects.get(pk=self.market.id).seal_due_at
        undone = self.client.post(f'/admin/markets/{self.market.slug}/cancel', headers=self.staff_headers,
                                  json={'expected_market_id':self.market.id,'note':'Revisão operacional'})
        self.assertEqual(undone.status_code, 200, undone.text)
        self.assertEqual(self.resolve().json()['detail']['code'], 'resolution_request_superseded')
        self.assertEqual(self.receipt().status_code, 409)
        self.assertEqual(self.resolve({**self.payload,'idempotency_key':str(uuid4())}).status_code, 200)
        self.market.refresh_from_db()
        self.assertGreater(self.market.seal_due_at, first_due)
        self.assertEqual(self.receipt().status_code, 409)

    def test_signing_failure_rolls_back_receipt_liquidation_and_state(self):
        self.prepare()
        with patch.object(integrity_service._signer, 'sign', side_effect=integrity_service.IntegritySigningError('unavailable')):
            response = self.resolve()
        self.assertEqual(response.status_code, 503, response.text)
        self.market.refresh_from_db()
        self.assertEqual(self.market.status, 'locked')
        self.assertEqual(Prediction.objects.get(market=self.market).status, 'open')
        self.assertFalse(MarketResolutionRequest.objects.exists())
        self.assertFalse(IntegrityLedgerEvent.objects.filter(market=self.market,event_type='market_resolved').exists())
        self.assertEqual(self.resolve().status_code, 200)

    def test_engine_rechecks_stale_state_under_lock(self):
        self.prepare()
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM gotrendlabs_markets WHERE id=%s', (self.market.id,))
                stale = cursor.fetchone()
        self.assertEqual(self.resolve().status_code, 200)
        with self.assertRaises(HTTPException) as caught:
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    _market_lifecycle_engine(cursor, None).resolve_market(stale,self.market.slug,AdminMarketResolvePayload(**self.payload))
        self.assertEqual(caught.exception.status_code, 409)

    def race(self, second):
        other_headers = self._register('Other Staff','other-resolution-staff@example.com')
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE gotrendlabs_users SET is_staff=true WHERE email='other-resolution-staff@example.com'")
                cursor.execute("UPDATE gotrendlabs_auth_sessions SET mfa_verified_at=NOW(),mfa_method='totp' WHERE user_id=(SELECT id FROM gotrendlabs_users WHERE email='other-resolution-staff@example.com')")
        barrier = Barrier(2)
        def send(payload, headers):
            with TestClient(app) as client:
                barrier.wait(timeout=10)
                return client.post(self.url,json=payload,headers=headers)
        with ThreadPoolExecutor(max_workers=2) as pool:
            a=pool.submit(send,self.payload,self.staff_headers)
            b=pool.submit(send,second,other_headers)
            responses=[a.result(timeout=30),b.result(timeout=30)]
        return responses

    def test_concurrent_different_results_only_one_is_applied(self):
        self.prepare()
        other_option = self.market.options.exclude(pk=self.option.id).first()
        responses = self.race({**self.payload, 'idempotency_key':str(uuid4()), 'winning_option_id':other_option.id})
        self.assertEqual(sorted(r.status_code for r in responses),[200,409], [r.text for r in responses])
        self.market.refresh_from_db()
        prediction=Prediction.objects.get(market=self.market)
        self.assertEqual(prediction.won,self.market.winning_option_id==prediction.market_option_id)
        self.assertEqual(MarketResolutionRequest.objects.filter(market=self.market).count(),1)
        self.assertEqual(IntegrityLedgerEvent.objects.filter(market=self.market,event_type='market_resolved').count(),1)

    def test_concurrent_same_request_returns_success_once_per_effect(self):
        self.prepare()
        responses = self.race(self.payload)
        self.assertEqual([r.status_code for r in responses], [200,200], [r.text for r in responses])
        self.assertEqual(MarketResolutionRequest.objects.filter(market=self.market).count(),1)
        self.assertEqual(IntegrityLedgerEvent.objects.filter(market=self.market,event_type='market_resolved').count(),1)
        self.assertEqual(UserNotification.objects.filter(market=self.market,event_type='market_resolved').count(),1)


class ResolutionClientTests(SimpleTestCase):
    def test_socket_timeout_is_classified_as_uncertain_transport(self):
        with patch.object(api_client, '_http_urlopen', side_effect=TimeoutError()):
            with self.assertRaises(api_client.APITransportError):
                api_client._request('POST', '/admin/markets/slug/resolve', {})

    def test_timeout_reconciles_once_without_resending_post(self):
        result={'title':'Mercado','status':'resolved'}
        with patch.object(api_client,'_request',side_effect=[api_client.APITransportError('timeout',503),result]) as request:
            actual=api_client.admin_resolve_market('token','slug',1,expected_market_id=3,idempotency_key='key')
        self.assertEqual(actual,result)
        self.assertEqual([c.args[0] for c in request.call_args_list],['POST','GET'])
        self.assertEqual(request.call_args_list[0].kwargs['timeout'],15)

    def test_unknown_confirmation_never_claims_rollback_or_resends(self):
        for failure in (api_client.AuthAPIError('unknown',404),api_client.APITransportError('timeout',503)):
            with self.subTest(code=failure.status_code), patch.object(api_client,'_request',side_effect=[api_client.APITransportError('timeout',503),failure]) as request:
                with self.assertRaisesMessage(api_client.AuthAPIError,'ainda não foi possível confirmar'):
                    api_client.admin_resolve_market('token','slug',1,expected_market_id=3,idempotency_key='key')
                self.assertEqual(request.call_count,2)

    def test_domain_error_is_not_treated_as_transport_failure(self):
        with patch.object(api_client,'_request',side_effect=api_client.AuthAPIError('conflito',409)) as request:
            with self.assertRaisesMessage(api_client.AuthAPIError,'conflito'):
                api_client.admin_resolve_market('token','slug',1,expected_market_id=3,idempotency_key='key')
        self.assertEqual(request.call_count,1)

    def test_form_preserves_identity_and_key_on_error(self):
        from apps.web.django.admin_ops.forms import MarketResolutionForm
        key=uuid4()
        form=MarketResolutionForm({'expected_market_id':12,'idempotency_key':str(key),'note':''},market={'market_id':99})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.cleaned_data['expected_market_id'],12)
        self.assertEqual(form.cleaned_data['idempotency_key'],key)

    def test_integrity_confirms_records_before_seal_but_not_when_pending_or_failed(self):
        market={'slug':'market','title':'Market','status':'resolved'}
        proof={'status':'resolved_pending_seal','definition':{}}
        valid={'overall_valid':True,'verification_status':'verified','prediction_commitments_valid':True,'result_matches_current':True}
        for verification,positive in [(valid,True),({**valid,'overall_valid':None,'verification_status':'pending'},False),({**valid,'overall_valid':False,'prediction_commitments_valid':False,'result_matches_current':False,'verification_status':'failed'},False)]:
            request=RequestFactory().get('/integrity/?modal=1')
            request.session={}
            with patch('apps.web.django.markets.views.is_authenticated',return_value=False),patch('apps.web.django.markets.views.get_market',return_value=market),patch('apps.web.django.markets.views.get_market_integrity',return_value=proof),patch('apps.web.django.markets.views.verify_market_integrity',return_value=verification):
                response=integrity(request,'market')
            html=response.content.decode()
            self.assertEqual('Comprovantes verificados' in html,positive)
            self.assertEqual('Resultado verificado' in html,positive)
            self.assertIn('Finalização prevista',html)
            if verification['verification_status']=='failed':self.assertIn('Diferença detectada',html)

    def test_admin_consult_only_reads_confirmation_and_keeps_key_after_error(self):
        from apps.web.django.admin_ops.views import resolution_action
        key=str(uuid4())
        request=RequestFactory().post('/admin-ops/resolution/market/resolve/', {
            'expected_market_id':3, 'idempotency_key':key, 'winning_option_id':1,
            'source_url':'https://example.com/result','note':'Conferido',
            'resolved_at':'2026-10-25T10:42','resolution_timezone':'UTC','check_resolution':'1',
        })
        request.session={'auth_api_token':'fixture','auth_api_user':{'id':1,'is_staff':True}}
        market={'market_id':3,'slug':'market','title':'Mercado','options':[{'id':1,'label':'SIM'}]}
        with patch('apps.web.django.admin_ops.views.admin_get_market',return_value=market), patch('apps.web.django.admin_ops.views.admin_resolve_market') as resolve, patch('apps.web.django.admin_ops.views.admin_get_resolution_request',side_effect=api_client.AuthAPIError('Ainda não confirmado',404)) as check, patch('apps.web.django.admin_ops.views.render') as render:
            resolution_action(request,action='resolve',slug='market')
        resolve.assert_not_called()
        check.assert_called_once()
        context=render.call_args.args[2]
        self.assertEqual(str(context['form']['idempotency_key'].value()),key)
        self.assertEqual(str(context['form']['expected_market_id'].value()),'3')
        self.assertIn('Ainda não confirmado',context['admin_error'])
