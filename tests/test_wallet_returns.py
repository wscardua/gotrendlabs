from uuid import uuid4
from django.template.loader import render_to_string
from tests.test_cases import AppendOnlyTransactionTestCase
from tests import test_resolution_reliability as reliability
from apps.api.backend_api.wallet_returns import resolution_returns
from apps.api.backend_api.db import get_connection
from apps.web.django.markets.models import Prediction
from apps.web.django.accounts.models import WalletLedgerEntry


class WalletReturnTests(AppendOnlyTransactionTestCase):
    setUp = reliability.ResolutionReliabilityTests.setUp
    tearDown = reliability.ResolutionReliabilityTests.tearDown
    _register = reliability.ResolutionReliabilityTests._register
    prepare = reliability.ResolutionReliabilityTests.prepare
    resolve = reliability.ResolutionReliabilityTests.resolve

    def summary(self):
        response = self.client.get('/users/me/ledger', headers=self.user_headers)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_return_100_at_50_percent_and_undo_reresolve_do_not_double_count(self):
        reliability.Market.objects.get(slug='openai-gpt6-2026').options.update(probability_exact=50)
        self.prepare(stake_amount=100)
        self.assertEqual(self.summary()['resolution_returns'], [])
        self.assertEqual(self.resolve().status_code, 200)
        data = self.summary()
        result = data['resolution_returns'][0]
        self.assertEqual((result['released_gtl'], result['net_profit_gtl'], result['total_received_gtl']), (100,100,200))
        self.assertEqual(self.client.get('/users/me/ledger',headers=self.staff_headers).json()['resolution_returns'], [])
        html = render_to_string('wallet/wallet.html', {**data, 'viewer': {'reputation': 0}})
        self.assertIn('Extrato', html)
        for label in ('Retornos por acerto', 'Valor liberado', 'Ganho líquido', 'Total recebido'):
            self.assertNotIn(label, html)
        undone = self.client.post(f'/admin/markets/{self.market.slug}/cancel',headers=self.staff_headers,
                                  json={'expected_market_id':self.market.id,'note':'Revisar resultado'})
        self.assertEqual(undone.status_code, 200, undone.text)
        self.assertEqual(self.summary()['resolution_returns'], [])
        self.assertEqual(self.resolve({**self.payload,'idempotency_key':str(uuid4())}).status_code, 200)
        second = self.summary()['resolution_returns'][0]
        self.assertEqual(second['total_received_gtl'], 200)
        self.assertEqual(second, result)

    def test_return_preserves_recorded_rounding_at_62_percent(self):
        self.prepare(stake_amount=100)
        self.assertEqual(self.resolve().status_code, 200)
        result = self.summary()['resolution_returns'][0]
        self.assertEqual((result['released_gtl'], result['net_profit_gtl'], result['total_received_gtl']), (100, 61, 161))

    def test_losing_prediction_does_not_show_winning_return(self):
        self.prepare(stake_amount=100)
        other = self.market.options.exclude(pk=self.option.id).first()
        self.assertEqual(self.resolve({**self.payload,'winning_option_id':other.id}).status_code, 200)
        self.assertEqual(self.summary()['resolution_returns'], [])

    def test_zero_profit_uses_actual_release_and_ignores_cancelled_positions(self):
        self.prepare(stake_amount=100)
        prediction = Prediction.objects.get(market=self.market)
        # Isolated read-projection fixture: a zero-profit settlement has no payout row.
        Prediction.objects.filter(pk=prediction.id).update(status='resolved', won=True)
        self.market.status = 'resolved'
        self.market.save(update_fields=['status'])
        WalletLedgerEntry.objects.create(user_id=prediction.user_id,entry_type='prediction_refund',
            amount=100,direction='release',description='Fixture',reference_type='prediction',reference_id=str(prediction.id))
        with get_connection() as conn, conn.cursor() as cursor:
            data = resolution_returns(cursor,prediction.user_id)
        self.assertEqual((data[0]['released_gtl'],data[0]['net_profit_gtl'],data[0]['total_received_gtl']),(100,0,100))
        Prediction.objects.filter(pk=prediction.id).update(status='canceled')
        with get_connection() as conn, conn.cursor() as cursor:
            self.assertEqual(resolution_returns(cursor,prediction.user_id),[])
