"""Require a clean checkout of the latest remote main for Android distribution."""

from pathlib import Path
import subprocess
import sys


class ReleaseSourceError(RuntimeError):
    pass


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise ReleaseSourceError(
            "Não foi possível verificar/atualizar origin/main. Confira o acesso Git ao remoto."
        )
    return result.stdout.strip()


def validate_release_source(repo: Path) -> str:
    # Fetch failures are fatal: an old local remote reference is not release evidence.
    _git(repo, "fetch", "origin", "main")
    changes = _git(repo, "status", "--porcelain", "--untracked-files=all", "--ignore-submodules=none")
    if changes:
        raise ReleaseSourceError(
            "Release bloqueada: há alterações não commitadas ou arquivos não rastreados. "
            "Preserve o trabalho, faça commit e integre a mudança à main. "
            "Use build debug para validação local."
        )
    head = _git(repo, "rev-parse", "HEAD")
    remote_main = _git(repo, "rev-parse", "refs/remotes/origin/main")
    if head != remote_main:
        raise ReleaseSourceError(
            "Release bloqueada: HEAD não é o commit atual de origin/main. "
            "Integre a mudança e use um checkout limpo da main atualizada. "
            "Use build debug para validação local."
        )
    return head


def main() -> int:
    try:
        revision = validate_release_source(Path(__file__).resolve().parents[2])
    except ReleaseSourceError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"Android release source: {revision} (origin/main atualizado, checkout limpo)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
