import struct
import tarfile
import zipfile

import pytest
from furaxxz import firmware


def test_analyze_missing_file_raises(tmp_path):
    with pytest.raises(firmware.FirmwareError):
        firmware.analyze(tmp_path / "nope.zip")


def test_analyze_zip_archive_detects_partitions(tmp_path):
    zpath = tmp_path / "fw.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("system.img", b"\x00" * 100)
        zf.writestr("boot.img", b"\x00" * 100)
        zf.writestr("readme.txt", b"info")

    report = firmware.analyze(zpath)

    assert report.format == "zip-archive"
    assert set(report.partitions_detected) == {"system.img", "boot.img"}
    assert len(report.sha256) == 64


def test_analyze_corrupt_zip_raises(tmp_path):
    zpath = tmp_path / "corrupt.zip"
    zpath.write_bytes(b"PK\x03\x04" + b"not a real zip body at all")
    with pytest.raises(firmware.FirmwareError):
        firmware.analyze(zpath)


def test_analyze_tar_archive(tmp_path):
    tpath = tmp_path / "fw.tar"
    inner = tmp_path / "vendor.img"
    inner.write_bytes(b"\x00" * 50)
    with tarfile.open(tpath, "w") as tf:
        tf.add(inner, arcname="vendor.img")

    report = firmware.analyze(tpath)
    assert report.format == "tar-archive"
    assert "vendor.img" in report.partitions_detected


def test_analyze_android_sparse_image(tmp_path):
    path = tmp_path / "system.sparse.img"
    path.write_bytes(struct.pack("<I", 0xED26FF3A) + b"\x00" * 100)
    report = firmware.analyze(path)
    assert report.format == "android-sparse-image"


def test_analyze_android_boot_image(tmp_path):
    path = tmp_path / "boot.img"
    header = struct.pack(
        "<8s9I", b"ANDROID!", 1024, 0x10000000, 2048, 0x11000000, 0, 0, 0x10000100, 2048, 0
    )
    path.write_bytes(header + b"\x00" * 200)
    report = firmware.analyze(path)
    assert report.format == "android-boot-image"
    assert report.boot_image_info["kernel_size"] == 1024
    assert report.boot_image_info["ramdisk_size"] == 2048


def test_analyze_unknown_format_notes_it(tmp_path):
    path = tmp_path / "mystery.bin"
    path.write_bytes(b"totally unrecognized binary content" * 10)
    report = firmware.analyze(path)
    assert report.format == "unknown"
    assert report.notes


def test_extract_zip_system_only(tmp_path):
    zpath = tmp_path / "fw.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("system.img", b"sys-data")
        zf.writestr("boot.img", b"boot-data")

    dest = tmp_path / "out"
    extracted = firmware.extract(zpath, dest, system_only=True)

    assert extracted == ["system.img"]
    assert (dest / "system.img").read_bytes() == b"sys-data"
    assert not (dest / "boot.img").exists()


def test_extract_unsupported_format_raises(tmp_path):
    path = tmp_path / "mystery.bin"
    path.write_bytes(b"not a container")
    with pytest.raises(firmware.FirmwareError):
        firmware.extract(path, tmp_path / "out")


def test_extract_tar_path_traversal_blocked(tmp_path):
    tpath = tmp_path / "evil.tar"
    with tarfile.open(tpath, "w") as tf:
        info = tarfile.TarInfo(name="../../etc/system.img")
        data = b"evil"
        info.size = len(data)
        import io
        tf.addfile(info, io.BytesIO(data))

    dest = tmp_path / "out"
    with pytest.raises(firmware.FirmwareError):
        firmware.extract(tpath, dest, all_partitions=True)
