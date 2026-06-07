#!/usr/bin/env python
import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = REPO_ROOT / "packages" / "contracts" / "openapi" / "gotrendlabs-api.json"


def render_openapi():
    sys.path.insert(0, str(REPO_ROOT))
    from apps.api.backend_api.main import app

    return json.dumps(app.openapi(), ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Export or validate the versioned GoTrendLabs FastAPI OpenAPI snapshot.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Snapshot path to write or check.")
    parser.add_argument("--check", action="store_true", help="Fail if the snapshot differs from the current FastAPI schema.")
    args = parser.parse_args()

    output_path = Path(args.output)
    rendered = render_openapi()

    if args.check:
        if not output_path.exists():
            print(f"OpenAPI snapshot missing: {output_path}", file=sys.stderr)
            return 1
        current = output_path.read_text(encoding="utf-8")
        if current != rendered:
            print(f"OpenAPI snapshot is out of date: {output_path}", file=sys.stderr)
            print("Run: python packages/contracts/export_openapi.py", file=sys.stderr)
            return 1
        print(f"OpenAPI snapshot is up to date: {output_path}")
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"OpenAPI snapshot written: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
