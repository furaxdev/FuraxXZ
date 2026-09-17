"""Offline system modification lab.

Everything here reads from wherever the user points it, but every write
goes under `lab/` — never into `firmware/`, never onto a real device.
A lab session has three stages, each hashed and never silently rewritten:

    lab/original/<session>/tree/   pristine snapshot, immutable after init
    lab/modified/<session>/tree/   working copy, changed only through apply()
    lab/rebuilt/<session>/         packaged output of build()
    lab/reports/<session>/         report.json for the session

Nothing produced here is flashable. `build()` writes a plain ZIP archive
of the modified tree — not a partition image, not signed, not something
any flashing tool would accept. See docs/FLASHING.md and
docs/MODIFICATIONS.md: real partition repacking remains BLOCKED.
"""

from __future__ import annotations

import json
import shutil
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .device import TARGET_DEVICE
from .hashing import sha256_file

OPERATIONS_FILE = "operations.json"
CHECKSUMS_FILE = "checksums.sha256"
REPORT_FILE = "report.json"


class LabError(ValueError):
    pass


@dataclass
class LabSession:
    session_id: str
    lab_root: Path

    @property
    def original_tree(self) -> Path:
        return self.lab_root / "original" / self.session_id / "tree"

    @property
    def original_checksums(self) -> Path:
        return self.lab_root / "original" / self.session_id / CHECKSUMS_FILE

    @property
    def modified_tree(self) -> Path:
        return self.lab_root / "modified" / self.session_id / "tree"

    @property
    def operations_path(self) -> Path:
        return self.lab_root / "modified" / self.session_id / OPERATIONS_FILE

    @property
    def rebuilt_dir(self) -> Path:
        return self.lab_root / "rebuilt" / self.session_id

    @property
    def report_dir(self) -> Path:
        return self.lab_root / "reports" / self.session_id

    def exists(self) -> bool:
        return self.original_tree.is_dir()

    def load_operations(self) -> list[dict]:
        if not self.operations_path.is_file():
            return []
        return json.loads(self.operations_path.read_text(encoding="utf-8"))

    def save_operations(self, ops: list[dict]) -> None:
        self.operations_path.write_text(json.dumps(ops, indent=2), encoding="utf-8")


def _tree_manifest(root: Path) -> dict[str, str]:
    """Map of relative path -> sha256 for every file under `root`."""
    manifest = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            manifest[rel] = sha256_file(path)
    return manifest


def _resolve_within(root: Path, rel_path: str) -> Path:
    """Resolve `rel_path` under `root`, refusing any path traversal."""
    if not rel_path or rel_path.startswith(("/", "\\")):
        raise LabError(f"Invalid relative path: {rel_path!r}")
    target = (root / rel_path).resolve()
    if not str(target).startswith(str(root.resolve()) + "/") and target != root.resolve():
        raise LabError(f"Refusing path outside the lab tree: {rel_path!r}")
    return target


def init_session(lab_root: Path, source_dir: Path, session_id: str) -> LabSession:
    """Snapshot `source_dir` into a new lab session. Refuses to overwrite
    an existing session (original/ is meant to be immutable)."""
    if not source_dir.is_dir():
        raise LabError(f"Source is not a directory: {source_dir}")

    session = LabSession(session_id=session_id, lab_root=lab_root)
    if session.exists():
        raise LabError(f"Session '{session_id}' already exists (original/ is immutable)")

    shutil.copytree(source_dir, session.original_tree)
    manifest = _tree_manifest(session.original_tree)
    session.original_checksums.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{digest}  {rel}" for rel, digest in sorted(manifest.items())]
    session.original_checksums.write_text(
        "\n".join(lines) + ("\n" if lines else ""), encoding="utf-8"
    )

    shutil.copytree(session.original_tree, session.modified_tree)
    session.save_operations([])

    return session


@dataclass
class ApplyResult:
    operation: dict
    sha256_before: str | None
    sha256_after: str | None


def apply_operation(
    session: LabSession, op_type: str, rel_path: str, source_file: Path | None = None
) -> ApplyResult:
    if not session.exists():
        raise LabError(f"No such session: {session.session_id}")
    if op_type not in ("replace", "add", "remove"):
        raise LabError(f"Unknown operation type: {op_type!r}")

    target = _resolve_within(session.modified_tree, rel_path)
    sha_before = sha256_file(target) if target.is_file() else None

    if op_type == "replace":
        if not target.is_file():
            raise LabError(f"Cannot replace: '{rel_path}' does not exist in the working tree")
        if source_file is None or not source_file.is_file():
            raise LabError(f"Replacement source file not found: {source_file}")
        shutil.copy2(source_file, target)
    elif op_type == "add":
        if target.exists():
            raise LabError(f"Cannot add: '{rel_path}' already exists in the working tree")
        if source_file is None or not source_file.is_file():
            raise LabError(f"Source file not found: {source_file}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target)
    elif op_type == "remove":
        if not target.is_file():
            raise LabError(f"Cannot remove: '{rel_path}' does not exist in the working tree")
        target.unlink()

    sha_after = sha256_file(target) if target.is_file() else None

    operation = {
        "type": op_type,
        "relPath": rel_path,
        "sourceFile": str(source_file) if source_file else None,
        "sha256Before": sha_before,
        "sha256After": sha_after,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    ops = session.load_operations()
    ops.append(operation)
    session.save_operations(ops)

    return ApplyResult(operation=operation, sha256_before=sha_before, sha256_after=sha_after)


def replay_operations(clean_tree: Path, ops: list[dict]) -> None:
    """Re-apply a recorded operations list onto a fresh tree, in place.
    Used by verify() to prove operations.json is a faithful description
    of what's in the working copy — never trusts the working copy alone.
    """
    for op in ops:
        target = _resolve_within(clean_tree, op["relPath"])
        op_type = op["type"]
        source_file = Path(op["sourceFile"]) if op.get("sourceFile") else None
        if op_type in ("replace", "add"):
            if source_file is None or not source_file.is_file():
                raise LabError(
                    f"Cannot replay operation on '{op['relPath']}': "
                    f"source file no longer available: {source_file}"
                )
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target)
        elif op_type == "remove":
            if target.is_file():
                target.unlink()
        else:
            raise LabError(f"Cannot replay unknown operation type: {op_type!r}")


@dataclass
class VerifyReport:
    original_intact: bool
    reproducible: bool
    original_mismatches: list[str] = field(default_factory=list)
    reproduction_mismatches: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.original_intact and self.reproducible


def verify_session(session: LabSession, work_dir: Path) -> VerifyReport:
    """Two independent checks, both against stored evidence rather than
    trusting the working copy:

    1. The pristine `original/` tree still matches its checksums.sha256
       recorded at init() time (nobody tampered with the snapshot).
    2. Replaying operations.json onto a *fresh* copy of that original
       reproduces exactly the current `modified/` tree, file-for-file.
    """
    if not session.exists():
        raise LabError(f"No such session: {session.session_id}")

    original_mismatches = []
    recorded = {}
    for line in session.original_checksums.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, _, rel = line.partition("  ")
        recorded[rel] = digest
    current_original = _tree_manifest(session.original_tree)
    if current_original != recorded:
        for rel in sorted(set(recorded) | set(current_original)):
            if recorded.get(rel) != current_original.get(rel):
                original_mismatches.append(rel)

    replay_dir = work_dir / "replay"
    if replay_dir.exists():
        shutil.rmtree(replay_dir)
    shutil.copytree(session.original_tree, replay_dir)
    replay_operations(replay_dir, session.load_operations())

    reproduced_manifest = _tree_manifest(replay_dir)
    actual_manifest = _tree_manifest(session.modified_tree)
    reproduction_mismatches = []
    if reproduced_manifest != actual_manifest:
        for rel in sorted(set(reproduced_manifest) | set(actual_manifest)):
            if reproduced_manifest.get(rel) != actual_manifest.get(rel):
                reproduction_mismatches.append(rel)

    shutil.rmtree(replay_dir, ignore_errors=True)

    return VerifyReport(
        original_intact=not original_mismatches,
        reproducible=not reproduction_mismatches,
        original_mismatches=original_mismatches,
        reproduction_mismatches=reproduction_mismatches,
    )


def build_session(session: LabSession) -> dict:
    """Package the modified tree into a deterministic ZIP under
    lab/rebuilt/, and write a report under lab/reports/. Never claims
    flashability — this is an offline experiment artifact, not a
    partition image."""
    if not session.exists():
        raise LabError(f"No such session: {session.session_id}")

    session.rebuilt_dir.mkdir(parents=True, exist_ok=True)
    archive_path = session.rebuilt_dir / f"{session.session_id}.zip"

    files = sorted(p for p in session.modified_tree.rglob("*") if p.is_file())
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            rel = f.relative_to(session.modified_tree).as_posix()
            info = zipfile.ZipInfo(rel, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, f.read_bytes())

    archive_hash = sha256_file(archive_path)
    modified_manifest = _tree_manifest(session.modified_tree)

    report = {
        "session": session.session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "device": TARGET_DEVICE.as_dict(),
        "operations": session.load_operations(),
        "outputArchive": str(archive_path),
        "outputArchiveSha256": archive_hash,
        "fileCount": len(modified_manifest),
        "status": "EXPERIMENTAL",
        "flashable": False,
        "notes": [
            "This archive is a plain ZIP of a modified directory tree, "
            "produced entirely offline in lab/. It is NOT a Sony partition "
            "image, is not signed, and is not flashable. See "
            "docs/FLASHING.md and docs/MODIFICATIONS.md.",
        ],
    }
    session.report_dir.mkdir(parents=True, exist_ok=True)
    (session.report_dir / REPORT_FILE).write_text(json.dumps(report, indent=2), encoding="utf-8")

    return report
