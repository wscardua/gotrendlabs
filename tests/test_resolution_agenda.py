import copy
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from django.test import SimpleTestCase
from django.core.management.base import CommandError
from fastapi import HTTPException
from pydantic import ValidationError
from apps.api.backend_api import resolution_schedule as s, integrity_service as integrity
from apps.api.backend_api.db import get_connection
from apps.api.backend_api.main import _market_lifecycle_engine
from apps.web.django.markets.models import Market, MarketCategory, MarketSubcategory, MarketOption, IntegrityLedgerEvent, MarketIntegrityDefinition
from apps.web.django.markets.management.commands.migrate_resolution_agenda import apply_inventory
from tests.test_cases import AppendOnlyTransactionTestCase

UTC = timezone.utc
NOW = datetime(2026,10,17,20,tzinfo=UTC)

def agenda(now=NOW):
    return dict(close_at=now-timedelta(days=2),expected_resolution_at=now+timedelta(days=1),schedule_timezone='America/Sao_Paulo',status='locked',schedule_version=1)


class AgendaRulesTests(SimpleTestCase):
    def test_expected_precision(self):
        m=agenda()
        self.assertEqual(s.classification(m,now=m['expected_resolution_at'])['code'],'resolution_scheduled')
        self.assertEqual(s.classification(m,now=m['expected_resolution_at']+timedelta(microseconds=1))['code'],'resolution_overdue')

    def test_open_expired_is_inconsistent_not_locked(self):
        self.assertEqual(s.classification({**agenda(),'status':'open'},now=NOW)['code'],'closure_inconsistent')

    def test_locked_is_not_overdue_because_close_passed(self):
        self.assertEqual(s.classification(agenda(),now=NOW)['code'],'resolution_scheduled')

    def test_no_fabricated_dates_or_no_deadline_claim(self):
        self.assertEqual(s.classification({'status':'locked'},now=NOW)['code'],'schedule_pending')
        self.assertIsNone(s.ScheduleFields().expected_resolution_at)
        for status in s.TERMINAL:
            self.assertEqual(s.classification({'status':status},now=NOW)['code'],'terminal')

    def test_draft_incomplete_publication_rejected(self):
        s.validate_schedule({})
        with self.assertRaises(HTTPException):s.validate_schedule({},required=True)
        s.validate_schedule(agenda(),required=True,publishing=True,now=NOW)
        with self.assertRaises(HTTPException):s.validate_schedule(agenda(),required=True,publishing=True,now=NOW+timedelta(days=1))

    def test_invalid_order_and_zone(self):
        for changed in [dict(expected_resolution_at=agenda()['close_at']),dict(schedule_timezone='Invalid/Zone'),dict(expected_resolution_at=NOW.replace(tzinfo=None))]:
            with self.subTest(changed=changed),self.assertRaises(HTTPException):s.validate_schedule({**agenda(),**changed})

    def test_offset_represents_instant(self):
        value=s.ScheduleFields(expected_resolution_at='2026-10-18T00:00:00-03:00',schedule_timezone='America/Sao_Paulo')
        self.assertEqual(value.expected_resolution_at.astimezone(UTC).hour,3)
        with self.assertRaises(ValidationError):s.ScheduleFields(expected_resolution_at='2026-10-18T12:00:00')

    def test_contract_timeline_separates_steam_and_never_completes_by_time(self):
        from apps.web.django.admin_ops.views import _build_contract_timeline
        m={**agenda(),'slug':'steam','created_at':'2026-10-01T00:00:00Z','close_at':'2026-10-16T02:59:00Z','expected_resolution_at':'2026-11-04T15:00:00Z','resolution_schedule':{'code':'resolution_scheduled','label':'Apuração prevista'}}
        timeline=_build_contract_timeline([m],today=NOW);row=timeline['rows'][0]
        self.assertTrue(timeline['has_today']);self.assertEqual(row['bar_progress_width'],0)
        self.assertEqual(len(row['markers']),3)
        self.assertFalse(any(p['state']=='done' for p in row['phase_steps'] if p['label']=='Resolução prevista'))
        self.assertNotEqual(row['markers'][1]['position'],row['markers'][-1]['position'])

    def test_editor_form_has_only_forecast_and_timezone_for_schedule(self):
        from apps.web.django.admin_ops.forms import AdminMarketForm
        fields=AdminMarketForm().fields
        self.assertIn('expected_resolution_at',fields)
        self.assertIn('schedule_timezone',fields)
        self.assertNotIn('evidence_cutoff_at',fields)
        self.assertNotIn('evidence_recovery_deadline_at',fields)



class AgendaPersistenceTests(AppendOnlyTransactionTestCase):
    def setUp(self):
        self.previous=integrity._signer;integrity._signer=integrity._EphemeralSigner()
        self.addCleanup(setattr,integrity,'_signer',self.previous)
        now=datetime.now(UTC)
        c=MarketCategory.objects.create(name='Agenda',slug='agenda')
        sub=MarketSubcategory.objects.create(category=c,name='Agenda',slug='agenda')
        values=agenda(now);values.pop('schedule_version')
        self.market=Market.objects.create(category=c,subcategory=sub,slug='agenda-market',title='Agenda?',published_at=now,**values)
        self.option=MarketOption.objects.create(market=self.market,label='SIM',probability_exact=50)
        with get_connection() as conn:
            with conn.cursor() as cur:integrity.register_market_definition(cur,self.market.id,occurred_at=now)
        self.definition=MarketIntegrityDefinition.objects.get(market=self.market)

    def register(self):
        with get_connection() as conn:
            with conn.cursor() as cur:s.register(cur,self.market.id,actor_id=None)
        self.market.refresh_from_db()

    def inventory(self):
        return {'schema':'gtl-resolution-agenda/v2','inventory_id':'reviewed-test','markets':[dict(market_id=self.market.id,slug=self.market.slug,status='locked',definition_hash=self.definition.payload_hash,definition_version=1,editorial_revision=None,expected_schedule_version=0,reviewed=True,reviewer='human-test',reviewed_at=NOW.isoformat(),proposed={k:getattr(self.market,k).isoformat() if k in s.DATES else getattr(self.market,k) for k in s.FIELDS},sources={k:{'origin':'explicit_text_candidate','excerpt':'Exact test fixture evidence','source':'isolated fixture'} for k in s.DATES},reason='Revisado em fixture isolada')]}

    def test_append_only_complement_preserves_definition_bytes(self):
        before=(bytes(self.definition.canonical_payload),self.definition.payload_hash,bytes(self.definition.signature))
        self.register();self.definition.refresh_from_db()
        self.assertEqual(before,(bytes(self.definition.canonical_payload),self.definition.payload_hash,bytes(self.definition.signature)))
        self.assertEqual(self.market.original_expected_resolution_at,self.market.expected_resolution_at)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM gotrendlabs_markets WHERE id=%s',(self.market.id,))
                current=cur.fetchone()
                self.assertTrue(integrity.verify_market_integrity_records(cur,current)['market_valid'])
        with get_connection() as conn:
            with conn.cursor() as cur:self.assertEqual(s.verify(cur,{'id':self.market.id}),[])

    def test_reschedule_preserves_original_and_concurrency(self):
        self.register();original=self.market.expected_resolution_at
        payload=s.Reschedule(expected_market_id=self.market.id,expected_version=1,expected_resolution_at=original+timedelta(hours=1),reason='Fonte indisponível')
        with get_connection() as conn:
            with conn.cursor() as cur:s.reschedule(cur,self.market.id,payload,actor_id=None)
        self.market.refresh_from_db();self.assertEqual(self.market.original_expected_resolution_at,original);self.assertEqual(self.market.schedule_version,2)
        with self.assertRaises(HTTPException) as exc,get_connection() as conn:
            with conn.cursor() as cur:s.reschedule(cur,self.market.id,payload,actor_id=None)
        self.assertEqual(exc.exception.status_code,409)
        with get_connection() as conn:
            with conn.cursor() as cur:self.assertEqual(s.verify(cur,{'id':self.market.id}),[])

    def test_signer_failure_rolls_back_projection_and_history(self):
        self.register();before=IntegrityLedgerEvent.objects.count()
        payload=s.Reschedule(expected_market_id=self.market.id,expected_version=1,expected_resolution_at=self.market.expected_resolution_at+timedelta(hours=1),reason='Retry')
        with patch.object(integrity._signer,'sign',side_effect=RuntimeError('signer unavailable')):
            with self.assertRaises(RuntimeError),get_connection() as conn:
                with conn.cursor() as cur:s.reschedule(cur,self.market.id,payload,actor_id=None)
        self.market.refresh_from_db();self.assertEqual(self.market.schedule_version,1);self.assertEqual(IntegrityLedgerEvent.objects.count(),before)

    def test_projection_tampering_detected(self):
        self.register();Market.objects.filter(id=self.market.id).update(expected_resolution_at=self.market.expected_resolution_at+timedelta(minutes=1))
        with get_connection() as conn:
            with conn.cursor() as cur:
                self.assertEqual(s.verify(cur,{'id':self.market.id}),['schedule_projection_changed'])
                cur.execute('SELECT * FROM gotrendlabs_markets WHERE id=%s',(self.market.id,))
                result=integrity.verify_market_integrity_records(cur,cur.fetchone())
                self.assertFalse(result['market_valid'])
                self.assertFalse(result['overall_valid'])

    def test_terminal_rejected_and_undo_preserves_schedule(self):
        self.register()
        for status in s.TERMINAL:
            Market.objects.filter(id=self.market.id).update(status=status)
            with self.assertRaises(HTTPException),get_connection() as conn:
                with conn.cursor() as cur:s.reschedule(cur,self.market.id,s.Reschedule(expected_market_id=self.market.id,expected_version=1,expected_resolution_at=self.market.expected_resolution_at+timedelta(hours=1),reason='No'),actor_id=None)
        Market.objects.filter(id=self.market.id).update(status='locked')
        with get_connection() as conn:
            with conn.cursor() as cur:self.assertEqual(s.verify(cur,{'id':self.market.id}),[])

    def test_resolution_expected_is_not_a_gate(self):
        self.register()
        self.assertGreater(self.market.expected_resolution_at,datetime.now(UTC))
        with get_connection() as conn:
            with conn.cursor() as cur:s.require_resolution(cur,self.market.id)

    def test_dry_run_no_write_apply_idempotent_stale_refused(self):
        inv=self.inventory();before=IntegrityLedgerEvent.objects.count()
        with get_connection() as conn:
            with conn.cursor() as cur:self.assertEqual(apply_inventory(cur,inv)[0]['action'],'would_apply')
        self.market.refresh_from_db();self.assertEqual(self.market.schedule_version,0);self.assertEqual(IntegrityLedgerEvent.objects.count(),before)
        with get_connection() as conn:
            with conn.cursor() as cur:apply_inventory(cur,inv,apply=True)
        with get_connection() as conn:
            with conn.cursor() as cur:self.assertEqual(apply_inventory(cur,inv,apply=True)[0]['action'],'already_applied')
        inv['markets'][0]['definition_hash']='0'*64
        with self.assertRaises(CommandError),get_connection() as conn:
            with conn.cursor() as cur:apply_inventory(cur,inv,apply=True)

    def test_unreviewed_inventory_rejected(self):
        inv=self.inventory();inv['markets'][0]['reviewed']=False
        with self.assertRaises(CommandError),get_connection() as conn:
            with conn.cursor() as cur:apply_inventory(cur,inv,apply=True)

    def test_concurrent_reschedules_only_one_wins(self):
        from concurrent.futures import ThreadPoolExecutor
        self.register()
        payload=s.Reschedule(expected_market_id=self.market.id,expected_version=1,expected_resolution_at=self.market.expected_resolution_at+timedelta(hours=1),reason='Concurrent review')
        def attempt(_):
            try:
                with get_connection() as conn:
                    with conn.cursor() as cur:s.reschedule(cur,self.market.id,payload,actor_id=None)
                return 'ok'
            except HTTPException as exc:return exc.detail['code']
        with ThreadPoolExecutor(max_workers=2) as executor:results=list(executor.map(attempt,range(2)))
        self.assertCountEqual(results,['ok','schedule_version_conflict'])

    def test_real_resolution_undo_keeps_agenda_and_history(self):
        self.register()
        from apps.api.backend_api.schemas import AdminMarketResolvePayload
        original=self.market.expected_resolution_at
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM gotrendlabs_markets WHERE id=%s',(self.market.id,))
                engine=_market_lifecycle_engine(cur,None)
                engine.resolve_market(cur.fetchone(),self.market.slug,AdminMarketResolvePayload(winning_option_id=self.option.id,note='Fixture evidence',resolution_timezone='UTC'))
        self.market.refresh_from_db();self.assertEqual(self.market.status,'resolved')
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM gotrendlabs_markets WHERE id=%s',(self.market.id,))
                _market_lifecycle_engine(cur,None).cancel_market(cur.fetchone(),self.market.slug,note='Revisão da evidência')
        self.market.refresh_from_db();self.assertEqual(self.market.status,'locked')
        self.assertEqual(self.market.expected_resolution_at,original)
        self.assertEqual(self.market.original_expected_resolution_at,original)
        self.assertEqual(self.market.schedule_version,1)

    def test_admin_filter_order_and_full_query_counts(self):
        from django.contrib.auth import get_user_model
        from apps.web.django.accounts.models import AuthSession
        from apps.api.backend_api.editorial_auth import digest
        from fastapi.testclient import TestClient
        user=get_user_model().objects.create(username='agenda-staff',email='agenda-staff@example.test',is_staff=True,is_active=True,account_status='active')
        token='isolated-agenda-session-token'
        AuthSession.objects.create(user=user,token_hash=digest(token),expires_at=datetime.now(UTC)+timedelta(hours=1),mfa_verified_at=datetime.now(UTC))
        self.register()
        from apps.api.backend_api.main import app
        client=TestClient(app);headers={'Authorization':'Bearer '+token}
        response=client.get('/admin/markets?status=locked&order=next_resolution&temporal=resolution_scheduled',headers=headers)
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(len(response.json()['markets']),1)
        self.assertEqual(response.json()['schedule_counts'],{'resolution_scheduled':1})
        self.assertEqual(response.json()['schedule_count_scope'],'filtered_query_before_temporal_filter')
        empty=client.get('/admin/markets?status=locked&temporal=resolution_overdue',headers=headers)
        self.assertEqual(empty.status_code,200,empty.text)
        self.assertEqual(empty.json()['markets'],[])
        self.assertEqual(empty.json()['schedule_counts'],{'resolution_scheduled':1})
        invalid=client.get('/admin/markets?temporal=invalid',headers=headers)
        self.assertEqual(invalid.status_code,422)

    def test_inventory_requires_boolean_review_aware_timestamp_and_decided_sources(self):
        for mutate in [lambda x:x.update(reviewed='true'),lambda x:x.update(reviewed_at='2026-10-17T12:00:00'),lambda x:x['sources']['expected_resolution_at'].update(origin='operational_decision_pending'),lambda x:x['proposed'].update(evidence_cutoff_at=NOW.isoformat())]:
            inv=self.inventory();mutate(inv['markets'][0])
            with self.assertRaises(CommandError),get_connection() as conn:
                with conn.cursor() as cur:apply_inventory(cur,inv,apply=True)

    def test_migration_signing_failure_rolls_back_proposed_fields(self):
        inv=self.inventory();original=self.market.expected_resolution_at
        inv['markets'][0]['proposed']['expected_resolution_at']=(original+timedelta(hours=1)).isoformat()
        count=IntegrityLedgerEvent.objects.count()
        with patch.object(integrity._signer,'sign',side_effect=RuntimeError('signer unavailable')):
            with self.assertRaises(RuntimeError),get_connection() as conn:
                with conn.cursor() as cur:apply_inventory(cur,inv,apply=True)
        self.market.refresh_from_db()
        self.assertEqual(self.market.expected_resolution_at,original)
        self.assertEqual(self.market.schedule_version,0)
        self.assertEqual(IntegrityLedgerEvent.objects.count(),count)

    def test_reschedule_can_extend_operational_forecast(self):
        self.register()
        payload=s.Reschedule(expected_market_id=self.market.id,expected_version=1,expected_resolution_at=self.market.expected_resolution_at+timedelta(days=30),reason='Nova previsão operacional')
        with get_connection() as conn:
            with conn.cursor() as cur:s.reschedule(cur,self.market.id,payload,actor_id=None)
        self.market.refresh_from_db()
        self.assertEqual(self.market.expected_resolution_at,payload.expected_resolution_at)

    def test_new_contract_rejects_retired_fields(self):
        with self.assertRaises(ValidationError):
            s.ScheduleFields(evidence_cutoff_at=NOW)
        from apps.api.backend_api.main import app
        schema=app.openapi()
        self.assertNotIn('/admin/markets/{slug}/evidence-recovery',schema['paths'])
        self.assertNotIn('evidence_cutoff_at',schema['components']['schemas']['MarketResponse']['properties'])
        from apps.api.backend_api.editorial_schemas import Draft, SearchItem
        for model in [Draft,SearchItem]:
            fields=model.model_json_schema()['properties']
            self.assertIn('expected_resolution_at',fields)
            self.assertIn('schedule_timezone',fields)
            self.assertNotIn('evidence_cutoff_at',fields)
            self.assertNotIn('evidence_recovery_deadline_at',fields)

    def test_historical_signed_snapshot_survives_simplification(self):
        # A previously signed payload remains byte-for-byte intact through a new revision.
        from apps.api.backend_api.integrity_service import _json_object
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE gotrendlabs_markets SET evidence_cutoff_at=%s,evidence_recovery_deadline_at=%s WHERE id=%s",(self.market.close_at,self.market.expected_resolution_at+timedelta(days=2),self.market.id))
        old_snapshot=s.snapshot
        def historical(market):
            return {**old_snapshot(market),'evidence_cutoff_at':market.get('evidence_cutoff_at'),'evidence_recovery_deadline_at':market.get('evidence_recovery_deadline_at'),'evidence_recovery_status':'not_recorded'}
        with patch.object(s,'snapshot',side_effect=historical):self.register()
        with get_connection() as conn:
            with conn.cursor() as cur:
                first=s.history(cur,self.market.id)[0]
                self.assertEqual(s.verify(cur,{'id':self.market.id}),[])
                s.reschedule(cur,self.market.id,s.Reschedule(expected_market_id=self.market.id,expected_version=1,expected_resolution_at=self.market.expected_resolution_at+timedelta(days=10),reason='Simplified operational forecast'),actor_id=None)
                self.assertEqual(s.history(cur,self.market.id)[0]['payload_json'],first['payload_json'])
                self.assertEqual(s.verify(cur,{'id':self.market.id}),[])
                after=_json_object(s.history(cur,self.market.id)[-1]['payload_json'])['payload_snapshot']['after']
                self.assertNotIn('evidence_cutoff_at',after)
