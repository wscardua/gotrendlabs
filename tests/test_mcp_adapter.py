import asyncio
import ast
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch
from django.test import SimpleTestCase
import httpx
from mcp.server.auth.provider import AccessToken
from apps.mcp import server


class AdapterBoundaryTests(SimpleTestCase):
    def test_discovery_preserves_exact_issuer_and_authentication_challenge(self):
        from fastapi.testclient import TestClient

        # Public discovery and unauthenticated denial do not run MCP sessions.
        # The real-client test already owns the singleton SDK lifespan.
        client = TestClient(server.app, base_url=server.RESOURCE.rsplit("/mcp", 1)[0])
        for issuer in ("https://issuer.example", "https://issuer.example/"):
            with self.subTest(issuer=issuer), patch.object(server, "ISSUER", issuer):
                metadata = client.get(server.metadata_path)
                self.assertEqual(metadata.status_code, 200)
                self.assertEqual(metadata.json()["authorization_servers"], [issuer])
                self.assertEqual(metadata.json()["resource"], server.RESOURCE)
                self.assertEqual(
                    set(metadata.json()["scopes_supported"]),
                    set(server.TOOL_SCOPES.values()),
                )
                denied = client.post(
                    "/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"}
                )
                self.assertEqual(denied.status_code, 401)
                self.assertIn(server.metadata_path, denied.headers["www-authenticate"])
        client.close()

    def test_api_unavailable_spool_is_durable_bounded_sanitized_and_replayed(self):
        auth = AccessToken(
            token="internal-token-must-not-spool",
            client_id="integration-id",
            scopes=["editorial:read"],
            resource=server.RESOURCE,
        )
        original_client = httpx.AsyncClient

        def unavailable(request):
            raise httpx.ConnectError("secret-free test failure", request=request)

        with tempfile.TemporaryDirectory() as tmp:
            spool = Path(tmp)
            with (
                patch.object(server, "SPOOL", spool),
                patch.object(server, "get_access_token", return_value=auth),
                patch.object(
                    server.httpx,
                    "AsyncClient",
                    side_effect=lambda **kwargs: original_client(
                        transport=httpx.MockTransport(unavailable), **kwargs
                    ),
                ),
            ):
                with self.assertRaisesRegex(ValueError, "dependency_unavailable"):
                    asyncio.run(
                        server.call(
                            "get_editorial_policy",
                            "GET",
                            "/integrations/editorial/policy",
                        )
                    )
                files = list(spool.glob("*.json"))
                self.assertEqual(len(files), 1)
                content = files[0].read_text()
                self.assertNotIn(auth.token, content)
                self.assertNotIn("Authorization", content)
            calls = []

            def recovered(request):
                calls.append(request.url.path)
                return httpx.Response(200, json={"accepted": True})

            with patch.object(server, "SPOOL", spool):

                async def replay():
                    async with original_client(
                        transport=httpx.MockTransport(recovered)
                    ) as client:
                        await server.event(
                            client,
                            auth,
                            "get_editorial_policy",
                            "completed",
                            "execution-id",
                        )

                asyncio.run(replay())
            self.assertFalse(list(spool.glob("*.json")))
            self.assertEqual(len(calls), 2)
            for n in range(128):
                (spool / f"{n}.json").write_text(
                    json.dumps(
                        {
                            "integration_id": "other",
                            "created": time.time(),
                            "payload": {},
                        }
                    )
                )
            with (
                patch.object(server, "SPOOL", spool),
                patch("builtins.print") as output,
            ):

                async def overflow():
                    async with original_client(
                        transport=httpx.MockTransport(unavailable)
                    ) as client:
                        await server.event(
                            client,
                            auth,
                            "get_editorial_policy",
                            "failed",
                            "execution-id",
                        )

                asyncio.run(overflow())
                output.assert_called_with(
                    "mcp_log_spool_capacity_exhausted", flush=True
                )
            self.assertEqual(len(list(spool.glob("*.json"))), 128)

    def test_no_database_or_logging_writer_imports_in_adapter(self):
        root = Path(__file__).resolve().parents[1] / "apps/mcp"
        for path in root.glob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [x.name for x in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                else:
                    continue
                self.assertFalse(
                    any(
                        x.startswith(("django", "psycopg", "sqlalchemy"))
                        or "system_logs" in x
                        or x.endswith(".db")
                        for x in names
                    ),
                    names,
                )

    def test_transport_rejects_large_body_and_host_or_origin(self):
        from fastapi.testclient import TestClient

        auth = AccessToken(
            token="local-test-internal",
            client_id="test",
            scopes=["catalog:read"],
            resource=server.RESOURCE,
        )
        with patch.object(server.Verifier, "verify_token", return_value=auth):
            client = TestClient(server.app)
            self.assertEqual(
                client.post(
                    "/mcp",
                    content=b"x" * 131073,
                    headers={
                        "content-type": "application/json",
                        "host": "localhost:8002",
                    },
                ).status_code,
                413,
            )
            for headers in (
                {"host": "attacker.example", "Authorization": "Bearer fake"},
                {
                    "host": "localhost:8002",
                    "origin": "https://attacker.example",
                    "Authorization": "Bearer fake",
                },
            ):
                self.assertIn(
                    client.post(
                        "/mcp",
                        json={},
                        headers={**headers, "content-type": "application/json"},
                    ).status_code,
                    (403, 421),
                )

    def test_mcp_schema_uses_same_restricted_draft_model(self):
        async def schemas():
            return await server.mcp.list_tools()

        tools = {x.name: x for x in asyncio.run(schemas())}
        draft_schema = tools["create_market_draft"].inputSchema["$defs"]["CreateDraft"]
        self.assertFalse(draft_schema["additionalProperties"])
        self.assertNotIn("is_featured", draft_schema["properties"])
        self.assertIn("idempotency_key", draft_schema["required"])
        self.assertTrue(tools["get_editorial_policy"].annotations.readOnlyHint)
        self.assertFalse(tools["create_market_draft"].annotations.readOnlyHint)
