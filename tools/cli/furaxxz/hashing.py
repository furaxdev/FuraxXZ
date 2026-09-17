"""SHA-256 hashing and manifest/backup helpers."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Compute the SHA-256 hex digest of a file, streaming it in chunks."""
    if not path.is_file():
        raise FileNotFoundError(f"Not a file: {path}")
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def write_checksums(root: Path, files: Iterable[Path], out_path: Path) -> Path:
    """Write a `checksums.sha256` file (sha256sum-compatible format)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for f in sorted(files):
        digest = sha256_file(f)
        rel = os.path.relpath(f, root)
        lines.append(f"{digest}  {rel}")
    out_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return out_path


def verify_checksums(root: Path, checksums_path: Path) -> dict:
    """Verify files listed in a checksums.sha256 file against `root`.

    Returns {"ok": [...], "failed": [...], "missing": [...]}.
    """
    ok, failed, missing = [], [], []
    for raw_line in checksums_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        digest, _, rel = line.partition("  ")
        target = root / rel
        if not target.exists():
            missing.append(rel)
            continue
        actual = sha256_file(target)
        (ok if actual == digest else failed).append(rel)
    return {"ok": ok, "failed": failed, "missing": missing}


def build_manifest(device_profile: dict, components: list[dict]) -> dict:
    """Build a backup/report manifest with timestamp + device context."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "device": device_profile.get("device"),
        "manufacturer": device_profile.get("manufacturer"),
        "model": device_profile.get("model"),
        "android": device_profile.get("android"),
        "build": device_profile.get("build"),
        "components": components,
    }


def write_manifest(manifest: dict, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=False), encoding="utf-8")
    return out_path
