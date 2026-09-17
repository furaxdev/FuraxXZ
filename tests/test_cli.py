import json
import subprocess
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args, cwd=None):
    env_cmd = [sys.executable, "-m", "furaxxz", *args]
    result = subprocess.run(
        env_cmd,
        capture_output=True,
        text=True,
        cwd=cwd or REPO_ROOT,
        env={"PYTHONPATH": str(REPO_ROOT / "tools" / "cli"), "PATH": "/usr/bin:/bin:/usr/local/bin"},
        check=False,
    )
    return result


def test_cli_device_profile():
    result = run_cli("device", "profile")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["model"] == "F8331"
    assert data["bootloaderUnlockAllowed"] is False


def test_cli_security_inspect():
    result = run_cli("security", "inspect")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["flashCompatibility"] == "UNKNOWN"


def test_cli_no_command_errors():
    result = run_cli()
    assert result.returncode != 0


def test_cli_firmware_analyze_invalid_path():
    result = run_cli("firmware", "analyze", "/nonexistent/path/fw.zip")
    assert result.returncode == 1
    assert "error" in result.stderr.lower()


def test_cli_firmware_analyze_zip(tmp_path):
    zpath = tmp_path / "fw.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("boot.img", b"\x00" * 20)
    result = run_cli("firmware", "analyze", str(zpath))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["format"] == "zip-archive"
    assert "boot.img" in data["partitions_detected"]


def test_cli_fonts_validate_corrupted_file(tmp_path):
    bad = tmp_path / "corrupt.ttf"
    bad.write_bytes(b"not a real font at all, just junk bytes")
    result = run_cli("fonts", "validate", str(bad))
    assert result.returncode == 1


def test_cli_backup_roundtrip(tmp_path):
    src = tmp_path / "font.ttf"
    src.write_bytes(b"font-bytes")
    backup_dir = tmp_path / "backup"
    result = run_cli("backup", "create", str(src), "--to", str(backup_dir))
    assert result.returncode == 0
    assert backup_dir.joinpath("manifest.json").is_file()

    restore_dir = tmp_path / "restored"
    result = run_cli("backup", "restore", str(backup_dir), "--to", str(restore_dir))
    assert result.returncode == 0
    assert (restore_dir / "font.ttf").read_bytes() == b"font-bytes"


def test_cli_doctor_runs():
    result = run_cli("doctor")
    assert "Environment" in result.stdout


def test_cli_clean_preserves_gitkeep(tmp_path, monkeypatch):
    import importlib

    from furaxxz import __main__ as cli_main

    fake_root = tmp_path
    (fake_root / "firmware" / "extracted").mkdir(parents=True)
    (fake_root / "lab" / "extracted").mkdir(parents=True)
    (fake_root / "firmware" / "extracted" / ".gitkeep").write_text("")
    (fake_root / "firmware" / "extracted" / "stray.img").write_bytes(b"x")

    monkeypatch.setattr(cli_main, "REPO_ROOT", fake_root)
    monkeypatch.setattr(cli_main, "LAB_DIR", fake_root / "lab")

    class Args:
        dry_run = False

    cli_main.cmd_clean(Args())

    assert (fake_root / "firmware" / "extracted" / ".gitkeep").exists()
    assert not (fake_root / "firmware" / "extracted" / "stray.img").exists()
    importlib.reload(cli_main)  # restore module-level constants for other tests


def test_cli_version():
    result = run_cli("--version")
    assert result.returncode == 0
    assert "furaxxz" in result.stdout
