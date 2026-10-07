"""Opt-in radar rehearsal over real MCP HTTP, on a disposable Django test DB.

Run ONLY via test_mcp_local.py with this exact method label. Inputs/results live
under tests/fixtures/mcp_radar_20261007 and .runtime/radar-20261007.
No production API URLs, human accounts, or secrets
are copied; the adapter subprocess receives no database environment variables.
"""

import asyncio
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
from unittest.mock import patch

import httpx
from django.db import connection
from django.utils.dateparse import parse_datetime
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import uvicorn

from apps.api.backend_api.main import app
from apps.web.django.markets.models import (
    Market,
    MarketCategory,
    MarketSubcategory,
    MarketEvent,
)
from apps.web.django.editorial_integrations.models import (
    EditorialDraft,
    EditorialRevision,
    Quota,
)
from apps.web.django.system_logs.models import SystemLog
from tests.test_mcp_editorial import McpEditorialTests

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / ".runtime/radar-20261007"
INPUT = ROOT / "tests/fixtures/mcp_radar_20261007"


class RadarPilot(McpEditorialTests):
    def seed_catalog(self):
        snapshot = json.loads((INPUT / "dev-public-snapshot.json").read_text())
        self.assertEqual(snapshot["source"], "DEV local public API read-only")
        MarketEvent.objects.all().delete()
        MarketSubcategory.objects.all().delete()
        MarketCategory.objects.all().delete()
        mapping = {}
        for c in snapshot["taxonomy"]["categories"]:
            category = MarketCategory.objects.create(name=c["name"], slug=c["slug"])
            for s in c["subcategories"]:
                sub = MarketSubcategory.objects.create(
                    category=category, name=s["name"], slug=s["slug"]
                )
                for e in s["events"]:
                    event = MarketEvent.objects.create(
                        subcategory=sub, name=e["name"], slug=e["slug"]
                    )
                    mapping[(c["name"], s["name"], e["name"])] = (category, sub, event)
        for m in snapshot["markets"]:
            category, sub, event = mapping[
                (m["category"], m["subcategory"], m["event"])
            ]
            Market.objects.create(
                slug=m["slug"],
                title=m["title"],
                summary=m["summary"],
                kind=m["kind"],
                status=m["status"],
                status_label=m["status"],
                primary_outcome="Sim",
                category=category,
                subcategory=sub,
                event=event,
                source=m.get("source", ""),
                resolution_criteria=m.get("resolution_criteria", ""),
                close_at=parse_datetime(m["close_at"]) if m.get("close_at") else None,
                close_timezone="America/Sao_Paulo",
            )
        return snapshot

    def test_run(self):
        self.assertTrue(connection.settings_dict["NAME"].startswith("test_gtl_mcp_"))
        snapshot = self.seed_catalog()
        plan_path = INPUT / "plan.json"
        plan = (
            None
            if os.environ.get("GTL_RADAR_PHASE") == "observe"
            else json.loads(plan_path.read_text())
        )
        mode = "execute" if plan else "observe"
        output = RUN / mode
        output.mkdir(parents=True, exist_ok=True)
        rows, called, created = [], set(), []
        sockets = []
        for _ in range(2):
            sock = socket.socket()
            sock.bind(("127.0.0.1", 0))
            sockets.append(sock)
        api_port, mcp_port = [s.getsockname()[1] for s in sockets]
        sockets[1].close()
        api_url, mcp_url = (
            f"http://127.0.0.1:{api_port}",
            f"http://127.0.0.1:{mcp_port}/mcp",
        )
        api_server = uvicorn.Server(
            uvicorn.Config(app, access_log=False, log_level="critical")
        )
        thread = threading.Thread(
            target=lambda: api_server.run(sockets=[sockets[0]]), daemon=True
        )
        adapter = None
        with patch.dict(
            os.environ, {"GTL_MCP_ISSUER": api_url, "GTL_MCP_RESOURCE": mcp_url}
        ):
            try:
                thread.start()
                for _ in range(200):
                    if api_server.started:
                        break
                    time.sleep(0.02)
                self.assertTrue(api_server.started)
                child_env = {
                    k: os.environ[k]
                    for k in ("PATH", "LANG", "TMPDIR")
                    if k in os.environ
                }
                child_env.update(
                    GTL_MCP_ENABLED="1",
                    GTL_MCP_API_URL=api_url,
                    GTL_MCP_ISSUER=api_url,
                    GTL_MCP_RESOURCE=mcp_url,
                    GTL_MCP_WORKLOAD_SECRET=os.environ["GTL_MCP_WORKLOAD_SECRET"],
                    GTL_MCP_SPOOL=str(output / "spool"),
                    PYTHONUNBUFFERED="1",
                )
                self.assertFalse(
                    any("POSTGRES" in k or "DATABASE" in k for k in child_env)
                )
                with (output / "adapter.log").open("w") as logfile:
                    adapter = subprocess.Popen(
                        [
                            sys.executable,
                            "-m",
                            "uvicorn",
                            "apps.mcp.server:app",
                            "--host",
                            "127.0.0.1",
                            "--port",
                            str(mcp_port),
                            "--no-access-log",
                            "--log-level",
                            "critical",
                        ],
                        cwd=ROOT,
                        env=child_env,
                        stdout=logfile,
                        stderr=logfile,
                    )
                    for _ in range(200):
                        try:
                            if (
                                httpx.get(
                                    f"http://127.0.0.1:{mcp_port}/health", timeout=0.2
                                ).status_code
                                == 200
                            ):
                                break
                        except httpx.TransportError:
                            pass
                        time.sleep(0.05)
                    # Credentials cross the actual HTTP token endpoint, held only in memory.
                    with httpx.Client() as auth_client:
                        exchange = auth_client.post(
                            api_url + "/oauth/token",
                            data={
                                "grant_type": "client_credentials",
                                "client_id": self.credential["credential_id"],
                                "client_secret": self.credential["secret"],
                                "resource": mcp_url,
                            },
                        )
                        self.assertEqual(exchange.status_code, 200)
                        access = exchange.json()["access_token"]

                    async def run():
                        async with streamablehttp_client(
                            mcp_url, headers={"Authorization": "Bearer " + access}
                        ) as (read, write, _):
                            async with ClientSession(read, write) as client:
                                initialized = await client.initialize()
                                tools = await client.list_tools()
                                self.assertEqual(len(tools.tools), 10)
                                (output / "discovery.json").write_text(
                                    json.dumps(
                                        {
                                            "protocol": initialized.protocolVersion,
                                            "instructions": initialized.instructions,
                                            "tools": [
                                                t.model_dump(mode="json")
                                                for t in tools.tools
                                            ],
                                        },
                                        ensure_ascii=False,
                                        indent=2,
                                    )
                                )

                                async def invoke(name, args, expect_error=False):
                                    start = time.monotonic()
                                    result = await client.call_tool(name, args)
                                    filename = f"{len(rows) + 1:03}-{name}.json"
                                    (output / filename).write_text(
                                        result.model_dump_json(indent=2)
                                    )
                                    row = {
                                        "tool": name,
                                        "is_error": result.isError,
                                        "seconds": round(time.monotonic() - start, 3),
                                        "artifact": filename,
                                    }
                                    rows.append(row)
                                    print("RADAR " + json.dumps(row), flush=True)
                                    self.assertEqual(
                                        bool(result.isError), expect_error, filename
                                    )
                                    called.add(name)
                                    return result.structuredContent

                                policy = await invoke("get_editorial_policy", {})
                                taxonomy, catalog = [], []
                                for tool, target in [
                                    ("get_taxonomy", taxonomy),
                                    ("search_markets", catalog),
                                ]:
                                    cursor = 0
                                    while True:
                                        page = await invoke(
                                            tool, {"cursor": cursor, "limit": 2}
                                        )
                                        target.extend(page["items"])
                                        if not page["has_more"]:
                                            break
                                        cursor = int(page["next_cursor"])
                                if catalog:
                                    await invoke(
                                        "get_market", {"market_id": catalog[0]["id"]}
                                    )
                                await invoke("get_editorial_signals", {"days": 7})
                                (output / "context.json").write_text(
                                    json.dumps(
                                        {
                                            "catalog": catalog,
                                            "taxonomy": taxonomy,
                                            "policy_version": policy["version"],
                                            "policy_hash": policy["hash"],
                                            "criteria": policy["criteria"],
                                            "internal_coverage": snapshot["coverage"],
                                            "metrics_note": "No predictions/analytics copied; isolated sample cannot estimate production demand.",
                                        },
                                        ensure_ascii=False,
                                        indent=2,
                                    )
                                )
                                if not plan:
                                    return
                                self.assertEqual(plan["policy_hash"], policy["hash"])
                                for candidate in plan["candidates"]:
                                    classification = candidate["classification"]
                                    matches = [
                                        t
                                        for t in taxonomy
                                        if [t["category"], t["subcategory"], t["event"]]
                                        == classification
                                    ]
                                    self.assertEqual(len(matches), 1)
                                    ids = matches[0]
                                    for query in candidate["queries"]:
                                        await invoke(
                                            "search_markets", {"q": query, "limit": 20}
                                        )
                                    draft = {
                                        **candidate["draft"],
                                        "category_id": ids["category_id"],
                                        "subcategory_id": ids["subcategory_id"],
                                        "event_id": ids["event_id"],
                                    }
                                    draft["editorial_record"].update(
                                        policy_version=policy["version"],
                                        policy_hash=policy["hash"],
                                    )
                                    valid = await invoke(
                                        "validate_market_draft", {"draft": draft}
                                    )
                                    self.assertTrue(valid["structurally_valid"])
                                    create_input = {
                                        "draft": {
                                            **draft,
                                            "idempotency_key": candidate["key"]
                                            + "-create",
                                        }
                                    }
                                    first = await invoke(
                                        "create_market_draft", create_input
                                    )
                                    replay = await invoke(
                                        "create_market_draft", create_input
                                    )
                                    self.assertEqual(
                                        first["market_id"], replay["market_id"]
                                    )
                                    self.assertTrue(replay["replayed"])
                                    mid = first["market_id"]
                                    draft["summary"] = candidate["updated_summary"]
                                    updated = await invoke(
                                        "update_market_draft",
                                        {
                                            "market_id": mid,
                                            "draft": {
                                                **draft,
                                                "expected_revision": first["revision"],
                                                "idempotency_key": candidate["key"]
                                                + "-update",
                                            },
                                        },
                                    )
                                    market = await invoke(
                                        "get_market", {"market_id": mid}
                                    )
                                    self.assertEqual(market["status"], "draft")
                                    self.assertEqual(
                                        market["summary"], candidate["updated_summary"]
                                    )
                                    submitted = await invoke(
                                        "submit_draft_for_review",
                                        {
                                            "market_id": mid,
                                            "submission": {
                                                "expected_revision": updated[
                                                    "revision"
                                                ],
                                                "idempotency_key": candidate["key"]
                                                + "-submit",
                                            },
                                        },
                                    )
                                    self.assertEqual(
                                        submitted["editorial_status"], "in_review"
                                    )
                                    review = await invoke(
                                        "get_draft_review", {"market_id": mid}
                                    )
                                    self.assertEqual(review["state"], "in_review")
                                    self.assertFalse(review["decision"])
                                    await invoke(
                                        "update_market_draft",
                                        {
                                            "market_id": mid,
                                            "draft": {
                                                **draft,
                                                "expected_revision": submitted[
                                                    "revision"
                                                ],
                                                "idempotency_key": candidate["key"]
                                                + "-blocked",
                                            },
                                        },
                                        expect_error=True,
                                    )
                                    created.append(
                                        {
                                            "market_id": mid,
                                            "title": draft["title"],
                                            "state": review["state"],
                                            "revision": review["revision"],
                                            "snapshot_hash": review["snapshot_hash"],
                                            "pending": valid["pending"],
                                            "human_decision": review["decision"],
                                        }
                                    )
                                self.assertEqual(called, {t.name for t in tools.tools})

                    asyncio.run(run())
                self.assertEqual(EditorialDraft.objects.count(), len(created))
                self.assertEqual(
                    Market.objects.count(), len(snapshot["markets"]) + len(created)
                )
                self.assertEqual(
                    EditorialDraft.objects.filter(state="in_review").count(),
                    len(created),
                )
                logs = list(
                    SystemLog.objects.filter(
                        context__integration_id=str(self.iid)
                    ).values("context", "request_id")
                )
                self.assertEqual(len(logs), len(rows) * 3)
                self.assertTrue(
                    all(
                        x["context"].get("execution_id") and x["request_id"]
                        for x in logs
                    )
                )
                if plan:
                    self.assertEqual(
                        sum(
                            Quota.objects.filter(
                                integration_id=self.iid, bucket__startswith="draft:"
                            ).values_list("count", flat=True)
                        ),
                        len(created),
                    )
                report = {
                    "mode": mode,
                    "database": connection.settings_dict["NAME"],
                    "calls": rows,
                    "tools_executed": sorted(called),
                    "created": created,
                    "revision_records": EditorialRevision.objects.count(),
                    "quota_rows": list(
                        Quota.objects.filter(integration_id=self.iid).values()
                    ),
                    "log_count": len(logs),
                    "correlated_log_count": sum(
                        bool(x["context"].get("execution_id") and x["request_id"])
                        for x in logs
                    ),
                    "isolation": "Disposable PostgreSQL, loopback HTTP, separate adapter process without DB environment; no human decision simulated.",
                }
                (output / "report.json").write_text(
                    json.dumps(report, ensure_ascii=False, indent=2, default=str)
                )
                print("RADAR_COMPLETE " + str(output / "report.json"), flush=True)
            finally:
                if adapter:
                    adapter.terminate()
                    try:
                        adapter.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        adapter.kill()
                        adapter.wait(timeout=5)
                api_server.should_exit = True
                thread.join(5)
