"""Backup manifest create/restore, hashed and versioned."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .device import TARGET_DEVICE
from .hashing import build_manifest, sha256_file, write_manifest

MANIFEST_NAME = "manifest.json"


class BackupError(ValueError):
    pass


def create_backup(sources: list[Path], backup_dir: Path) -> Path:
    """Copy `sources` into `backup_dir/files/` and write a hashed manifest."""
    if not sources:
        raise BackupError("No source files given for backup")

    backup_dir.mkdir(parents=True, exist_ok=True)
    files_dir = backup_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    components = []
    for src in sources:
        if not src.is_file():
            raise BackupError(f"Backup source not found: {src}")
        dest = files_dir / src.name
        shutil.copy2(src, dest)
        components.append({
            "name": src.name,
            "originalPath": str(src),
            "sha256": sha256_file(dest),
            "sizeBytes": dest.stat().st_size,
        })

    manifest = build_manifest(TARGET_DEVICE.as_dict(), components)
    write_manifest(manifest, backup_dir / MANIFEST_NAME)
    return backup_dir / MANIFEST_NAME


def restore_backup(backup_dir: Path, dest_dir: Path) -> list[str]:
    """Restore files from a backup, verifying each against its recorded hash
    before copying it out. Raises BackupError on any hash mismatch."""
    manifest_path = backup_dir / MANIFEST_NAME
    if not manifest_path.is_file():
        raise BackupError(f"No manifest found at {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files_dir = backup_dir / "files"
    dest_dir.mkdir(parents=True, exist_ok=True)

    restored = []
    for component in manifest.get("components", []):
        name = component["name"]
        src = files_dir / name
        if not src.is_file():
            raise BackupError(f"Backup file missing: {src}")
        actual_hash = sha256_file(src)
        if actual_hash != component["sha256"]:
            raise BackupError(
                f"Hash mismatch for '{name}': backup is corrupted "
                f"(expected {component['sha256']}, got {actual_hash})"
            )
        dest = dest_dir / name
        shutil.copy2(src, dest)
        restored.append(name)

    return restored
