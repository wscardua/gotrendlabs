import os
from datetime import timedelta
from django.utils import timezone
from django.template.loader import render_to_string
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection
from fastapi.testclient import TestClient

from apps.api.backend_api.agent_services import refresh_market_public_metrics
from apps.api.backend_api.db import get_connection
from apps.api.backend_api.main import app, _viewer_position_summary
from apps.web.django.admin_ops.models import SiteConfig
from apps.web.django.markets.models import Market, MarketCategory, MarketSubcategory, MarketOption, Prediction
from tests.test_cases import AppendOnlyTransactionTestCase


class MarketParticipantTests(AppendOnlyTransactionTestCase):
    def setUp(self):
        super().setUp()
        if connection.vendor != 'postgresql':
            self.skipTest('Métricas de mercado usam PostgreSQL')
        environment = patch.dict(os.environ, {f'FASTAPI_POSTGRES_{key}': '' for key in (
            'DB', 'USER', 'PASSWORD', 'HOST', 'PORT')})
        environment.start()
        self.addCleanup(environment.stop)
        category = MarketCategory.objects.create(name="Tecnologia", slug="tecnologia")
        subcategory = MarketSubcategory.objects.create(category=category, name="Apps", slug="apps")
        self.market = Market.objects.create(
            category=category, subcategory=subcategory,
            slug='participantes-totais', title='Mercado de participantes?',
            kind='binary', status='open', status_label='Aberto', primary_outcome='SIM',
        )
        self.option = MarketOption.objects.create(market=self.market, label='SIM', probability_exact=50)
        self.api = TestClient(app)

    def predict(self, user, **kwargs):
        return Prediction.objects.create(
            market=self.market, market_option=self.option, user=user,
            stake_amount=10, probability_at_entry=50, weight_at_entry=1000,
            potential_payout=20, **kwargs,
        )

    def assert_metrics(self, total, label):
        with get_connection() as conn, conn.cursor() as cursor:
            metrics = refresh_market_public_metrics(cursor, self.market.pk)
        self.assertEqual(metrics['total_participants'], total)
        self.assertEqual(metrics['participants'], label)
        self.market.refresh_from_db()
        self.assertEqual(self.market.participants, label)
        response = self.api.get(f'/markets/{self.market.slug}')
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['total_participants'], total)
        self.assertEqual(response.json()['participants'], label)
        feed = self.api.get('/markets')
        self.assertEqual(feed.status_code, 200, feed.text)
        row = next(m for m in feed.json()['markets'] if m['slug'] == self.market.slug)
        self.assertEqual(row['total_participants'], total)
        self.assertEqual(row['participants'], label)
        html = render_to_string('markets/detail.html', {'market': response.json()})
        self.assertIn(label, html)
        return response.json()

    def test_total_includes_bots_without_counting_reinforcements_or_inactive_entries(self):
        self.assert_metrics(0, '0 participantes')
        human = get_user_model().objects.create(username='humano', email='humano@example.test')
        bot = get_user_model().objects.create(username='bot', email='bot@example.test', is_bot=True)
        self.predict(human, status='open')
        self.assert_metrics(1, '1 participante')
        self.predict(bot, status='open')
        self.predict(human, status='open', action_type='reinforcement', position_sequence=2)
        self.predict(bot, status='open', action_type='reinforcement', position_sequence=2)
        other = get_user_model().objects.create(username='inativo', email='inativo@example.test')
        for index, status in enumerate(['revised', 'resolved', 'canceled'], start=1):
            self.predict(other, status=status, position_sequence=index)
        data = self.assert_metrics(2, '2 participantes')
        self.assertEqual(data['human_participants'], 1)
        self.assertEqual(data['bot_participants'], 1)
        self.assertEqual(data['human_volume_gtl'], 20)
        self.assertEqual(data['bot_volume_gtl'], 20)

    def test_resolved_and_sealed_keep_final_volume_and_distinct_participants(self):
        human = get_user_model().objects.create(username='winner', email='winner@example.test')
        bot = get_user_model().objects.create(username='final-bot', email='final-bot@example.test', is_bot=True)
        self.predict(human, status='resolved')
        self.predict(human, status='resolved', action_type='reinforcement', position_sequence=2)
        self.predict(bot, status='resolved')
        excluded = get_user_model().objects.create(username='excluded', email='excluded@example.test')
        self.predict(excluded, status='revised')
        self.predict(excluded, status='canceled', position_sequence=2)
        # An inconsistent open row must not inflate the final public result.
        self.predict(excluded, status='open', position_sequence=3)
        for state in ('resolved', 'sealed'):
            self.market.status = state
            self.market.save(update_fields=['status'])
            data = self.assert_metrics(2, '2 participantes')
            self.assertEqual(data['human_volume_gtl'], 20)
            self.assertEqual(data['total_volume_gtl'], 30)
            html = render_to_string('markets/detail.html', {'market': data})
            self.assertIn('GT₵ em previsões', html)
        from apps.api.backend_api.agent_services import _human_prediction_totals
        with get_connection() as conn, conn.cursor() as cursor:
            humans, amount = _human_prediction_totals(cursor, self.market.id)
        self.assertEqual((humans, amount), (1, 10))
        self.market.status = 'locked'
        self.market.save(update_fields=['status'])
        data = self.assert_metrics(1, '1 participante')
        self.assertEqual(data['human_volume_gtl'], 10)

    def test_bot_only_is_one_public_participant_and_no_human(self):
        bot = get_user_model().objects.create(username='somente-bot', email='somente-bot@example.test', is_bot=True)
        self.predict(bot, status='open')
        data = self.assert_metrics(1, '1 participante')
        self.assertEqual(data['human_participants'], 0)
        self.assertEqual(data['bot_participants'], 1)
        self.assertEqual(data['human_volume_gtl'], 0)

    def test_backend_revision_reasons_leave_reinforcement_available(self):
        user = get_user_model().objects.create(username='revisao', email='revisao@example.test')
        self.predict(user, status='open')
        config = SiteConfig.get_solo()
        for enabled, hours, limit, reason in (
            (False, 48, 1, 'Revisão de posição desativada no Admin Ops.'),
            (True, 1, 1, 'Janela de revisão encerrada para este mercado.'),
            (True, 48, 0, 'Limite de revisões atingido neste mercado.'),
        ):
            with self.subTest(reason=reason):
                config.position_reinforcement_enabled = True
                config.position_reinforcement_max_count = 3
                config.position_revision_enabled = enabled
                config.position_revision_cutoff_hours = 24
                config.position_revision_max_count = limit
                config.save()
                market = {'id': self.market.pk, 'status': 'open',
                          'close_at': timezone.now() + timedelta(hours=hours),
                          'auto_close_enabled': True}
                with get_connection() as conn, conn.cursor() as cursor:
                    position = _viewer_position_summary(cursor, market, user.pk)
                self.assertTrue(position['can_reinforce'])
                self.assertFalse(position['can_revise'])
                self.assertEqual(position['revision_blocked_reason'], reason)
