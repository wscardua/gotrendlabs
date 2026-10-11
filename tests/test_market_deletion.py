import os
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client, RequestFactory, SimpleTestCase, override_settings
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from fastapi.testclient import TestClient

from apps.api.backend_api.main import app
from apps.api.backend_api.db import get_connection
from apps.api.backend_api.security import hash_token
from apps.api.backend_api import editorial_service
from apps.web.django.accounts.models import AuthSession
from apps.web.django.editorial_integrations.models import EditorialDraft, EditorialRevision
from apps.web.django.markets.models import Market, AdminEvent, Prediction, MarketIntegrityDefinition
from tests.test_cases import AppendOnlyTransactionTestCase


class MarketDeletionTests(AppendOnlyTransactionTestCase):
    def setUp(self):
        super().setUp()
        if connection.vendor != 'postgresql':
            self.skipTest('Requires PostgreSQL')
        env = patch.dict(os.environ, {f'FASTAPI_POSTGRES_{key}': '' for key in ('DB', 'USER', 'PASSWORD', 'HOST', 'PORT')})
        env.start()
        self.addCleanup(env.stop)
        self.staff = get_user_model().objects.create(username='delete-staff', is_staff=True)
        self.api = TestClient(app)
        self.headers = self.session(self.staff, 'staff-delete', mfa=True)
        response = self.api.post('/admin/markets', headers=self.headers, json={
            'title': 'Mercado para excluir?', 'slug': 'delete-me', 'summary': 'Resumo',
            'category': 'Tecnologia', 'subcategory': 'Software', 'event': 'Lançamento',
            'source': 'https://example.com', 'resolution_criteria': 'Critério',
            'close_at': '2027-12-31T23:59:00-03:00', 'thumb_color': '#123456',
        })
        self.assertEqual(response.status_code, 201, response.text)
        self.market = Market.objects.get(slug='delete-me')
        self.draft = EditorialDraft.objects.get(market=self.market)

    def session(self, user, token, mfa=False):
        AuthSession.objects.create(user=user, token_hash=hash_token(token),
            expires_at=timezone.now() + timedelta(days=1),
            mfa_verified_at=timezone.now() if mfa else None)
        return {'Authorization': f'Bearer {token}'}

    def delete(self, revision=None, headers=None):
        return self.api.delete('/admin/markets/delete-me', headers=self.headers if headers is None else headers,
            params={'expected_revision': self.draft.revision if revision is None else revision, 'expected_market_id': self.market.pk})

    def test_preparation_physically_removed_with_editorial_history(self):
        self.assertTrue(EditorialRevision.objects.filter(draft_id=self.market.pk).exists())
        self.assertTrue(self.api.get('/admin/markets/delete-me', headers=self.headers).json()['can_delete'])
        self.assertEqual(self.delete().status_code, 204)
        self.assertFalse(Market.objects.filter(pk=self.market.pk).exists())
        self.assertFalse(EditorialRevision.objects.filter(draft_id=self.market.pk).exists())
        self.assertFalse(EditorialDraft.objects.filter(pk=self.market.pk).exists())
        event = AdminEvent.objects.get(action='market.delete')
        self.assertEqual(event.actor_id, self.staff.pk)
        self.assertIn('preparation', event.note)
        listing = self.api.get('/admin/markets', headers=self.headers).json()
        self.assertEqual(listing['markets'], [])
        self.assertEqual(listing['counts'].get('draft', 0), 0)
        reviews = self.api.get('/admin/agent-editorial-reviews', headers=self.headers).json()
        self.assertEqual(reviews['items'], [])
        for url in ('/admin/markets/delete-me', '/markets/delete-me',
                    f'/admin/agent-editorial-reviews/{self.market.pk}',
                    '/markets/delete-me/integrity/verify', '/admin/markets/delete-me/integrity/verify'):
            self.assertEqual(self.api.get(url, headers=self.headers).status_code, 404, url)
        with get_connection() as conn, conn.cursor() as cursor:
            self.assertEqual(editorial_service.search(cursor)['items'], [])
        self.assertEqual(self.delete().status_code, 404)
        self.assertEqual(AdminEvent.objects.filter(action='market.delete').count(), 1)

    def test_in_review_can_be_deleted(self):
        EditorialDraft.objects.filter(pk=self.market.pk).update(state='in_review')
        self.assertEqual(self.delete().status_code, 204)

    def test_other_editorial_states_are_blocked(self):
        for state in ('approved', 'returned', 'rejected'):
            EditorialDraft.objects.filter(pk=self.market.pk).update(state=state)
            self.assertEqual(self.delete().status_code, 409, state)
        self.market.refresh_from_db()
        self.assertTrue(Market.objects.filter(pk=self.market.pk).exists())
        self.assertFalse(AdminEvent.objects.filter(action='market.delete').exists())

    def test_published_and_terminal_states_are_blocked(self):
        for state in ('scheduled', 'open', 'locked', 'resolved', 'sealed', 'canceled'):
            Market.objects.filter(pk=self.market.pk).update(status=state)
            self.assertEqual(self.delete().status_code, 409, state)
        Market.objects.filter(pk=self.market.pk).update(status='draft', published_at=timezone.now())
        self.assertEqual(self.delete().status_code, 409)

    def test_stale_or_missing_revision(self):
        self.assertEqual(self.delete(revision=100).status_code, 409)
        self.assertEqual(self.api.delete('/admin/markets/delete-me', headers=self.headers).status_code, 422)
        self.assertEqual(self.delete(revision=0).status_code, 422)
        self.market.refresh_from_db()
        self.assertTrue(Market.objects.filter(pk=self.market.pk).exists())

    def test_stale_edit_and_actions_cannot_target_reused_slug(self):
        old_id = self.market.pk
        self.assertEqual(self.delete().status_code, 204)
        payload = {
            'title': 'Novo mercado', 'slug': 'delete-me', 'category': 'Tecnologia',
            'subcategory': 'Software', 'expected_revision': 1,
            'summary': 'Resumo', 'source': 'https://example.com', 'resolution_criteria': 'Critério',
            'thumb_color': '#123456', 'close_at': '2027-12-31T23:59:00-03:00',
        }
        created = self.api.post('/admin/markets', headers=self.headers, json=payload)
        self.assertEqual(created.status_code, 201, created.text)
        new_market = Market.objects.get(slug='delete-me')
        self.assertNotEqual(new_market.pk, old_id)
        for identity in ({}, {'expected_market_id': old_id}):
            response = self.api.patch('/admin/markets/delete-me', headers=self.headers,
                json={**payload, 'title': 'Alteração da aba antiga', **identity})
            self.assertEqual(response.status_code, 409, response.text)
            for action in ('publish', 'cancel', 'lock'):
                response = self.api.post(f'/admin/markets/delete-me/{action}',
                    headers=self.headers, json={'note': 'Aba antiga', **identity})
                self.assertEqual(response.status_code, 409, response.text)
        new_market.refresh_from_db()
        self.assertEqual(new_market.title, 'Novo mercado')
        self.assertEqual(new_market.status, 'draft')
        self.assertEqual(EditorialDraft.objects.get(pk=new_market.pk).revision, 1)
        saved = self.api.patch('/admin/markets/delete-me', headers=self.headers,
            json={**payload, 'title': 'Alteração autorizada', 'expected_market_id': new_market.pk})
        self.assertEqual(saved.status_code, 200, saved.text)
        canceled = self.api.post('/admin/markets/delete-me/cancel', headers=self.headers,
            json={'expected_market_id': new_market.pk})
        self.assertEqual(canceled.status_code, 200, canceled.text)

    def test_permissions_and_mfa(self):
        self.assertEqual(self.delete(headers={}).status_code, 401)
        user = get_user_model().objects.create(username='delete-member', email='delete-member@example.com')
        self.assertEqual(self.delete(headers=self.session(user, 'member-delete')).status_code, 403)
        self.assertEqual(self.delete(headers=self.session(self.staff, 'staff-without-mfa')).status_code, 403)
        self.market.refresh_from_db()
        self.assertTrue(Market.objects.filter(pk=self.market.pk).exists())

    def test_prediction_blocks_deletion_without_touching_positions(self):
        prediction = Prediction.objects.create(user=self.staff, market=self.market,
            market_option=self.market.options.first(), stake_amount=10,
            probability_at_entry=50, weight_at_entry=20, potential_payout=20)
        self.assertEqual(self.delete().status_code, 409)
        self.assertTrue(Prediction.objects.filter(pk=prediction.pk).exists())

    def test_registered_definition_blocks_anomalous_draft(self):
        MarketIntegrityDefinition.objects.create(
            market=self.market, protocol_version='test', canonical_payload=b'{}', payload_json={},
            payload_hash='a' * 64, signature=b'test', algorithm='test', key_id='test',
            key_fingerprint='b' * 64, signed_at=timezone.now(),
        )
        self.assertEqual(self.delete().status_code, 409)
        self.market.refresh_from_db()
        self.assertTrue(Market.objects.filter(pk=self.market.pk).exists())
        self.assertTrue(MarketIntegrityDefinition.objects.filter(market=self.market).exists())

    def test_deletion_rechecks_state_after_waiting_for_editor_lock(self):
        from concurrent.futures import ThreadPoolExecutor
        import threading
        from apps.api.backend_api.market_deletion import delete_market
        from fastapi import HTTPException
        ready = threading.Event()
        def attempt():
            with get_connection() as conn, conn.cursor() as cursor:
                ready.set()
                try:
                    delete_market(cursor, self.market.slug, self.draft.revision, self.staff.pk, self.market.pk)
                except HTTPException as exc:
                    return exc.status_code
            return 204
        with ThreadPoolExecutor(max_workers=1) as pool:
            with get_connection() as conn, conn.cursor() as cursor:
                cursor.execute('SELECT id FROM gotrendlabs_markets WHERE id=%s FOR UPDATE', (self.market.pk,))
                future = pool.submit(attempt)
                self.assertTrue(ready.wait(5))
                cursor.execute("UPDATE gotrendlabs_agent_editorial_drafts SET state='approved',revision=revision+1 WHERE market_id=%s", (self.market.pk,))
            self.assertEqual(future.result(timeout=10), 409)
        self.market.refresh_from_db()
        self.assertTrue(Market.objects.filter(pk=self.market.pk).exists())

    def test_dependents_removed_and_suggestion_preserved(self):
        from apps.web.django.markets.models import (MarketOption, MarketComment, CommentReaction,
            UserNotification, MarketFavorite, MarketLike, MarketSuggestion, IntegrityAlert)
        from apps.web.django.communications.models import PushDevice, PushDelivery
        from apps.web.django.agents.models import AiAgentAction
        comment = MarketComment.objects.create(market=self.market, author=self.staff, body='Draft note')
        CommentReaction.objects.create(comment=comment, user=self.staff, reaction='like')
        notification = UserNotification.objects.create(recipient=self.staff, comment=comment,
            event_type='comment', source_key='delete-test', title='Draft note')
        device = PushDevice.objects.create(user=self.staff, platform='android', token='fake', token_hash='a' * 64)
        PushDelivery.objects.create(notification=notification, device=device, event_type='comment', idempotency_key='delete-test')
        MarketFavorite.objects.create(market=self.market, user=self.staff)
        MarketLike.objects.create(market=self.market, user=self.staff)
        suggestion = MarketSuggestion.objects.create(question='Original suggestion', category='Technology',
            suggested_source='https://example.org', status='rewarded', reward_gtl=10, converted_market=self.market)
        action = AiAgentAction.objects.create(market=self.market, comment=comment, action_type='comment', status='created')
        IntegrityAlert.objects.create(market=self.market, dedupe_key='delete-test',
            issue_code='draft-warning', title='Draft alert', description='Review draft',
            first_detected_at=timezone.now(), last_detected_at=timezone.now())
        option_ids = list(self.market.options.values_list('id', flat=True))
        self.assertEqual(self.delete().status_code, 204)
        for model in (MarketComment, CommentReaction, UserNotification, PushDelivery, MarketFavorite, MarketLike, IntegrityAlert):
            self.assertFalse(model.objects.exists(), model.__name__)
        self.assertFalse(MarketOption.objects.filter(id__in=option_ids).exists())
        suggestion.refresh_from_db()
        self.assertIsNone(suggestion.converted_market_id)
        self.assertEqual((suggestion.status, suggestion.reward_gtl), ('rewarded', 10))
        action.refresh_from_db()
        self.assertIsNone(action.market_id)
        self.assertIsNone(action.comment_id)
        self.assertTrue(PushDevice.objects.filter(pk=device.pk).exists())

    def test_old_confirmation_cannot_delete_replacement_at_same_slug(self):
        self.assertEqual(self.delete().status_code, 204)
        response = self.api.post('/admin/markets', headers=self.headers, json={
            'title': 'Replacement?', 'slug': 'delete-me', 'summary': 'New market',
            'category': 'Tecnologia', 'subcategory': 'Software', 'event': 'Lançamento',
            'source': 'https://example.com', 'resolution_criteria': 'Criteria',
            'close_at': '2027-12-31T23:59:00-03:00', 'thumb_color': '#123456',
        })
        self.assertEqual(response.status_code, 201, response.text)
        replacement = Market.objects.get(slug='delete-me')
        self.assertNotEqual(replacement.pk, self.market.pk)
        self.assertEqual(self.delete().status_code, 409)
        self.assertTrue(Market.objects.filter(pk=replacement.pk).exists())

    def test_database_function_rejects_protected_states_and_stale_revision(self):
        import psycopg
        for state in ('approved', 'returned', 'rejected'):
            EditorialDraft.objects.filter(pk=self.market.pk).update(state=state)
            with self.assertRaises(psycopg.errors.CheckViolation):
                with get_connection() as conn, conn.cursor() as cursor:
                    cursor.execute('SELECT public.delete_prepublication_editorial(%s,%s)', (self.market.pk, 1))
        EditorialDraft.objects.filter(pk=self.market.pk).update(state='preparation')
        with self.assertRaises(psycopg.errors.CheckViolation):
            with get_connection() as conn, conn.cursor() as cursor:
                cursor.execute('SELECT public.delete_prepublication_editorial(%s,%s)', (self.market.pk, 2))
        self.assertTrue(EditorialRevision.objects.filter(draft_id=self.market.pk).exists())

    def test_database_function_is_only_executable_by_fastapi_runtime(self):
        with get_connection() as conn, conn.cursor() as cursor:
            cursor.execute("SELECT rolname FROM pg_roles WHERE rolname IN ('gotrendlabs_fastapi','gotrendlabs_django')")
            if len(cursor.fetchall()) != 2:
                self.skipTest('Runtime roles absent in this test environment')
            for role, allowed in (('gotrendlabs_fastapi', True), ('gotrendlabs_django', False)):
                cursor.execute("SELECT has_function_privilege(%s,'public.delete_prepublication_editorial(bigint,integer)','EXECUTE') AS allowed", (role,))
                self.assertEqual(cursor.fetchone()['allowed'], allowed)
            cursor.execute("SELECT has_table_privilege('gotrendlabs_fastapi','gotrendlabs_agent_editorial_revisions','DELETE') AS allowed")
            self.assertFalse(cursor.fetchone()['allowed'])

    def test_audit_failure_rolls_back_deletion(self):
        revisions = list(EditorialRevision.objects.filter(draft_id=self.market.pk).values())
        options = list(self.market.options.values())
        with patch('apps.api.backend_api.market_deletion.record_admin_event', side_effect=RuntimeError('audit failure')):
            with self.assertRaises(RuntimeError):
                self.delete()
        self.market.refresh_from_db()
        self.assertTrue(Market.objects.filter(pk=self.market.pk).exists())

        self.assertEqual(list(EditorialRevision.objects.filter(draft_id=self.market.pk).values()), revisions)
        self.assertEqual(list(self.market.options.values()), options)
        self.assertTrue(EditorialDraft.objects.filter(pk=self.market.pk).exists())

    def test_old_mutation_urls_cannot_revive_market(self):
        self.assertEqual(self.delete().status_code, 204)
        for action in ('publish', 'cancel', 'lock'):
            response = self.api.post(f'/admin/markets/delete-me/{action}', headers=self.headers, json={'note': 'old tab'})
            self.assertEqual(response.status_code, 404, response.text)
        with get_connection() as conn, conn.cursor() as cursor:
            from apps.api.backend_api.main import _market_lifecycle_engine
            from fastapi import HTTPException
            # Simulates a publisher that read the market before deletion committed.
            with self.assertRaises(HTTPException) as exc:
                _market_lifecycle_engine(cursor, self.staff.pk).publish_market({'id': self.market.pk, 'status': 'draft'}, self.market.slug)
            self.assertEqual(exc.exception.status_code, 404)
            from apps.api.backend_api.thumbnail_service import market
            with self.assertRaises(HTTPException):
                market(cursor, self.market.slug, lock=True)


@override_settings(TEMPLATES=[{**settings.TEMPLATES[0], "OPTIONS": {**settings.TEMPLATES[0]["OPTIONS"], "context_processors": ["django.template.context_processors.request"]}}])
class MarketDeletionWebTests(SimpleTestCase):
    def request(self, method='get', data=None):
        request = getattr(RequestFactory(), method)('/admin-ops/markets/delete-me/delete/', data or {})
        request.session = {'auth_api_token': 'staff-token', 'auth_api_user': {'id': 1, 'is_staff': True}}
        return request

    market = {'slug': 'delete-me', 'title': 'Mercado para excluir?', 'can_delete': True,
              'editorial_market_id': 7, 'editorial_revision': 4, 'editorial_status': 'in_review', 'status': 'draft'}

    def test_confirmation_get_is_read_only(self):
        from apps.web.django.admin_ops.views import market_delete
        with patch('apps.web.django.admin_ops.views.admin_get_market', return_value=self.market), patch('apps.web.django.admin_ops.views.admin_delete_market') as delete:
            response = market_delete(self.request(), 'delete-me')
        delete.assert_not_called()
        self.assertContains(response, 'Confirmar exclusão')
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertContains(response, 'value="4"')

    def test_explicit_post_uses_confirmed_revision(self):
        from apps.web.django.admin_ops.views import market_delete
        with patch('apps.web.django.admin_ops.views.admin_get_market', return_value=self.market), patch('apps.web.django.admin_ops.views.admin_delete_market') as delete, patch('apps.web.django.admin_ops.views.messages.success'):
            response = market_delete(self.request('post', {'confirm': 'yes', 'expected_revision': '3', 'expected_market_id': '7'}), 'delete-me')
        delete.assert_called_once_with('staff-token', 'delete-me', 3, 7)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('admin-ops-markets'))

    def test_missing_confirmation_does_not_delete(self):
        from apps.web.django.admin_ops.views import market_delete
        with patch('apps.web.django.admin_ops.views.admin_get_market', return_value=self.market), patch('apps.web.django.admin_ops.views.admin_delete_market') as delete:
            response = market_delete(self.request('post', {'expected_revision': '4'}), 'delete-me')
        self.assertEqual(response.status_code, 400)
        delete.assert_not_called()

    def test_csrf_required(self):
        response = Client(enforce_csrf_checks=True).post(reverse('admin-ops-market-delete', args=['delete-me']), {'confirm': 'yes', 'expected_revision': 4})
        self.assertEqual(response.status_code, 403)

    def test_conflict_displays_backend_error(self):
        from apps.web.django.admin_ops.views import market_delete
        from apps.web.django.accounts.api_client import AuthAPIError
        with patch('apps.web.django.admin_ops.views.admin_get_market', return_value=self.market), patch('apps.web.django.admin_ops.views.admin_delete_market', side_effect=AuthAPIError('O mercado foi alterado.', 409)):
            response = market_delete(self.request('post', {'confirm': 'yes', 'expected_revision': '3', 'expected_market_id': '7'}), 'delete-me')
        self.assertContains(response, 'O mercado foi alterado.', status_code=409)

    def test_list_button_only_for_eligible_market(self):
        for allowed in (True, False):
            html = render_to_string('admin_ops/markets.html', {'market_data': {'markets': [{**self.market, 'can_delete': allowed}]}})
            self.assertEqual('Excluir mercado' in html, allowed)
