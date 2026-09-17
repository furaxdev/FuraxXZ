import hashlib

import pytest
from furaxxz import hashing


def test_sha256_file_matches_hashlib(tmp_path):
    f = tmp_path / "data.bin"
    content = b"FuraxXZ" * 10000
    f.write_bytes(content)

    assert hashing.sha256_file(f) == hashlib.sha256(content).hexdigest()


def test_sha256_file_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        hashing.sha256_file(tmp_path / "nope.bin")


def test_write_and_verify_checksums(tmp_path):
    root = tmp_path
    (root / "a.txt").write_bytes(b"aaa")
    (root / "b.txt").write_bytes(b"bbb")
    checksums_path = root / "checksums.sha256"

    hashing.write_checksums(root, [root / "a.txt", root / "b.txt"], checksums_path)
    result = hashing.verify_checksums(root, checksums_path)

    assert result["ok"] == ["a.txt", "b.txt"]
    assert result["failed"] == []
    assert result["missing"] == []


def test_verify_checksums_detects_tamper(tmp_path):
    root = tmp_path
    (root / "a.txt").write_bytes(b"original")
    checksums_path = root / "checksums.sha256"
    hashing.write_checksums(root, [root / "a.txt"], checksums_path)

    (root / "a.txt").write_bytes(b"tampered!")
    result = hashing.verify_checksums(root, checksums_path)

    assert result["failed"] == ["a.txt"]
    assert result["ok"] == []


def test_verify_checksums_detects_missing(tmp_path):
    root = tmp_path
    (root / "a.txt").write_bytes(b"original")
    checksums_path = root / "checksums.sha256"
    hashing.write_checksums(root, [root / "a.txt"], checksums_path)

    (root / "a.txt").unlink()
    result = hashing.verify_checksums(root, checksums_path)

    assert result["missing"] == ["a.txt"]


def test_build_manifest_shape():
    manifest = hashing.build_manifest(
        {"device": "kagura", "manufacturer": "Sony", "model": "F8331", "android": "8.0.0", "build": "x"},
        [{"name": "a.txt", "sha256": "abc"}],
    )
    assert manifest["device"] == "kagura"
    assert "timestamp" in manifest
    assert manifest["components"][0]["name"] == "a.txt"
