"""Prepare isolated MCP host files; never print workload secrets or read shared env."""
import argparse
import fcntl
import os
from pathlib import Path
import secrets
import tempfile
from urllib.parse import urlsplit

COMMON = {"GTL_MCP_ENABLED", "GTL_MCP_ISSUER", "GTL_MCP_RESOURCE", "GTL_MCP_WORKLOAD_SECRET"}
ADAPTER = COMMON | {"GTL_MCP_API_URL", "GTL_MCP_SPOOL"}


def load(path, allowed):
    if not path.exists():
        return {}
    if path.is_symlink():
        raise ValueError("MCP configuration must not be a symlink")
    result = {}
    for line in path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator or key not in allowed or key in result:
            raise ValueError("Unexpected MCP configuration entry")
        result[key] = value
    return result


def write_private(path, values):
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".")
    try:
        with os.fdopen(descriptor, "w") as output:
            output.write("".join(f"{key}={value}\n" for key, value in values.items()))
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def configure(app_dir, issuer="https://gotrendlabs.com.br", enabled=None):
    parsed = urlsplit(issuer)
    if (parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password
            or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
        raise ValueError("Production MCP issuer must be an HTTPS origin")
    issuer = issuer.rstrip("/")
    app_dir = Path(app_dir)
    app_dir.mkdir(parents=True, exist_ok=True)
    # Serialize deploy/enable operations. The lock contains no secrets.
    lock_path = app_dir / ".mcp-config.lock"
    if lock_path.is_symlink():
        raise ValueError("MCP lock must not be a symlink")
    with lock_path.open("a") as lock:
        os.chmod(lock_path, 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)
        api_path, adapter_path = app_dir / ".env.mcp-api.prod", app_dir / ".env.mcp.prod"
        previous = [load(api_path, COMMON), load(adapter_path, ADAPTER)]
        workloads = {item["GTL_MCP_WORKLOAD_SECRET"] for item in previous if item.get("GTL_MCP_WORKLOAD_SECRET")}
        states = {item["GTL_MCP_ENABLED"] for item in previous if item.get("GTL_MCP_ENABLED") is not None}
        if len(workloads) > 1 or any(len(value) < 32 for value in workloads):
            raise ValueError("MCP workload files disagree or contain an invalid secret")
        if len(states) > 1 or states - {"0", "1"} or enabled not in (None, "0", "1"):
            raise ValueError("MCP enable states disagree or are invalid")
        workload = next(iter(workloads)) if workloads else secrets.token_urlsafe(48)
        common = {
            "GTL_MCP_ENABLED": enabled if enabled is not None else next(iter(states), "0"),
            "GTL_MCP_ISSUER": issuer,
            "GTL_MCP_RESOURCE": issuer + "/mcp",
            "GTL_MCP_WORKLOAD_SECRET": workload,
        }
        write_private(api_path, common)
        write_private(adapter_path, {**common, "GTL_MCP_API_URL": "http://fastapi:8001", "GTL_MCP_SPOOL": "/spool"})
    return common["GTL_MCP_ENABLED"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-dir", default="/opt/gotrendlabs", type=Path)
    parser.add_argument("--issuer", default="https://gotrendlabs.com.br")
    parser.add_argument("--enabled", choices=("0", "1"))
    args = parser.parse_args()
    try:
        state = configure(args.app_dir, args.issuer, args.enabled)
    except (OSError, ValueError):
        parser.exit(1, "Unable to prepare MCP files; check permissions and configuration consistency.\n")
    print(f"MCP files ready (0600); enabled={state}; workload preserved/generated without disclosure.")


if __name__ == "__main__":
    main()
