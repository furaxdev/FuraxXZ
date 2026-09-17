import pytest
from furaxxz import backup


def test_create_and_restore_roundtrip(tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    f1 = src_dir / "font.ttf"
    f1.write_bytes(b"fake font bytes")
    f2 = src_dir / "wallpaper.png"
    f2.write_bytes(b"fake png bytes")

    backup_dir = tmp_path / "backup1"
    manifest_path = backup.create_backup([f1, f2], backup_dir)
    assert manifest_path.is_file()

    restore_dir = tmp_path / "restored"
    restored = backup.restore_backup(backup_dir, restore_dir)

    assert set(restored) == {"font.ttf", "wallpaper.png"}
    assert (restore_dir / "font.ttf").read_bytes() == b"fake font bytes"
    assert (restore_dir / "wallpaper.png").read_bytes() == b"fake png bytes"


def test_create_backup_no_sources_raises(tmp_path):
    with pytest.raises(backup.BackupError):
        backup.create_backup([], tmp_path / "backup")


def test_create_backup_missing_source_raises(tmp_path):
    with pytest.raises(backup.BackupError):
        backup.create_backup([tmp_path / "missing.ttf"], tmp_path / "backup")


def test_restore_detects_corruption(tmp_path):
    src = tmp_path / "font.ttf"
    src.write_bytes(b"original bytes")
    backup_dir = tmp_path / "backup"
    backup.create_backup([src], backup_dir)

    # Corrupt the stored backup file after the fact.
    (backup_dir / "files" / "font.ttf").write_bytes(b"corrupted!!")

    with pytest.raises(backup.BackupError, match="Hash mismatch"):
        backup.restore_backup(backup_dir, tmp_path / "restored")


def test_restore_missing_manifest_raises(tmp_path):
    with pytest.raises(backup.BackupError):
        backup.restore_backup(tmp_path / "no-such-backup", tmp_path / "restored")
