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
        self.assertNotEqual(next(x['position'] for x in row['markers'] if x['class']=='close'), next(x['position'] for x in row['markers'] if x['class']=='planned'))

    def test_editor_form_has_only_forecast_and_timezone_for_schedule(self):
        from apps.web.django.admin_ops.forms import AdminMarketForm
        fields=AdminMarketForm().fields
        self.assertIn('expected_resolution_at',fields)
        self.assertIn('schedule_timezone',fields)
        self.assertNotIn('evidence_cutoff_at',fields)
        self.assertNotIn('evidence_recovery_deadline_at',fields)



class ContractTimelinePresentationTests(SimpleTestCase):
    def market(self, status="locked", **changes):
        value = {**agenda(), "status": status, "slug": "fixture-contract", "title": "Contrato de teste",
                 "created_at": NOW - timedelta(days=10), "published_at": NOW - timedelta(days=9),
                 "close_timezone": "America/Sao_Paulo", "resolution_timezone": "America/Sao_Paulo"}
        value.update(changes)
        value["resolution_schedule"] = s.classification(value, now=NOW)
        return value

    def row(self, market, now=NOW):
        from apps.web.django.admin_ops.views import _build_contract_timeline
        return _build_contract_timeline([market], today=now, include_terminal=True)["rows"][0]

    def phases(self, market):
        return {p["label"]: p for p in self.row(market)["phase_steps"]}

    def test_all_states_and_closure_never_completed_by_clock(self):
        for status in ("draft", "scheduled", "open", "locked", "resolved", "sealed", "canceled"):
            for close in (NOW - timedelta(days=2), NOW + timedelta(days=2), None):
                with self.subTest(status=status, close=close):
                    phases = self.phases(self.market(status, close_at=close))
                    closed = status in {"locked", "resolved", "sealed"}
                    self.assertEqual(phases["Fechamento"]["state"] == "done", closed)
                    if closed:
                        self.assertEqual(phases["Fechamento"]["time_label"], "Fechado")
                        self.assertIn("instante efetivo de fechamento não informado", phases["Fechamento"]["note"])
                    elif status in {"open", "scheduled"} and close and close <= NOW:
                        self.assertEqual(phases["Fechamento"]["urgency"], "overdue")
                    self.assertFalse(any(p["state"] == "active" for p in phases.values()))

    def test_forecasts_follow_authoritative_classification_and_are_historical_in_terminals(self):
        for status in ("draft", "scheduled", "open", "locked", "resolved", "sealed", "canceled"):
            for expected in (NOW - timedelta(days=1), NOW + timedelta(days=1), None):
                with self.subTest(status=status, expected=expected):
                    m = self.market(status, close_at=NOW - timedelta(days=2), expected_resolution_at=expected)
                    phase = self.phases(m)["Resolução prevista"]
                    self.assertNotEqual(phase["state"], "done")
                    if status in s.TERMINAL:
                        self.assertEqual((phase["state"], phase["time_label"]), ("historical", "Histórica"))
                    elif m["resolution_schedule"]["code"] == "resolution_overdue":
                        self.assertEqual(phase["time_label"], "Previsão vencida")
                        self.assertEqual(phase["urgency"], "overdue")
                    elif expected is None:
                        self.assertEqual(phase["time_label"], "Não informada")
        # Django must not recompute the classification from its own clock.
        m = self.market(expected_resolution_at=NOW - timedelta(days=1))
        m["resolution_schedule"] = {"code": "resolution_scheduled", "label": "Apuração prevista"}
        self.assertEqual(self.phases(m)["Resolução prevista"]["time_label"], "Planejada")

    def test_actual_creation_publication_resolution_and_sealing_and_missing_dates(self):
        m = self.market("sealed", resolved_at=NOW - timedelta(hours=3), sealed_at=NOW - timedelta(hours=1), seal_due_at=NOW - timedelta(hours=2))
        phases = self.phases(m)
        for label in ("Criação", "Publicação", "Resolução efetiva", "Selagem"):
            self.assertEqual(phases[label]["state"], "done")
            self.assertNotEqual(phases[label]["date_label"], "Data não registrada")
        self.assertIn("Prazo previsto de selagem", phases["Selagem"]["note"])
        self.assertIn("Selagem efetiva", " ".join(x["label"] for x in self.row(m)["markers"]))
        for status in ("resolved", "sealed"):
            phases = self.phases(self.market(status, seal_due_at=NOW - timedelta(days=1)))
            self.assertNotEqual(phases["Resolução efetiva"]["state"], "pending")
            self.assertIn("data não registrada", phases["Resolução efetiva"]["time_label"])
            self.assertNotEqual(phases["Selagem"]["state"], "done")
        for status in ("draft", "scheduled"):
            self.assertNotIn("Publicação", self.phases(self.market(status, published_at=None)))

    def test_cancellation_and_undo_do_not_fabricate_obligations_or_actual_dates(self):
        phases = self.phases(self.market("canceled"))
        for label in ("Resolução efetiva", "Selagem"):
            self.assertEqual(phases[label]["time_label"], "Não se aplica")
            self.assertEqual(phases[label]["state"], "historical")
        # Undo clears resolved_at/seal_due_at in FastAPI, retaining the schedule.
        m = self.market("locked", resolved_at=None, seal_due_at=None, sealed_at=None)
        phases = self.phases(m)
        self.assertEqual(phases["Resolução efetiva"]["time_label"], "Pendente")
        self.assertEqual(phases["Selagem"]["time_label"], "Aguarda resolução")
        self.assertFalse(any(x["class"] in {"resolved", "sealed"} for x in self.row(m)["markers"]))

    def test_reschedule_retains_original_and_history_without_mutation(self):
        m = self.market(original_expected_resolution_at=NOW - timedelta(days=1), schedule_version=2,
                        schedule_history=[{"reason": "Fonte adiou anúncio", "after": {"expected_resolution_at": "2026-10-18T20:00:00Z"}}])
        before = copy.deepcopy(m)
        phases = self.phases(m)
        self.assertEqual(m, before)
        self.assertIn("18/10/2026", phases["Resolução prevista"]["date_label"])

    def test_same_day_markers_have_today_time_and_correct_zone_not_now(self):
        from apps.web.django.admin_ops.views import _contract_timeline_marker_context
        from django.utils import timezone as tz
        with tz.override("America/Sao_Paulo"):
            for offset in (-1, 0, 1):
                result = _contract_timeline_marker_context("Prazo", NOW + timedelta(hours=offset), NOW)
                self.assertIn("Hoje", result["label"])
                self.assertNotIn("Agora", result["label"])
                self.assertIn("America/Sao_Paulo", result["label"])
                self.assertIn(f"{17 + offset}:00:00", result["label"])
            value = datetime(2026, 10, 18, 1, tzinfo=UTC)
            self.assertEqual(_contract_timeline_marker_context("Prazo", value, NOW, "UTC")["time_class"], "future")
            self.assertEqual(_contract_timeline_marker_context("Prazo", value, NOW, "America/Sao_Paulo")["time_class"], "now")

    def test_coincident_markers_keep_stable_sequence(self):
        m = self.market("sealed", created_at=NOW, published_at=NOW, close_at=NOW,
                        expected_resolution_at=NOW, resolved_at=NOW, sealed_at=NOW, seal_due_at=NOW)
        row = self.row(m)
        self.assertEqual(len(row["markers"]), 7)
        self.assertEqual(len({x["position"] for x in row["markers"]}), 1)
        self.assertEqual([x["class"] for x in row["markers"]],
                         ["start", "published", "close", "planned", "resolved", "sealed", "planned"])
        self.assertEqual(sum(x["kind"] == "planned" for x in row["markers"]), 3)
        self.assertEqual(row["bar_progress_width"], 0)

    def test_sequence_is_chronological_and_closing_is_always_a_forecast(self):
        m = self.market("locked", close_at=NOW - timedelta(days=1))
        row = self.row(m)
        closing = next(x for x in row["markers"] if x["class"] == "close")
        self.assertEqual(closing["kind"], "planned")
        self.assertEqual(closing["name"], "Fechamento programado")
        self.assertIn("16/10", closing["short_date"])
        stamps = [marker["timestamp"] for marker in row["markers"]]
        self.assertEqual(stamps, sorted(stamps))
        early = self.row(self.market("resolved", resolved_at=NOW - timedelta(days=2)))
        self.assertEqual([m["timestamp"] for m in early["markers"]],
                         sorted(m["timestamp"] for m in early["markers"]))

    def test_today_durations_and_undated_stages(self):
        row = self.row(self.market("locked", published_at=None, resolved_at=None, sealed_at=None))
        sequence = row["time_sequence"]
        self.assertEqual(sum(m["kind"] == "today" for m in sequence), 1)
        self.assertEqual([m["timestamp"] for m in sequence], sorted(m["timestamp"] for m in sequence))
        self.assertTrue(any(m.get("gap_label") for m in sequence))
        self.assertFalse(any("· ·" in m.get("gap_label", "") for m in sequence))
        from apps.web.django.admin_ops.views import _build_contract_timeline
        market = self.market("locked")
        for reference, expected_index in [(NOW - timedelta(days=100), 0), (NOW + timedelta(days=100), -1)]:
            timed = _build_contract_timeline([market], today=reference)["rows"][0]["time_sequence"]
            self.assertEqual(timed[expected_index]["kind"], "today")
        self.assertEqual({m["label"] for m in row["undated_steps"]}, {"Publicação", "Resolução efetiva", "Selagem"})
        canceled = self.row(self.market("canceled", resolved_at=None, sealed_at=None))
        self.assertTrue(all(m["time_label"] == "Não se aplica" for m in canceled["undated_steps"]))
        coincident = self.row(self.market("sealed", created_at=NOW, published_at=NOW, close_at=NOW,
                              expected_resolution_at=NOW, resolved_at=NOW, sealed_at=NOW, seal_due_at=NOW))
        self.assertTrue(all(m["gap_label"] == "Mesmo instante" for m in coincident["time_sequence"][:-1]))

    def test_duration_controls_extra_spacing_with_stable_query_scale(self):
        from apps.web.django.admin_ops.views import _build_contract_timeline
        market = self.market("locked", created_at=NOW - timedelta(days=21),
                             published_at=NOW - timedelta(days=1),
                             close_at=NOW - timedelta(days=1) + timedelta(hours=1))
        row = self.row(market)
        by_field = {m.get("field"): m for m in row["time_sequence"]}
        long_gap = by_field["created_at"]["gap_extra_px"]
        short_gap = by_field["published_at"]["gap_extra_px"]
        self.assertGreater(long_gap, short_gap)
        self.assertAlmostEqual(long_gap, 480 * short_gap, delta=0.25)
        markets = [self.market(slug=f"duration-{i}", expected_resolution_at=NOW + timedelta(days=i + 1)) for i in range(12)]
        first, _ = self.contract_context(markets)
        more, _ = self.contract_context(markets, "?limit=20")
        self.assertEqual(first["timeline"]["rows"][0]["time_sequence"], more["timeline"]["rows"][0]["time_sequence"])

    def test_scale_includes_actual_sealing_and_planned_due(self):
        from apps.web.django.admin_ops.views import _build_contract_timeline
        m = self.market("sealed", sealed_at=NOW + timedelta(days=3), seal_due_at=NOW + timedelta(days=5))
        timeline = _build_contract_timeline([m], today=NOW, include_terminal=True)
        self.assertIn("22/10/2026", timeline["ends_at_label"])
        self.assertTrue(all(0 <= x["position"] <= 100 for x in timeline["rows"][0]["markers"]))

    def contract_context(self, markets, query=""):
        from django.test import RequestFactory
        from apps.web.django.admin_ops import views
        request = RequestFactory().get("/admin-ops/contracts/" + query)
        request.session = {"auth_api_token": "fixture", "auth_api_user": {"is_staff": True}}
        data = {"markets": markets, "counts": {"locked": len(markets)},
                "schedule_count_scope": "filtered_query_before_temporal_filter",
                "schedule_summary": [{"label": "Apuração prevista", "total": len(markets)}]}
        with patch.object(views, "admin_get_markets", return_value=data) as api, patch.object(views, "render", side_effect=lambda req, template, context: context), patch.object(views.timezone, "now", return_value=NOW):
            context = views.contracts(request)
        return context, api

    def test_load_more_preserves_scale_filter_order_counts_and_history(self):
        markets = [self.market(slug=f"fixture-{i}", expected_resolution_at=NOW + timedelta(days=i + 1)) for i in range(12)]
        for m in markets:
            m.update(original_expected_resolution_label="18/10/2026 17:00 America/Sao_Paulo",
                     schedule_history=[{"reason": "Adiamento <fonte>", "after": {"expected_resolution_at": "2026-11-01T20:00:00Z"}}])
        before = copy.deepcopy(markets)
        query = "?status=locked&q=fixture&temporal=resolution_scheduled&order=created_asc"
        first, api = self.contract_context(markets, query)
        more, _ = self.contract_context(markets, query + "&limit=20")
        api.assert_called_once_with("fixture", status="locked", q="fixture", temporal="resolution_scheduled", order="created_asc", active_contracts=False)
        self.assertEqual(len(first["timeline"]["rows"]), 10)
        self.assertEqual(len(more["timeline"]["rows"]), 12)
        self.assertEqual(first["timeline"]["rows"], more["timeline"]["rows"][:10])
        self.assertEqual(first["timeline"]["ends_at_label"], more["timeline"]["ends_at_label"])
        self.assertEqual(markets, before)
        from django.template.loader import render_to_string
        html = render_to_string("admin_ops/contracts.html", first)
        for text in ("Fechado", "Fechamento programado", "Previsão original e histórico", "Adiamento &lt;fonte&gt;", "etapa sem conclusão confirmada", "10 de 12", "Carregar mais", "Contadores da consulta antes do filtro temporal", "totais do catálogo completo", "contract-time-sequence", "Espaçamento por duração, com mínimo para leitura dos rótulos.", "Fechamento programado", "horário previsto"):
            self.assertIn(text, html)
        self.assertNotIn("phase-state-active", html)
        self.assertNotIn("Agora", html)

    def test_timeline_regions_are_named_for_their_market_before_and_after_load_more(self):
        from html.parser import HTMLParser
        from django.template.loader import render_to_string
        from django.urls import reverse

        class Elements(HTMLParser):
            def __init__(self):
                super().__init__()
                self.tags = []
                self.text = {}
                self.current_id = None

            def handle_starttag(self, tag, attributes):
                attrs = dict(attributes)
                self.tags.append((tag, attrs))
                if attrs.get("id"):
                    self.current_id = attrs["id"]
                    self.text[self.current_id] = ""

            def handle_data(self, data):
                if self.current_id:
                    self.text[self.current_id] += data

            def handle_endtag(self, tag):
                self.current_id = None

        markets = [self.market(slug=f"named-{i}", title=f"Evento {i} & <critério>") for i in range(12)]
        for query, count in (("", 10), ("?limit=20", 12)):
            with self.subTest(query=query):
                context, _ = self.contract_context(markets, query)
                parser = Elements()
                parser.feed(render_to_string("admin_ops/contracts.html", context))
                ids = [attrs["id"] for _, attrs in parser.tags if "id" in attrs]
                self.assertEqual(len(ids), len(set(ids)))
                by_id = {attrs["id"]: attrs for _, attrs in parser.tags if "id" in attrs}
                regions = [attrs for _, attrs in parser.tags if attrs.get("class") == "contract-time-scroll"]
                self.assertEqual(len(regions), count)
                for region, market in zip(regions, markets):
                    label_ids = region["aria-labelledby"].split()
                    self.assertEqual(" ".join(parser.text[identifier] for identifier in label_ids),
                                     "Cronograma " + market["title"])
                    self.assertEqual(by_id[label_ids[-1]]["href"], reverse("admin-ops-market-edit", args=[market["slug"]]))
                    self.assertIn("use as setas", parser.text[region["aria-describedby"]])
                    self.assertEqual(region["tabindex"], "0")

    def test_terminal_render_has_no_pending_resolution_for_canceled_and_explicit_missing_actual_dates(self):
        from django.template.loader import render_to_string
        for status in ("resolved", "sealed", "canceled"):
            context, api = self.contract_context([self.market(status)], "?status=" + status)
            html = render_to_string("admin_ops/contracts.html", context)
            self.assertIn("Histórica", html)
            if status == "canceled":
                self.assertNotIn("Pendente", html)
                self.assertIn("Não se aplica", html)
            else:
                self.assertIn("Resolvido — data não registrada", html)
            self.assertEqual(context["timeline"]["total"], 1)


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
