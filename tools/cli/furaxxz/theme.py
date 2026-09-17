"""Theme engine: create and validate FuraxXZ theme manifests.

A theme manifest is a versioned JSON document (schema below). This module
only manages the manifest + directory layout — it does not modify a live
device.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

THEME_SCHEMA_VERSION = 1

REQUIRED_FIELDS = {"name", "version", "colors"}
OPTIONAL_FIELDS = {"wallpaper", "icons", "font", "sounds", "animations", "author", "description"}

HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


class ThemeError(ValueError):
    pass


def create_theme(themes_root: Path, name: str, colors: dict, **optional) -> Path:
    if not name or not name.strip():
        raise ThemeError("Theme name must not be empty")
    unknown = set(optional) - OPTIONAL_FIELDS
    if unknown:
        raise ThemeError(f"Unknown theme fields: {sorted(unknown)}")

    theme_dir = themes_root / name
    theme_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schemaVersion": THEME_SCHEMA_VERSION,
        "name": name,
        "version": "0.1.0",
        "colors": colors,
        **optional,
    }
    validate_theme(manifest)

    manifest_path = theme_dir / "theme.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def validate_theme(manifest: dict) -> None:
    missing = REQUIRED_FIELDS - manifest.keys()
    if missing:
        raise ThemeError(f"Theme manifest missing required fields: {sorted(missing)}")
    if not isinstance(manifest["colors"], dict) or not manifest["colors"]:
        raise ThemeError("Theme 'colors' must be a non-empty object")
    for key, value in manifest["colors"].items():
        if not isinstance(value, str) or not HEX_COLOR.match(value):
            raise ThemeError(f"Color '{key}' must be a hex string like '#RRGGBB', got {value!r}")


def load_theme(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_theme(manifest)
    return manifest
