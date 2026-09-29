"""Validate and atomically install a licensed GeoLite City archive or MMDB."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import shutil
import tarfile
import tempfile

from apps.api.backend_api.db import get_connection


def _record_run(started_at, status, *, metadata=None, error_code=None):
    metadata = metadata or {}
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO gotrendlabs_geolite_load_runs
                  (started_at, completed_at, status, database_build_at, database_type,
                   file_size_bytes, node_count, error_code)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (started_at, datetime.now(timezone.utc), status,
                  metadata.get("database_build_at"), metadata.get("database_type"),
                  metadata.get("file_size_bytes"), metadata.get("node_count"), error_code))


def _verify_checksum(source, checksum_file):
    if not checksum_file:
        return
    expected = Path(checksum_file).read_text().split()[0].lower()
    if len(expected) != 64 or any(char not in "0123456789abcdef" for char in expected):
        raise ValueError("Checksum inválido")
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected:
        raise ValueError("Checksum divergente")


def _copy_database(source, target):
    if source.name.endswith(".mmdb"):
        with source.open("rb") as stream, target.open("wb") as output:
            shutil.copyfileobj(stream, output)
        return
    with tarfile.open(source, "r:gz") as archive:
        members = [member for member in archive.getmembers()
                   if member.isfile() and Path(member.name).name == "GeoLite2-City.mmdb"]
        if len(members) != 1 or members[0].size > 200 * 1024 * 1024:
            raise ValueError("Arquivo GeoLite City inválido")
        stream = archive.extractfile(members[0])
        if stream is None:
            raise ValueError("Base GeoLite ausente no arquivo")
        with stream, target.open("wb") as output:
            shutil.copyfileobj(stream, output)


def install(source_path, destination_path, *, checksum_file=None):
    """Install one local source and persist the outcome; never expose license keys."""
    started_at = datetime.now(timezone.utc)
    temporary = None
    try:
        source = Path(source_path)
        destination = Path(destination_path)
        if not source.is_file() or not destination_path:
            raise ValueError("Fonte ou destino ausente")
        _verify_checksum(source, checksum_file)
        destination.parent.mkdir(parents=True, exist_ok=True)
        descriptor, name = tempfile.mkstemp(prefix=".geolite-", suffix=".mmdb", dir=str(destination.parent))
        os.close(descriptor)
        temporary = Path(name)
        _copy_database(source, temporary)

        import geoip2.database
        with geoip2.database.Reader(str(temporary)) as reader:
            database = reader.metadata()
            if "City" not in database.database_type:
                raise ValueError("Base não é GeoLite City")
            metadata = {"database_build_at": datetime.fromtimestamp(database.build_epoch, timezone.utc),
                        "database_type": database.database_type,
                        "file_size_bytes": temporary.stat().st_size,
                        "node_count": database.node_count}
        os.chmod(temporary, 0o644)
        os.replace(str(temporary), str(destination))
        temporary = None
        _record_run(started_at, "success", metadata=metadata)
        return metadata
    except Exception as exc:
        _record_run(started_at, "failed", error_code=type(exc).__name__)
        raise
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Instala GeoLite City local e registra a execução no Analytics.")
    parser.add_argument("--source", required=True, help="Arquivo .tar.gz ou .mmdb local")
    parser.add_argument("--sha256", help="Arquivo de checksum SHA256 opcional")
    parser.add_argument("--env-file", help="Arquivo de ambiente da FastAPI")
    args = parser.parse_args()
    if args.env_file:
        from dotenv import load_dotenv
        load_dotenv(args.env_file, override=False)
    destination = os.environ.get("GOTRENDLABS_GEOLITE_CITY_PATH", "")
    if not destination:
        parser.error("GOTRENDLABS_GEOLITE_CITY_PATH não configurado")
    result = install(args.source, destination, checksum_file=args.sha256)
    print(f"GeoLite City instalada: {result['database_build_at'].isoformat()}, "
          f"{result['file_size_bytes']} bytes, {result['node_count']} nós")


if __name__ == "__main__":
    main()
