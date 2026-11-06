import subprocess
import tempfile
import unittest
from pathlib import Path

from ops.scripts.check_android_release_source import ReleaseSourceError, validate_release_source


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


class AndroidReleaseSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.repo = root / "repo"
        self.remote = root / "origin.git"
        self.repo.mkdir()
        git(root, "init", "--bare", "--initial-branch=main", str(self.remote))
        git(self.repo, "init", "--initial-branch=main")
        git(self.repo, "config", "user.email", "release-test@example.test")
        git(self.repo, "config", "user.name", "Release Test")
        git(self.repo, "config", "commit.gpgsign", "false")
        git(self.repo, "remote", "add", "origin", str(self.remote))
        (self.repo / "source.txt").write_text("integrated source")
        self.commit("initial")
        git(self.repo, "push", "-u", "origin", "main")

    def commit(self, message):
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", message)

    def test_clean_current_main_is_accepted(self):
        self.assertEqual(validate_release_source(self.repo), git(self.repo, "rev-parse", "HEAD"))

    def test_detached_checkout_of_current_main_is_accepted(self):
        git(self.repo, "checkout", "--detach")
        self.assertEqual(validate_release_source(self.repo), git(self.repo, "rev-parse", "HEAD"))

    def test_modified_or_staged_source_is_rejected(self):
        (self.repo / "source.txt").write_text("local fix")
        with self.assertRaisesRegex(ReleaseSourceError, "não commitadas"):
            validate_release_source(self.repo)
        git(self.repo, "add", "source.txt")
        with self.assertRaisesRegex(ReleaseSourceError, "não commitadas"):
            validate_release_source(self.repo)

    def test_untracked_implementation_is_rejected(self):
        (self.repo / "new_feature.dart").write_text("local feature")
        with self.assertRaisesRegex(ReleaseSourceError, "não rastreados"):
            validate_release_source(self.repo)

    def test_committed_but_unmerged_fix_is_rejected(self):
        git(self.repo, "checkout", "-b", "fix/local")
        (self.repo / "source.txt").write_text("committed fix")
        self.commit("fix")
        with self.assertRaisesRegex(ReleaseSourceError, "HEAD não é"):
            validate_release_source(self.repo)

    def test_fetch_detects_main_advanced_elsewhere(self):
        publisher = self.repo.parent / "publisher"
        git(self.repo.parent, "clone", str(self.remote), str(publisher))
        git(publisher, "config", "user.email", "release-test@example.test")
        git(publisher, "config", "user.name", "Release Test")
        git(publisher, "config", "commit.gpgsign", "false")
        (publisher / "source.txt").write_text("new main")
        git(publisher, "add", ".")
        git(publisher, "commit", "-m", "new main")
        git(publisher, "push", "origin", "main")
        with self.assertRaisesRegex(ReleaseSourceError, "HEAD não é"):
            validate_release_source(self.repo)
        self.assertNotEqual(git(self.repo, "rev-parse", "origin/main"), git(self.repo, "rev-parse", "HEAD"))

    def test_fetch_failure_cannot_reuse_stale_reference(self):
        git(self.repo, "remote", "set-url", "origin", str(self.repo.parent / "missing"))
        with self.assertRaisesRegex(ReleaseSourceError, "atualizar origin/main"):
            validate_release_source(self.repo)
