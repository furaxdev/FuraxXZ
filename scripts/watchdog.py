#!/usr/bin/env python3
"""FuraxXZ watchdog — non-destructive environment/repo health snapshot.

Writes reports/latest.md and appends a timestamped copy to
reports/history/. Never modifies git state, source files, or the catalog.

Usage: python3 scripts/watchdog.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "cli"))

from furaxxz import environment  # noqa: E402


def _git(*args: str) -> str:
    try:
        out = subprocess.run(
            ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, timeout=15, check=False
        )
        return out.stdout.strip() or out.stderr.strip()
    except subprocess.SubprocessError as exc:
        return f"(git unavailable: {exc})"


def _run_tests() -> tuple[bool, str]:
    try:
        out = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=120, check=False,
        )
        summary = out.stdout.strip().splitlines()[-1] if out.stdout.strip() else out.stderr.strip()
        return out.returncode == 0, summary
    except subprocess.SubprocessError as exc:
        return False, f"could not run pytest: {exc}"


def build_report() -> str:
    now = datetime.now(timezone.utc).isoformat()
    checks = environment.run_doctor(str(REPO_ROOT))
    env_ok = all(c.ok for c in checks)

    branch = _git("symbolic-ref", "--short", "-q", "HEAD") or "(detached)"
    status = _git("status", "--porcelain")
    dirty = bool(status)
    last_commit = _git("log", "-1", "--format=%h %s") or "(no commits yet)"

    tests_ok, tests_summary = _run_tests()

    disk = shutil.disk_usage(REPO_ROOT)
    disk_free_gb = disk.free / (1024 ** 3)

    lines = [
        "# FuraxXZ Watchdog Report",
        "",
        f"Generated: {now}",
        "",
        "## Git",
        f"- Branch: `{branch}`",
        f"- Working tree: {'DIRTY (uncommitted changes)' if dirty else 'clean'}",
        f"- Last commit: {last_commit}",
        "",
        "## Environment",
        f"- Status: {'READY' if env_ok else 'MISSING PIECES (see docs/ENVIRONMENT.md)'}",
    ]
    for c in checks:
        lines.append(f"  - [{'OK' if c.ok else 'FAIL'}] {c.name}: {c.detail}")

    lines += [
        "",
        "## Tests",
        f"- Result: {'PASS' if tests_ok else 'FAIL'}",
        f"- Summary: {tests_summary}",
        "",
        "## Disk",
        f"- Free: {disk_free_gb:.1f} GiB",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    report = build_report()
    reports_dir = REPO_ROOT / "reports"
    history_dir = reports_dir / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    (reports_dir / "latest.md").write_text(report, encoding="utf-8")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (history_dir / f"{stamp}.md").write_text(report, encoding="utf-8")

    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
