"""The editorial schema must load inside the MCP image without API runtime."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import TestCase


class IsolatedMCPContractTests(TestCase):
    def test_schema_imports_with_only_the_files_packaged_for_mcp(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'apps/api/backend_api'
            target.mkdir(parents=True)
            for name in ('editorial_schemas.py', 'resolution_schedule_contract.py'):
                shutil.copyfile(root / 'apps/api/backend_api' / name, target / name)
            script = '''import sys
sys.path.insert(0, sys.argv[1])
from apps.api.backend_api.editorial_schemas import Draft
from apps.api.backend_api.resolution_schedule_contract import ScheduleFields
assert 'expected_resolution_at' in Draft.model_json_schema()['properties']
ScheduleFields(expected_resolution_at='2026-10-20T12:00:00-03:00', schedule_timezone='America/Sao_Paulo')
assert not any(name in sys.modules for name in ('fastapi', 'django', 'psycopg', 'apps.api.backend_api.resolution_schedule'))
'''
            process = subprocess.run([sys.executable, '-I', '-c', script, directory], capture_output=True, text=True, timeout=30)
            self.assertEqual(process.returncode, 0, process.stderr)
