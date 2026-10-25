"""Permission regression for production's broad default ACL on new tables."""

from importlib import import_module
from unittest.mock import patch

from django.db import connection
from django.test import TestCase


class ResolutionReceiptPrivilegeTests(TestCase):
    def test_migration_removes_broad_runtime_access_but_preserves_receipt_writer(self):
        if connection.vendor != "postgresql":
            self.skipTest("PostgreSQL roles required")
        writer = "gtl_receipt_acl_test"
        table = "gotrendlabs_market_resolution_requests"
        sequence = "gotrendlabs_market_resolution_requests_id_seq"
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE ROLE {writer} NOLOGIN")
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname='gotrendlabs_django'")
            if not cursor.fetchone():
                cursor.execute("CREATE ROLE gotrendlabs_django NOLOGIN")
            for role in (writer, "gotrendlabs_django"):
                cursor.execute(f"GRANT ALL PRIVILEGES ON TABLE {table} TO {role}")
                cursor.execute(f"GRANT ALL PRIVILEGES ON SEQUENCE {sequence} TO {role}")

        migration = import_module("apps.web.django.markets.migrations.0038_limit_resolution_request_privileges")
        with patch.dict("os.environ", {"FASTAPI_POSTGRES_USER": writer}):
            with connection.schema_editor() as schema_editor:
                migration.limit_receipt_privileges(None, schema_editor)

        with connection.cursor() as cursor:
            for role, expected in (
                (writer, (True, True, False, False, True, False)),
                ("gotrendlabs_django", (True, False, False, False, False, False)),
            ):
                cursor.execute(
                    f"""SELECT has_table_privilege(%s, '{table}', 'SELECT'),
                               has_table_privilege(%s, '{table}', 'INSERT'),
                               has_table_privilege(%s, '{table}', 'UPDATE'),
                               has_table_privilege(%s, '{table}', 'DELETE'),
                               has_sequence_privilege(%s, '{sequence}', 'USAGE'),
                               has_sequence_privilege(%s, '{sequence}', 'UPDATE')""",
                    (role,) * 6,
                )
                self.assertEqual(cursor.fetchone(), expected, role)
