"""Pack engine: bundles of font + wallpaper + icons + colors + sounds +
boot animation, with preview/install/restore/validation/versioning."""

from __future__ import annotations

import json
from pathlib import Path

PACK_SCHEMA_VERSION = 1
REQUIRED_FIELDS = {"name", "version"}
COMPONENT_FIELDS = {"font", "wallpaper", "icons", "colors", "sounds", "bootAnimation"}


class PackError(ValueError):
    pass


def create_pack(packs_root: Path, name: str, version: str = "0.1.0", **components) -> Path:
    if not name or not name.strip():
        raise PackError("Pack name must not be empty")
    unknown = set(components) - COMPONENT_FIELDS
    if unknown:
        raise PackError(f"Unknown pack components: {sorted(unknown)}")

    pack_dir = packs_root / name
    pack_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schemaVersion": PACK_SCHEMA_VERSION,
        "name": name,
        "version": version,
        "components": components,
    }
    validate_pack(manifest)

    manifest_path = pack_dir / "pack.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def validate_pack(manifest: dict) -> None:
    missing = REQUIRED_FIELDS - manifest.keys()
    if missing:
        raise PackError(f"Pack manifest missing required fields: {sorted(missing)}")
    if "components" not in manifest or not isinstance(manifest["components"], dict):
        raise PackError("Pack manifest must have a 'components' object")
    if not manifest["components"]:
        raise PackError("Pack must declare at least one component")


def load_pack(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_pack(manifest)
    return manifest
