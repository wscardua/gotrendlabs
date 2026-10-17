import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
from django.test import SimpleTestCase

from apps.mcp import server


class McpScheduleErrorTests(SimpleTestCase):
    async def test_schedule_validation_codes_reach_agent_without_upstream_text(self):
        payload = {'expected_revision': 3, 'idempotency_key': 'schedule-submit-test'}
        codes = (
            'schedule_incomplete', 'schedule_timezone_invalid',
            'schedule_offset_required', 'schedule_order_invalid', 'schedule_expired',
        )
        for code in codes:
            with self.subTest(code=code):
                requests = []

                def respond(request):
                    requests.append(request)
                    return httpx.Response(422, json={
                        'detail': {'code': code, 'message': 'private upstream detail'},
                    })

                client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
                auth = SimpleNamespace(scopes=['drafts:submit'], token='fixture-token')
                with (
                    patch.object(server, 'get_access_token', return_value=auth),
                    patch.object(server.httpx, 'AsyncClient', return_value=client),
                    patch.object(server, 'event', new_callable=AsyncMock) as event,
                ):
                    with self.assertRaises(ValueError) as exc:
                        await server.call('submit_draft_for_review', 'POST',
                                          '/integrations/editorial/drafts/7/submit', payload)
                    self.assertEqual(str(exc.exception), code)
                    self.assertEqual(len(requests), 1)
                    self.assertEqual(json.loads(requests[0].content), payload)
                    event.assert_awaited_once()
                    self.assertEqual(event.call_args.args[3], 'failed')

    async def test_unknown_codes_remain_sanitized(self):
        client = httpx.AsyncClient(transport=httpx.MockTransport(
            lambda request: httpx.Response(500, json={
                'detail': {'code': 'private upstream detail', 'message': 'sensitive'},
            })
        ))
        with (
            patch.object(server, 'get_access_token', return_value=SimpleNamespace(
                scopes=['drafts:submit'], token='fixture-token')),
            patch.object(server.httpx, 'AsyncClient', return_value=client),
            patch.object(server, 'event', new_callable=AsyncMock),
        ):
            with self.assertRaises(ValueError) as exc:
                await server.call('submit_draft_for_review', 'POST', '/fixture')
            self.assertEqual(str(exc.exception), 'dependency_unavailable')

    async def test_schedule_errors_do_not_bypass_scope_gate(self):
        with (
            patch.object(server, 'get_access_token', return_value=SimpleNamespace(
                scopes=['catalog:read'], token='fixture-token')),
            patch.object(server.httpx, 'AsyncClient') as client,
        ):
            with self.assertRaises(ValueError) as exc:
                await server.call('submit_draft_for_review', 'POST', '/fixture')
            self.assertEqual(str(exc.exception), 'forbidden_scope')
            client.assert_not_called()
