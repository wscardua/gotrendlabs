import os
import base64
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

from django.test import SimpleTestCase, RequestFactory
from apps.api.backend_api import (
    badge_image_service as b,
    thumbnail_service as s,
    thumbnail_worker as w,
    thumbnail_provider as p,
)
from apps.api.backend_api.db import get_connection
from apps.web.django.admin_ops.models import SiteConfig
from apps.web.django.admin_ops import views
from apps.web.django.accounts.api_client import AuthAPIError
from apps.web.django.accounts.models import BadgeDefinition
from tests import test_thumbnails as fixtures
from tests.test_cases import AppendOnlyTransactionTestCase


class BadgeImageIntegrationTests(AppendOnlyTransactionTestCase):
    def setUp(self):
        fixtures.ThumbnailIntegrationTests.setUp(self)
        policy = SiteConfig.get_solo()
        policy.badge_image_enabled = True
        policy.save()
        self.env_badge = patch.dict(
            os.environ, {"GTL_BADGE_PUBLIC_ROOT": self.temp.name + "/badges"}
        )
        self.env_badge.start()
        self.addCleanup(self.env_badge.stop)
        self.badge_count = BadgeDefinition.objects.count()
        self.editor = uuid4()
        self.path = "/admin/badge-images/" + str(self.editor)

    def context(self, **changes):
        return {
            "request_id": str(uuid4()),
            "name": "Primeira resolução",
            "description": "Participou da primeira previsão resolvida.",
            "rule_description": "Uma previsão concluída.",
            "badge_type": "global",
            "category": "",
            "subcategory": "",
            "event": "",
            **changes,
        }

    def request(self, **changes):
        body = self.context(**changes)
        r = self.api.post(self.path, json=body, headers=self.headers)
        self.assertEqual(r.status_code, 202, r.text)
        return r.json(), body

    def status(self, id):
        return self.api.get(self.path + "/" + str(id), headers=self.headers)

    def ready(self, **changes):
        job, body = self.request(**changes)
        self.assertTrue(
            w.run_once(provider=lambda job: (fixtures.png(), "mock-id", None))
        )
        self.assertEqual(self.status(job["request_id"]).json()["state"], "succeeded")
        return job, body

    def badge_payload(self, job=None, **changes):
        return {
            "code": "generated-badge",
            "name": "Primeira resolução",
            "description": "Participou.",
            "rule_description": "Uma previsão concluída.",
            "badge_type": "global",
            "rule_type": "resolved_predictions_count",
            "threshold_value": 1,
            "image_url": "/media/old-light.png",
            "image_dark_url": "/media/old-dark.png",
            **(
                {
                    "badge_image_candidate_id": job["request_id"],
                    "badge_image_editor_id": str(self.editor),
                }
                if job
                else {}
            ),
            **changes,
        }

    def create_badge(self, job=None, **changes):
        r = self.api.post(
            "/admin/badges",
            json=self.badge_payload(job, **changes),
            headers=self.headers,
        )
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()

    def apply_payload(self, badge, job, **changes):
        return self.badge_payload(
            job,
            badge_image_expected_image_url=badge["image_url"],
            badge_image_expected_dark_url=badge["image_dark_url"],
            badge_image_expected_updated_at=badge["updated_at"],
            **changes,
        )

    def test_current_context_no_badge_creation_and_only_required_visual_fields(self):
        job, body = self.request(
            name="Nome ainda não salvo", description="Descrição atual"
        )
        self.assertEqual(BadgeDefinition.objects.count(), self.badge_count)
        self.assertEqual(job["snapshot"]["name"], body["name"])
        self.assertEqual(
            self.api.post(
                self.path, json=self.context(name=" "), headers=self.headers
            ).status_code,
            422,
        )
        self.assertEqual(
            self.api.post(
                self.path,
                json=self.context(admin_notes="private"),
                headers=self.headers,
            ).status_code,
            422,
        )
        with get_connection() as conn, conn.cursor() as cursor:
            cursor.execute(
                "SELECT provider_config FROM gotrendlabs_thumbnail_jobs WHERE id=%s",
                (job["request_id"],),
            )
            self.assertEqual(
                cursor.fetchone()["provider_config"]["aspect_ratio"], "1:1"
            )

    def test_staff_mfa_protected_preview_and_editor_scope(self):
        job, _ = self.ready()
        url = self.path + "/" + job["request_id"] + "/preview"
        self.assertEqual(self.api.get(url).status_code, 401)
        self.session.mfa_verified_at = None
        self.session.save()
        self.assertEqual(self.api.get(url, headers=self.headers).status_code, 403)
        self.session.mfa_verified_at = s.now()
        self.session.save()
        response = self.api.get(url, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["cache-control"], "private, no-store")
        self.assertEqual(
            self.api.get(
                "/admin/badge-images/" + str(uuid4()) + "/" + job["request_id"],
                headers=self.headers,
            ).status_code,
            404,
        )
        self.user.is_staff = False
        self.user.save()
        self.assertEqual(self.status(job["request_id"]).status_code, 403)

    def test_reloaded_editor_recovers_existing_job_without_generation(self):
        from django.http import HttpResponse
        browser_session={"auth_api_token":"fixture", "auth_api_user":{"is_staff":True}}
        factory=RequestFactory()
        ids=[]
        with patch.object(views,"admin_get_taxonomy",return_value={"categories":[]}), patch.object(views,"admin_get_badges",return_value={"badges":[{"code":"saved","name":"Badge","badge_type":"global","rule_type":"resolved_predictions_count"}]}), patch.object(views,"render",return_value=HttpResponse("fixture")) as render:
            for _ in range(2):
                request=factory.get("/admin-ops/badges/saved/edit/")
                request.session=browser_session
                views.badge_form(request,mode="edit",code="saved")
                ids.append(render.call_args.args[2]["badge_editor_id"])
        self.assertEqual(ids[0],ids[1])
        badge=self.create_badge(code="saved")
        self.editor=ids[0]
        self.path="/admin/badge-images/"+str(self.editor)
        job,_=self.request(badge_code=badge["code"])
        with patch("apps.api.backend_api.thumbnail_provider.httpx.post") as paid:
            result=self.api.get("/admin/badge-images/"+str(ids[1]),headers=self.headers)
            self.assertEqual(result.json()["request_id"],job["request_id"])
            self.assertEqual(result.json()["state"],"queued")
            paid.assert_not_called()
        with get_connection() as conn,conn.cursor() as cursor:
            cursor.execute("SELECT count(*) AS n FROM gotrendlabs_thumbnail_jobs")
            self.assertEqual(cursor.fetchone()["n"],1)

    def test_candidate_owned_by_operator_and_session(self):
        job, _ = self.ready()
        with get_connection() as conn, conn.cursor() as cursor:
            cursor.execute(
                "UPDATE gotrendlabs_thumbnail_jobs SET session_id=session_id+999 WHERE id=%s",
                (job["request_id"],),
            )
        self.assertEqual(self.status(job["request_id"]).status_code, 404)
        r = self.api.post(
            "/admin/badges", json=self.badge_payload(job), headers=self.headers
        )
        self.assertEqual(r.status_code, 404)
        self.assertEqual(BadgeDefinition.objects.count(), self.badge_count)

    def test_idempotency_active_limit_and_polling_no_generation(self):
        job, body = self.request()
        self.assertEqual(
            self.api.post(self.path, json=body, headers=self.headers).json()[
                "request_id"
            ],
            job["request_id"],
        )
        self.assertEqual(
            self.api.post(
                self.path, json={**body, "name": "changed"}, headers=self.headers
            ).status_code,
            409,
        )
        self.assertEqual(
            self.api.post(
                self.path, json=self.context(), headers=self.headers
            ).status_code,
            409,
        )
        for _ in range(3):
            self.assertEqual(self.status(job["request_id"]).json()["state"], "queued")
        with get_connection() as conn, conn.cursor() as cursor:
            cursor.execute("SELECT count(*) AS n FROM gotrendlabs_thumbnail_jobs")
            self.assertEqual(cursor.fetchone()["n"], 1)

    def test_global_and_operator_limits_shared_with_markets(self):
        with patch.dict(os.environ, {"GTL_THUMB_GLOBAL_LIMIT": "2"}):
            self.request()
            r = self.api.post(
                "/admin/markets/thumb-market/thumbnails",
                json=fixtures.ThumbnailIntegrationTests.payload(self),
                headers=self.headers,
            )
            self.assertEqual(r.status_code, 429, r.text)
        with patch.dict(os.environ, {"GTL_THUMB_OPERATOR_LIMIT": "1"}):
            other = "/admin/badge-images/" + str(uuid4())
            self.assertEqual(
                self.api.post(
                    other, json=self.context(), headers=self.headers
                ).status_code,
                429,
            )

    def test_shared_capacity_reserved_between_concurrent_editors(self):
        with (
            patch.dict(os.environ, {"GTL_THUMB_GLOBAL_LIMIT": "2"}),
            ThreadPoolExecutor(max_workers=2) as pool,
        ):

            def call(_):
                return self.api.post(
                    "/admin/badge-images/" + str(uuid4()),
                    json=self.context(),
                    headers=self.headers,
                ).status_code

            self.assertEqual(sorted(pool.map(call, range(2))), [202, 429])

    def test_create_confirms_theme_pair_and_preserves_rules(self):
        job, body = self.ready()
        badge = self.create_badge(job)
        self.assertTrue(badge["image_url"].startswith("/media/badge_images/"))
        self.assertTrue(badge["image_dark_url"].startswith("/media/badge_images/"))
        self.assertNotEqual(badge["image_url"], badge["image_dark_url"])
        self.assertEqual(badge["rule_type"], "resolved_predictions_count")
        self.assertEqual(badge["awards_count"], 0)
        self.assertTrue(
            (s.public_root("badge") / badge["image_url"].split("/")[-1]).is_file()
        )
        repeated = self.api.post(self.path, json=body, headers=self.headers)
        self.assertEqual(repeated.status_code, 202)
        reuse = self.api.post(
            "/admin/badges",
            json=self.badge_payload(job, code="reuse"),
            headers=self.headers,
        )
        self.assertEqual(reuse.status_code, 409)
        self.assertEqual(BadgeDefinition.objects.count(), self.badge_count + 1)

    def test_existing_badge_expected_version_and_urls_are_required(self):
        badge = self.create_badge()
        job, _ = self.ready(badge_code=badge["code"])
        url = "/admin/badges/" + badge["code"]
        self.assertEqual(
            self.api.patch(
                url, json=self.badge_payload(job), headers=self.headers
            ).status_code,
            409,
        )
        payload = self.apply_payload(badge, job)
        self.assertEqual(
            self.api.patch(
                url,
                json={**payload, "badge_image_expected_dark_url": "wrong"},
                headers=self.headers,
            ).status_code,
            409,
        )
        r = self.api.patch(url, json=payload, headers=self.headers)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(r.json()["image_dark_url"].startswith("/media/badge_images/"))

    def test_other_badge_editor_and_market_candidate_rejected(self):
        badge = self.create_badge()
        job, _ = self.ready(badge_code=badge["code"])
        other = self.create_badge(code="other-badge")
        self.assertEqual(
            self.api.patch(
                "/admin/badges/other-badge",
                json=self.apply_payload(other, job),
                headers=self.headers,
            ).status_code,
            409,
        )
        self.assertEqual(
            self.api.patch(
                "/admin/badges/" + badge["code"],
                json=self.apply_payload(badge, job, badge_image_editor_id=str(uuid4())),
                headers=self.headers,
            ).status_code,
            404,
        )
        self.assertEqual(
            self.api.post(
                "/admin/badges",
                json=self.badge_payload(job, code="new-other"),
                headers=self.headers,
            ).status_code,
            409,
        )
        r = self.api.post(
            "/admin/markets/thumb-market/thumbnails",
            json=fixtures.ThumbnailIntegrationTests.payload(self),
            headers=self.headers,
        )
        self.assertEqual(r.status_code, 202, r.text)
        w.run_once(provider=lambda job: (fixtures.png(), None, None))
        self.assertEqual(
            self.api.post(
                "/admin/badges",
                json=self.badge_payload(
                    {"request_id": r.json()["request_id"]}, code="market-candidate"
                ),
                headers=self.headers,
            ).status_code,
            404,
        )

    def test_expired_incomplete_and_storage_failure_preserve_existing_images(self):
        badge = self.create_badge()
        job, _ = self.request(badge_code=badge["code"])
        url = "/admin/badges/" + badge["code"]
        payload = self.apply_payload(badge, job)
        self.assertEqual(
            self.api.patch(url, json=payload, headers=self.headers).status_code, 409
        )
        w.run_once(provider=lambda job: (fixtures.png(), None, None))
        with patch("pathlib.Path.mkdir", side_effect=OSError("storage")):
            self.assertEqual(
                self.api.patch(url, json=payload, headers=self.headers).status_code, 503
            )
        stored = BadgeDefinition.objects.get(code=badge["code"])
        self.assertEqual(stored.image_url, badge["image_url"])
        with get_connection() as conn, conn.cursor() as cursor:
            cursor.execute(
                "UPDATE gotrendlabs_thumbnail_jobs SET expires_at=%s WHERE id=%s",
                (s.now() - timedelta(seconds=1), job["request_id"]),
            )
        self.assertEqual(
            self.api.patch(url, json=payload, headers=self.headers).status_code, 409
        )

    def test_manual_update_fences_stale_candidate(self):
        badge = self.create_badge()
        job, _ = self.ready(badge_code=badge["code"])
        url = "/admin/badges/" + badge["code"]
        manual = self.api.patch(
            url,
            json=self.badge_payload(image_url="/media/manual.png"),
            headers=self.headers,
        )
        self.assertEqual(manual.status_code, 200)
        self.assertEqual(
            self.api.patch(
                url, json=self.apply_payload(badge, job), headers=self.headers
            ).status_code,
            409,
        )
        self.assertEqual(
            BadgeDefinition.objects.get(code=badge["code"]).image_url,
            "/media/manual.png",
        )

    def test_concurrent_confirmations_apply_only_once(self):
        badge = self.create_badge()
        job, _ = self.ready(badge_code=badge["code"])
        payload = self.apply_payload(badge, job)
        barrier = threading.Barrier(2)

        def apply(_):
            barrier.wait(timeout=5)
            return self.api.patch(
                "/admin/badges/" + badge["code"], json=payload, headers=self.headers
            ).status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(apply, range(2))), [200, 409])

    def test_unknown_provider_result_and_restart_never_repeat_paid_call(self):
        job, _ = self.request()

        def unknown(job):
            raise p.ProviderFailure("timeout", uncertain=True)

        w.run_once(provider=unknown)
        self.assertEqual(self.status(job["request_id"]).json()["state"], "uncertain")
        with patch("apps.api.backend_api.thumbnail_provider.httpx.post") as paid:
            self.assertFalse(w.run_once())
            paid.assert_not_called()
        self.editor = uuid4()
        self.path = "/admin/badge-images/" + str(self.editor)
        next_job, _ = self.request()
        with get_connection() as conn, conn.cursor() as cursor:
            cursor.execute(
                "UPDATE gotrendlabs_thumbnail_jobs SET state='running',lease_until=%s WHERE id=%s",
                (s.now() - timedelta(seconds=1), next_job["request_id"]),
            )
        self.assertFalse(w.run_once(provider=unknown))
        self.assertEqual(
            self.status(next_job["request_id"]).json()["state"], "uncertain"
        )

    def test_worker_respects_independent_switch_and_revoked_session(self):
        policy = SiteConfig.get_solo()
        policy.thumbnail_enabled = False
        policy.save()
        job, _ = self.request()
        self.session.revoked_at = s.now()
        self.session.save()
        called = []
        self.assertTrue(w.run_once(provider=lambda job: called.append(job)))
        self.assertEqual(called, [])
        with get_connection() as conn, conn.cursor() as cursor:
            cursor.execute(
                "SELECT state FROM gotrendlabs_thumbnail_jobs WHERE id=%s",
                (job["request_id"],),
            )
            self.assertEqual(cursor.fetchone()["state"], "failed")

    def test_settings_are_admin_audited_and_do_not_invoke_provider(self):
        with patch("apps.api.backend_api.thumbnail_provider.httpx.post") as paid:
            path = "/admin/badge-image-settings"
            self.assertEqual(self.api.get(path).status_code, 401)
            self.assertEqual(
                self.api.put(path, json={}, headers=self.headers).status_code, 422
            )
            r = self.api.put(
                path, json={"badge_image_enabled": False}, headers=self.headers
            )
            self.assertEqual(r.status_code, 200)
            self.assertEqual(
                self.api.post(
                    self.path, json=self.context(), headers=self.headers
                ).status_code,
                503,
            )
            paid.assert_not_called()

    def test_cleanup_preserves_both_linked_theme_files_and_removes_orphans(self):
        root = s.public_root("badge")
        root.mkdir(parents=True)
        names = [str(uuid4()) + ".png" for _ in range(3)]
        for name in names:
            (root / name).write_bytes(fixtures.png())
            os.utime(root / name, (time.time() - 7200,) * 2)
        self.create_badge(
            image_url="/media/badge_images/" + names[0],
            image_dark_url="/media/badge_images/" + names[1],
        )
        w.prune()
        self.assertTrue((root / names[0]).exists())
        self.assertTrue((root / names[1]).exists())
        self.assertFalse((root / names[2]).exists())

    def test_pair_has_distinct_files_private_previews_and_audited_calls(self):
        from io import BytesIO
        from PIL import Image
        job, _ = self.request()
        def provider(j):
            out = BytesIO()
            Image.new("RGB", (512,512), "ivory" if j["theme"] == "light" else "darkgreen").save(out, "PNG")
            return out.getvalue(), "mock-" + j["theme"], {"images": 1}
        with patch.object(w, "eligible", wraps=w.eligible):
            self.assertTrue(w.run_once(provider=provider))
        url = self.path + "/" + job["request_id"] + "/preview"
        light = self.api.get(url, headers=self.headers)
        dark = self.api.get(url + "?theme=dark", headers=self.headers)
        self.assertEqual(dark.status_code, 200)
        self.assertNotEqual(light.content, dark.content)
        self.assertEqual(self.api.get(url + "?theme=dark").status_code, 401)
        self.assertEqual(self.api.get(url + "?theme=invalid", headers=self.headers).status_code, 422)
        with get_connection() as conn, conn.cursor() as cursor:
            cursor.execute("SELECT usage FROM gotrendlabs_thumbnail_jobs WHERE id=%s", (job["request_id"],))
            records = cursor.fetchone()["usage"]["variants"]
            self.assertEqual(records["light"]["provider_id"], "mock-light")
            self.assertEqual(records["dark"]["reported_usage"], {"images": 1})
        badge = self.create_badge(job)
        for theme, field in (("light","image_url"),("dark","image_dark_url")):
            expected = light.content if theme == "light" else dark.content
            self.assertEqual((s.public_root("badge") / badge[field].split("/")[-1]).read_bytes(), expected)

    def test_partial_provider_failure_never_selects_applies_or_retries_pair(self):
        for uncertain in (False, True):
            with self.subTest(uncertain=uncertain):
                self.editor = uuid4()
                self.path = "/admin/badge-images/" + str(self.editor)
                job, _ = self.request()
                calls = []
                def provider(j):
                    calls.append(j["theme"])
                    if j["theme"] == "dark":
                        raise p.ProviderFailure("timeout" if uncertain else "content_refusal", uncertain=uncertain, provider_id="dark-failed")
                    return fixtures.png(), "light-ok", {"images":1}
                w.run_once(provider=provider)
                self.assertEqual(calls, ["light", "dark"])
                result = self.status(job["request_id"]).json()
                self.assertEqual(result["state"], "uncertain" if uncertain else "failed")
                self.assertIsNone(result["candidate_id"])
                self.assertEqual(self.api.post("/admin/badges",json=self.badge_payload(job,code=str(uuid4())),headers=self.headers).status_code,409)
                self.assertEqual(self.api.get(self.path+"/"+job["request_id"]+"/preview",headers=self.headers).status_code,409)
                self.assertFalse(w.run_once(provider=provider))
                self.assertEqual(len(calls), 2)
                with get_connection() as conn, conn.cursor() as cursor:
                    cursor.execute("SELECT usage FROM gotrendlabs_thumbnail_jobs WHERE id=%s", (job["request_id"],))
                    self.assertEqual(cursor.fetchone()["usage"]["variants"]["light"]["provider_id"], "light-ok")

    def test_invalid_dark_image_and_private_storage_failure_leave_no_pair(self):
        job, _ = self.request()
        w.run_once(provider=lambda j: (fixtures.png() if j["theme"] == "light" else b"invalid", j["theme"], None))
        self.assertEqual(self.status(job["request_id"]).json()["state"], "failed")
        job, _ = self.request()
        from pathlib import Path
        original = Path.open
        def open_path(path, *args, **kwargs):
            if path.name.endswith(".dark.png") and args and args[0] == "xb":
                raise OSError("storage")
            return original(path, *args, **kwargs)
        with patch.object(Path, "open", open_path):
            w.run_once(provider=lambda j: (fixtures.png(), j["theme"], None))
        self.assertEqual(self.status(job["request_id"]).json()["state"], "failed")
        self.assertFalse((s.private_root()/(job["request_id"]+".png")).exists())

    def test_missing_dark_and_legacy_single_image_candidate_cannot_be_applied(self):
        job, _ = self.ready()
        (s.private_root()/(job["request_id"]+".dark.png")).unlink()
        self.assertEqual(self.api.post("/admin/badges",json=self.badge_payload(job),headers=self.headers).status_code,409)
        with get_connection() as conn, conn.cursor() as cursor:
            cursor.execute("UPDATE gotrendlabs_thumbnail_jobs SET instructions_version='badge-image-bedrock-v1' WHERE id=%s", (job["request_id"],))
        self.assertEqual(self.api.post("/admin/badges",json=self.badge_payload(job),headers=self.headers).status_code,409)

    def test_restart_during_second_call_preserves_first_receipt_without_replay(self):
        job, _ = self.request()
        def provider(j):
            if j["theme"] == "dark":
                raise SystemExit("simulated process exit")
            return fixtures.png(), "light-receipt", {"images": 1}
        with self.assertRaises(SystemExit):
            w.run_once(provider=provider)
        with get_connection() as conn, conn.cursor() as cursor:
            cursor.execute("SELECT usage FROM gotrendlabs_thumbnail_jobs WHERE id=%s", (job["request_id"],))
            records = cursor.fetchone()["usage"]["variants"]
            self.assertEqual(records["light"]["provider_id"], "light-receipt")
            self.assertEqual(records["dark"]["state"], "started")
            cursor.execute("UPDATE gotrendlabs_thumbnail_jobs SET lease_until=%s WHERE id=%s", (s.now()-timedelta(seconds=1),job["request_id"]))
        with patch("apps.api.backend_api.thumbnail_provider.httpx.post") as paid:
            self.assertFalse(w.run_once())
            paid.assert_not_called()
        self.assertEqual(self.status(job["request_id"]).json()["state"], "uncertain")

    def test_pair_capacity_requires_two_units_before_any_provider_call(self):
        with patch.dict(os.environ, {"GTL_THUMB_GLOBAL_LIMIT":"1"}):
            self.assertEqual(self.api.post(self.path,json=self.context(),headers=self.headers).status_code,429)
        with patch.dict(os.environ, {"GTL_THUMB_OPERATOR_LIMIT":"1"}):
            self.assertEqual(self.api.post(self.path,json=self.context(),headers=self.headers).status_code,429)

    def test_second_public_file_failure_compensates_and_preserves_previous_pair(self):
        from pathlib import Path
        badge = self.create_badge()
        job, _ = self.ready(badge_code=badge["code"])
        original = Path.open
        calls = []
        def open_path(path, *args, **kwargs):
            if path.parent == s.public_root("badge") and args and args[0] == "xb":
                calls.append(path)
                if len(calls) == 2: raise OSError("storage")
            return original(path, *args, **kwargs)
        with patch.object(Path, "open", open_path):
            result = self.api.patch("/admin/badges/"+badge["code"],json=self.apply_payload(badge,job),headers=self.headers)
        self.assertEqual(result.status_code,503)
        stored = BadgeDefinition.objects.get(code=badge["code"])
        self.assertEqual((stored.image_url,stored.image_dark_url),(badge["image_url"],badge["image_dark_url"]))
        self.assertFalse(calls[0].exists())

    def test_cleanup_removes_both_expired_private_variants(self):
        job, _ = self.ready()
        with get_connection() as conn, conn.cursor() as cursor:
            cursor.execute("UPDATE gotrendlabs_thumbnail_jobs SET expires_at=%s WHERE id=%s",(s.now()-timedelta(seconds=1),job["request_id"]))
        w.prune()
        for suffix in ("", ".dark"):
            self.assertFalse((s.private_root()/(job["request_id"]+suffix+".png")).exists())


class BadgeImagePromptTests(SimpleTestCase):
    def test_single_native_invocation_uses_badge_prompt_and_square_format(self):
        import httpx

        job = {
            "kind": "badge",
            "provider": "bedrock",
            "instructions_version": b.VERSION,
            "image_model": "stability.stable-image-core-v1:1",
            "provider_config": {
                "region": "us-west-2",
                "aspect_ratio": "1:1",
                "timeout_seconds": 180,
                "seed": 42,
            },
            "snapshot": {
                "name": "Conquista específica",
                "description": "Mérito de participação",
                "admin_notes": "PRIVATE",
            },
        }
        response = httpx.Response(
            200,
            json={
                "images": [base64.b64encode(fixtures.png()).decode()],
                "finish_reasons": [None],
            },
            headers={"x-amzn-requestid": "fixture"},
        )
        with (
            patch.dict(os.environ, {"AWS_BEARER_TOKEN_BEDROCK": "fixture"}),
            patch.object(p.httpx, "post", return_value=response) as call,
        ):
            image, provider_id, usage = p.generate(job)
        self.assertTrue(image)
        self.assertEqual(provider_id, "fixture")
        call.assert_called_once()
        body = call.call_args.kwargs["json"]
        self.assertEqual(body["aspect_ratio"], "1:1")
        self.assertIn("Conquista específica", body["prompt"])
        self.assertNotIn("PRIVATE", body["prompt"])

    def test_visual_context_whitelist_and_badge_instructions(self):
        prompt, negative = b.visual_prompt(
            {
                "snapshot": {
                    "name": "Primeira resolução",
                    "description": "Comunidade",
                    "admin_notes": "DO NOT SEND SECRET",
                    "users": ["private"],
                },
                "variation": 1,
            }
        )
        self.assertIn("Primeira resolução", prompt)
        self.assertIn("48", prompt)
        self.assertIn("geometric shield", prompt)
        self.assertNotIn("DO NOT SEND SECRET", prompt)
        self.assertNotIn("private", prompt)
        self.assertIn("casino", negative)
        dark, _ = b.visual_prompt({"snapshot":{"name":"Primeira resolução"},"theme":"dark","variation":1})
        self.assertIn("Theme: LIGHT UI", prompt)
        self.assertIn("Theme: DARK UI", dark)
        self.assertIn("geometric shield", dark)


class BadgeImageWebTests(SimpleTestCase):
    def setUp(self):
        from django.http import HttpResponse

        self.factory = RequestFactory()
        self.session = {
            "auth_api_token": "fixture",
            "auth_api_user": {"is_staff": True},
        }
        self.body = {
            "name": "Conquista",
            "description": "Descrição pública",
            "badge_type": "global",
            "rule_type": "resolved_predictions_count",
            "threshold_value": "1",
            "image_url": "/media/old.png",
            "image_dark_url": "/media/dark.png",
            "action": "save",
            "badge_image_editor_id": str(uuid4()),
        }
        self.patches = [
            patch.object(views, "admin_get_taxonomy", return_value={"categories": []}),
            patch.object(views, "render", return_value=HttpResponse("fixture")),
            patch.object(views.messages, "success"),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def post(self, **changes):
        request = self.factory.post("/admin-ops/badges/new/", {**self.body, **changes})
        request.session = self.session
        return views.badge_form(request, mode="new")

    def test_editor_identity_survives_reload_and_is_scoped_to_badge_and_session(self):
        first = []
        with patch.object(views, "admin_get_badges", return_value={"badges":[{"code":"existing-badge","name":"Badge","badge_type":"global","rule_type":"resolved_predictions_count"}]}), patch.object(views, "render") as render:
            for _ in range(2):
                request = self.factory.get("/admin-ops/badges/existing-badge/edit/")
                request.session = self.session
                views.badge_form(request, mode="edit", code="existing-badge")
                first.append(render.call_args.args[2]["badge_editor_id"])
        self.assertEqual(first[0],first[1])
        # Registry eviction must not lose a saved badge's stable identity.
        saved_registry = self.session.pop("badge_image_editors")
        request = self.factory.get("/admin-ops/badges/existing-badge/edit/")
        request.session = self.session
        recreated,_ = views._badge_image_editor(request,"existing-badge","fixture")
        self.assertEqual(first[0],recreated)
        self.session["badge_image_editors"] = saved_registry
        request = self.factory.get("/admin-ops/badges/new/")
        request.session = self.session
        different,_ = views._badge_image_editor(request,"other-badge","fixture")
        self.assertNotEqual(first[0],different)
        new_session,_ = views._badge_image_editor(request,"existing-badge","another-session")
        self.assertNotEqual(first[0],new_session)

    def test_new_editor_is_reused_until_successful_creation_then_rotated(self):
        request = self.factory.get("/admin-ops/badges/new/")
        request.session = self.session
        first,_ = views._badge_image_editor(request,None,"fixture")
        same,_ = views._badge_image_editor(request,None,"fixture")
        self.assertEqual(first,same)
        with patch.object(views,"admin_create_badge",return_value={"code":"created"}):
            self.assertEqual(self.post(badge_image_editor_id=str(first)).status_code,302)
        next_editor,_ = views._badge_image_editor(request,None,"fixture")
        self.assertNotEqual(first,next_editor)

    def test_candidate_ignores_both_old_uploads_and_uses_existing_save(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        candidate = str(uuid4())
        with (
            patch.object(views, "_save_badge_image") as upload,
            patch.object(
                views, "admin_create_badge", return_value={"code": "new-badge"}
            ) as create,
        ):
            result = self.post(
                badge_image_origin="generated",
                badge_image_candidate_id=candidate,
                badge_image=SimpleUploadedFile("old.png", fixtures.png(), "image/png"),
                badge_dark_image=SimpleUploadedFile(
                    "dark.png", fixtures.png(), "image/png"
                ),
            )
        self.assertEqual(result.status_code, 302)
        upload.assert_not_called()
        self.assertEqual(
            create.call_args.args[1]["badge_image_candidate_id"], candidate
        )

    def test_invalid_form_does_not_write_upload(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        with patch.object(views, "_save_badge_image") as upload:
            self.post(
                name="",
                badge_image=SimpleUploadedFile("file.png", fixtures.png(), "image/png"),
            )
        upload.assert_not_called()

    def test_confirmed_rejection_compensates_but_unknown_response_preserves_file(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        for code in (422, 503, None):
            with (
                self.subTest(code=code),
                patch.object(views, "_save_badge_image", return_value="new.png"),
                patch.object(
                    views,
                    "admin_create_badge",
                    side_effect=AuthAPIError("rejected", code),
                ),
                patch.object(views.BADGE_STORAGE, "delete") as delete,
            ):
                self.post(
                    badge_image_origin="upload",
                    badge_image=SimpleUploadedFile(
                        "file.png", fixtures.png(), "image/png"
                    ),
                )
                self.assertEqual(delete.call_count, 1 if code == 422 else 0)

    def test_generation_adapter_requires_csrf_and_anonymous_access_is_rejected(self):
        from django.test import Client

        client = Client(enforce_csrf_checks=True)
        self.assertEqual(
            client.post(
                "/admin-ops/badge-images/" + str(uuid4()) + "/",
                {},
                content_type="application/json",
            ).status_code,
            403,
        )
        self.assertEqual(
            client.get("/admin-ops/badge-images/" + str(uuid4()) + "/").status_code, 302
        )

    def test_badge_configuration_has_independent_form_and_backend_save(self):
        request = self.factory.post(
            "/admin-ops/config/",
            {"action": "badge_image_settings", "badge_image-badge_image_enabled": "on"},
        )
        request.session = self.session
        with (
            patch.object(SiteConfig, "get_solo", return_value=SiteConfig()),
            patch.object(views, "load_platform_config", return_value={}),
            patch.object(views, "thumbnail_api_request", return_value={}) as api,
        ):
            response = views.config(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(api.call_args.args[:2], ("PUT", "/admin/badge-image-settings"))
        self.assertEqual(api.call_args.args[2], {"badge_image_enabled": True})
