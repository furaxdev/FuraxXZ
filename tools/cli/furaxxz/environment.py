"""`furaxxz doctor` — real environment checks, nothing assumed."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def _run_version(cmd: list[str]) -> str | None:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False)
        lines = [
            line for line in (out.stdout or out.stderr or "").strip().splitlines()
            if "JAVA_TOOL_OPTIONS" not in line and line.strip()
        ]
        return lines[0] if lines else "(no output)"
    except (FileNotFoundError, subprocess.SubprocessError):
        return None


def check_binary(name: str, cmd: list[str]) -> CheckResult:
    path = shutil.which(cmd[0])
    if not path:
        return CheckResult(name, False, "not found on PATH")
    version = _run_version(cmd)
    return CheckResult(name, True, f"{path} — {version or 'installed'}")


def check_python() -> CheckResult:
    return CheckResult("python", True, f"{sys.executable} — {platform.python_version()}")


def check_android_sdk() -> CheckResult:
    home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if not home:
        return CheckResult("android-sdk", False, "ANDROID_HOME/ANDROID_SDK_ROOT not set")
    sdkmanager = shutil.which("sdkmanager")
    if sdkmanager:
        return CheckResult("android-sdk", True, f"{home} (sdkmanager: {sdkmanager})")
    return CheckResult("android-sdk", False, f"{home} set but sdkmanager not found")


def check_disk(path: str = ".") -> CheckResult:
    usage = shutil.disk_usage(path)
    free_gb = usage.free / (1024 ** 3)
    ok = free_gb > 2.0
    return CheckResult("disk-space", ok, f"{free_gb:.1f} GiB free at {os.path.abspath(path)}")


def check_git_repo(path: str = ".") -> CheckResult:
    git_dir = os.path.join(path, ".git")
    if os.path.isdir(git_dir):
        return CheckResult("git-repo", True, f"{os.path.abspath(path)} is a git repository")
    return CheckResult("git-repo", False, f"{os.path.abspath(path)} is not a git repository")


def run_doctor(repo_root: str = ".") -> list[CheckResult]:
    results = [
        check_binary("git", ["git", "--version"]),
        check_python(),
        check_binary("pip", [sys.executable, "-m", "pip", "--version"]),
        check_binary("node", ["node", "--version"]),
        check_binary("npm", ["npm", "--version"]),
        check_binary("java", ["java", "-version"]),
        check_binary("gradle", ["gradle", "-v"]),
        check_android_sdk(),
        check_binary("unzip", ["unzip", "-v"]),
        check_binary("tar", ["tar", "--version"]),
        check_binary("file", ["file", "--version"]),
        check_binary("sha256sum", ["sha256sum", "--version"]),
        check_disk(repo_root),
        check_git_repo(repo_root),
    ]
    return results
