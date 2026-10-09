import contextlib
import io
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from ops.deploy.mcp.configure_environment import ADAPTER, COMMON, configure, load, main


class MCPDeployEnvironmentTests(unittest.TestCase):
    def test_first_install_is_disabled_private_and_adapter_has_no_inherited_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.dict('os.environ', {'POSTGRES_PASSWORD': 'private-fixture', 'GOTRENDLABS_PASSWORD_PEPPER': 'private-fixture'}):
                self.assertEqual(configure(root), '0')
            api = load(root / '.env.mcp-api.prod', COMMON)
            adapter = load(root / '.env.mcp.prod', ADAPTER)
            self.assertEqual(set(api), COMMON)
            self.assertEqual(set(adapter), ADAPTER)
            self.assertEqual(api['GTL_MCP_WORKLOAD_SECRET'], adapter['GTL_MCP_WORKLOAD_SECRET'])
            self.assertGreaterEqual(len(api['GTL_MCP_WORKLOAD_SECRET']), 32)
            self.assertEqual(api['GTL_MCP_RESOURCE'], 'https://gotrendlabs.com.br/mcp')
            for name in ('.env.mcp.prod', '.env.mcp-api.prod'):
                self.assertEqual(stat.S_IMODE((root / name).stat().st_mode), 0o600)

    def test_enable_rollback_and_redeploy_preserve_workload(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            configure(root)
            secret = load(root / '.env.mcp-api.prod', COMMON)['GTL_MCP_WORKLOAD_SECRET']
            self.assertEqual(configure(root, enabled='1'), '1')
            self.assertEqual(configure(root), '1')
            self.assertEqual(configure(root, enabled='0'), '0')
            self.assertEqual(load(root / '.env.mcp.prod', ADAPTER)['GTL_MCP_WORKLOAD_SECRET'], secret)

    def test_mismatched_existing_workloads_fail_without_rewriting_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            configure(root)
            adapter = root / '.env.mcp.prod'
            secret = load(adapter, ADAPTER)['GTL_MCP_WORKLOAD_SECRET']
            adapter.write_text(adapter.read_text().replace(secret, 'x' * 48))
            before = [(root / name).read_bytes() for name in ('.env.mcp.prod', '.env.mcp-api.prod')]
            with self.assertRaises(ValueError):
                configure(root, enabled='1')
            self.assertEqual(before, [(root / name).read_bytes() for name in ('.env.mcp.prod', '.env.mcp-api.prod')])

    def test_insecure_origin_and_symlink_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                configure(root, issuer='http://localhost:8000')
            target = root / 'unrelated'
            target.write_text('preserve')
            (root / '.env.mcp.prod').symlink_to(target)
            with self.assertRaises(ValueError):
                configure(root)
            self.assertEqual(target.read_text(), 'preserve')

    def test_cli_never_discloses_secret(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = io.StringIO()
            with patch('sys.argv', ['configure_environment.py', '--app-dir', directory]), contextlib.redirect_stdout(output):
                main()
            secret = load(root / '.env.mcp.prod', ADAPTER)['GTL_MCP_WORKLOAD_SECRET']
            self.assertNotIn(secret, output.getvalue())
            self.assertIn('enabled=0', output.getvalue())


class MCPDeployWindowTests(unittest.TestCase):
    def run_deploy(self, fail_migration=False, thumbnails=False):
        import json
        import os
        import shutil
        import subprocess
        import sys

        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / '.git').mkdir()
            (root / 'ops/deploy/production').mkdir(parents=True)
            (root / 'ops/deploy/mcp').mkdir(parents=True)
            (root / 'ops/deploy/production/docker-compose.yml').touch()
            shutil.copy(repository / 'ops/deploy/mcp/configure_environment.py', root / 'ops/deploy/mcp/configure_environment.py')
            for name, content in {
                '.env.prod': '',
                '.env.auth.prod': 'GOTRENDLABS_TOTP_ENCRYPTION_KEY=fixture\n',
                '.env.fastapi-db.prod': 'FASTAPI_POSTGRES_USER=fixture\nFASTAPI_POSTGRES_PASSWORD=fixture\n',
                '.env.migrate.prod': '',
            }.items():
                (root / name).write_text(content)
            if thumbnails:
                (root / '.env.thumbnails.prod').write_text('AWS_BEARER_TOKEN_BEDROCK=fixture\n')
            binaries = root / 'bin'
            binaries.mkdir()
            state = root / 'mock-state.json'
            state.write_text(json.dumps({'writers_running': True, 'migrated': False, 'restarted': False, 'commands': [], 'media_ready': False}))
            mock = '''import json, os, sys
from pathlib import Path
if Path(sys.argv[0]).name == 'git':
    sys.exit(0)
path = Path(os.environ['DEPLOY_MOCK_STATE'])
state = json.loads(path.read_text())
args = sys.argv[1:]
state['commands'].append(args)
if 'migrate' in args and any('p.mkdir(' in arg for arg in args):
    state['media_ready'] = True
if 'fastapi' in args and 'run' in args and not state['media_ready']:
    sys.exit(93)
if 'stop' in args:
    state['writers_running'] = False
if 'migrate' in args and any('ops.scripts.' in arg for arg in args):
    if state['writers_running']:
        sys.exit(91)
    if 'ops.scripts.migrate_with_role' in args:
        if os.environ['DEPLOY_MOCK_FAIL'] == '1':
            sys.exit(19)
        state['migrated'] = True
if 'up' in args:
    if not state['migrated']:
        sys.exit(92)
    state['writers_running'] = True
    state['restarted'] = True
path.write_text(json.dumps(state))
'''
            for name in ('git', 'docker'):
                binary = binaries / name
                binary.write_text(f'#!{sys.executable}\n' + mock)
                binary.chmod(0o700)
            result = subprocess.run(
                ['bash', str(repository / 'ops/deploy/production/deploy.sh')],
                env={**os.environ, 'APP_DIR': str(root), 'PATH': str(binaries) + os.pathsep + os.environ['PATH'],
                     'DEPLOY_MOCK_STATE': str(state), 'DEPLOY_MOCK_FAIL': '1' if fail_migration else '0'},
                capture_output=True, text=True, timeout=30,
            )
            return result.returncode, json.loads(state.read_text())

    def test_writers_stop_during_migration_and_restart_after_success(self):
        code, state = self.run_deploy()
        self.assertEqual(code, 0)
        self.assertTrue(state['migrated'])
        self.assertTrue(state['restarted'])
        self.assertTrue(state['writers_running'])

    def test_migration_failure_keeps_writers_stopped_for_explicit_recovery(self):
        code, state = self.run_deploy(fail_migration=True)
        self.assertEqual(code, 19)
        self.assertFalse(state['migrated'])
        self.assertFalse(state['restarted'])
        self.assertFalse(state['writers_running'])

    def test_installed_thumbnail_worker_is_built_stopped_and_redeployed(self):
        code, state = self.run_deploy(thumbnails=True)
        self.assertEqual(code, 0)
        self.assertTrue(state['media_ready'])
        for command in state['commands']:
            self.assertIn('thumbnails', command)
        stop = next(command for command in state['commands'] if 'stop' in command)
        self.assertIn('thumbnail-worker', stop)
        self.assertTrue(state['restarted'])

    def test_thumbnail_migration_failure_never_restarts_executor(self):
        code, state = self.run_deploy(fail_migration=True, thumbnails=True)
        self.assertEqual(code, 19)
        stop = next(command for command in state['commands'] if 'stop' in command)
        self.assertIn('thumbnail-worker', stop)
        self.assertFalse(state['restarted'])
        self.assertFalse(state['writers_running'])

    def test_unconfigured_install_does_not_require_thumbnail_secret_or_worker(self):
        code, state = self.run_deploy()
        self.assertEqual(code, 0)
        for command in state['commands']:
            self.assertNotIn('thumbnails', command)
            self.assertNotIn('thumbnail-worker', command)
        self.assertTrue(state['media_ready'])
