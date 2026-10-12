from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase

from apps.web.django.accounts.api_client import AuthAPIError, _request
from apps.web.django.markets.views import prediction_preview, position_action_preview


class PredictionPreviewWebTests(SimpleTestCase):
    def request(self, **data):
        request = RequestFactory().post('/markets/example/predict/', data)
        request.session = {'auth_api_token': 'token', 'auth_api_user': {'id': 1}}
        return request

    def test_preview_uses_slider_value_and_only_preview_api_without_page_context(self):
        # SimpleTestCase rejects database access, including page context fallbacks.
        with patch('apps.web.django.markets.views.get_market') as market, patch(
            'apps.web.django.core.context_processors.get_wallet', side_effect=AssertionError('page context')
        ), patch('apps.web.django.markets.views.preview_prediction', return_value={'estimated_return': 1000}) as api:
            response = prediction_preview(self.request(option_id='7', stake_amount='500', choice='SIM'), 'example')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['X-GTL-Preview'], '1')
        self.assertEqual(response['Cache-Control'], 'no-store')
        self.assertContains(response, '500 GT₵')
        self.assertContains(response, '1000 GT₵')
        market.assert_not_called()
        api.assert_called_once_with('example', {'option_id': 7, 'stake_amount': 500, 'client_locale': 'pt-br'})

    def test_preview_failure_is_a_fragment_without_fake_zero_return(self):
        with patch('apps.web.django.markets.views.preview_prediction', side_effect=AuthAPIError('Tente novamente.', 503)):
            response = prediction_preview(self.request(option_id='7', stake_amount='120'), 'example')
        self.assertContains(response, 'Tente novamente.')
        self.assertNotContains(response, '0 GT₵')
        self.assertNotContains(response, '<html')

    def test_invalid_input_does_not_call_backend(self):
        for data in ({'option_id': '7', 'stake_amount': 'abc'}, {'stake_amount': '80'}):
            with self.subTest(data=data), patch('apps.web.django.markets.views.preview_prediction') as api:
                response = prediction_preview(self.request(**data), 'example')
                self.assertContains(response, 'valor válido')
                api.assert_not_called()

    def test_position_preview_uses_only_position_api_and_escapes_label(self):
        with patch('apps.web.django.markets.views.get_market') as market, patch(
            'apps.web.django.markets.views.preview_position_action', return_value={'estimated_return': 140, 'allowed': True}
        ) as api:
            response = position_action_preview(self.request(option_id='7', stake_amount='0', action='revision', choice='<script>x</script>'), 'example')
        self.assertEqual(response['X-GTL-Preview'], '1')
        self.assertContains(response, '&lt;script&gt;')
        market.assert_not_called()
        api.assert_called_once_with('token', 'example', {'action': 'revision', 'option_id': 7, 'stake_amount': 0, 'client_locale': 'pt-br'})

    def test_transport_timeout_becomes_handled_api_error(self):
        with patch('apps.web.django.accounts.api_client._http_urlopen', side_effect=TimeoutError('timed out')):
            with self.assertRaises(AuthAPIError) as caught:
                _request('GET', '/health')
        self.assertEqual(caught.exception.status_code, 503)

    def test_body_read_timeout_becomes_handled_api_error(self):
        with patch('apps.web.django.accounts.api_client._http_urlopen') as urlopen:
            urlopen.return_value.__enter__.return_value.read.side_effect = TimeoutError('timed out')
            with self.assertRaises(AuthAPIError):
                _request('GET', '/health')

    def test_preview_is_post_only(self):
        request = RequestFactory().get('/markets/example/predict/')
        self.assertEqual(prediction_preview(request, 'example').status_code, 405)
        self.assertEqual(position_action_preview(request, 'example').status_code, 405)
