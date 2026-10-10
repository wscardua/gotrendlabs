"""Consolidate explicitly selected duplicate subcategories without moving markets.

Run as a module inside FastAPI's environment. Dry-run is the default.
"""
import argparse
import json
import os
from pathlib import Path

from apps.api.backend_api.admin_events import record_admin_event
from apps.api.backend_api.db import get_connection


METADATA = ("notice", "is_blocked", "blocked_reason", "blocked_at")


def normalized(name):
    return name.strip().lower()


def consolidate(connection, pairs, *, execute=False, backup_path=None):
    if execute and not backup_path:
        raise ValueError("Execução exige caminho de backup novo.")
    ids = [identifier for pair in pairs for identifier in pair]
    if not pairs or len(ids) != len(set(ids)):
        raise ValueError("Informe pares distintos REMOVE:KEEP, sem IDs repetidos.")
    with connection.transaction(), connection.cursor() as cursor:
        if execute:
            cursor.execute("SET LOCAL lock_timeout = '5s'")
            cursor.execute("LOCK TABLE gotrendlabs_market_categories, gotrendlabs_market_subcategories, gotrendlabs_market_events, gotrendlabs_markets IN SHARE ROW EXCLUSIVE MODE")
        report = {"mode": "execute" if execute else "dry-run", "merges": []}
        for remove_id, keep_id in pairs:
            cursor.execute("SELECT * FROM gotrendlabs_market_subcategories WHERE id IN (%s,%s) ORDER BY id", (remove_id, keep_id))
            rows = {row["id"]: row for row in cursor.fetchall()}
            if set(rows) != {remove_id, keep_id}:
                raise ValueError("Subcategoria ausente; refaça o inventário.")
            source, target = rows[remove_id], rows[keep_id]
            if source["category_id"] != target["category_id"] or normalized(source["name"]) != normalized(target["name"]):
                raise ValueError("Os registros não são duplicados no mesmo pai.")
            if any(source[field] != target[field] for field in METADATA):
                raise ValueError("Avisos ou bloqueios divergentes exigem análise manual.")
            cursor.execute("SELECT * FROM gotrendlabs_market_events WHERE subcategory_id IN (%s,%s) ORDER BY id", (remove_id, keep_id))
            events = cursor.fetchall()
            cursor.execute("SELECT id FROM gotrendlabs_markets WHERE subcategory_id=%s OR event_id IN (SELECT id FROM gotrendlabs_market_events WHERE subcategory_id=%s) LIMIT 1", (remove_id, remove_id))
            if cursor.fetchone():
                raise ValueError("Subcategoria ou evento de origem possui mercado; IDs de mercados não podem ser alterados.")
            targets = [row for row in events if row["subcategory_id"] == keep_id]
            actions = []
            for event in [row for row in events if row["subcategory_id"] == remove_id]:
                matches = [row for row in targets if normalized(row["name"]) == normalized(event["name"])]
                if len(matches) > 1:
                    raise ValueError("Eventos de destino ambíguos.")
                if matches:
                    if any(event[field] != matches[0][field] for field in METADATA):
                        raise ValueError("Metadados dos eventos divergentes.")
                    actions.append({"action": "delete", "event_id": event["id"], "keep_event_id": matches[0]["id"]})
                else:
                    if any(row["slug"] == event["slug"] for row in targets):
                        raise ValueError("Slug de evento em conflito no destino.")
                    actions.append({"action": "move", "event_id": event["id"]})
                    targets.append(event)
            report["merges"].append({"remove_id": remove_id, "keep_id": keep_id, "subcategories_before": list(rows.values()), "events_before": events, "actions": actions})
        if not execute:
            return report
        # Exclusive creation and fsync ensure a persisted preimage before deleting.
        with Path(backup_path).open("x", encoding="utf-8") as backup:
            os.chmod(backup_path, 0o600)
            json.dump(report, backup, default=str, ensure_ascii=False, indent=2)
            backup.flush()
            os.fsync(backup.fileno())
        for merge in report["merges"]:
            for action in merge["actions"]:
                if action["action"] == "delete":
                    cursor.execute("DELETE FROM gotrendlabs_market_events WHERE id=%s", (action["event_id"],))
                else:
                    cursor.execute("UPDATE gotrendlabs_market_events SET subcategory_id=%s WHERE id=%s", (merge["keep_id"], action["event_id"]))
            cursor.execute("DELETE FROM gotrendlabs_market_subcategories WHERE id=%s", (merge["remove_id"],))
            record_admin_event(cursor, None, "taxonomy.deduplicate", "subcategory", str(merge["remove_id"]), json.dumps(merge, default=str, ensure_ascii=False))
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--merge", action="append", required=True, metavar="REMOVE:KEEP")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--backup")
    args = parser.parse_args()
    pairs = [tuple(int(value) for value in pair.split(":")) for pair in args.merge]
    if any(len(pair) != 2 for pair in pairs):
        parser.error("Cada --merge deve conter REMOVE:KEEP.")
    with get_connection() as connection:
        report = consolidate(connection, pairs, execute=args.execute, backup_path=args.backup)
    print(json.dumps(report, default=str, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
