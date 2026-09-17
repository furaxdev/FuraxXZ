"""Firmware analyzer / extractor.

Detects real container formats (ZIP, TAR, gzip, Android sparse image,
ext4 raw image, Android boot image) by reading actual magic bytes and
structure instead of assuming a fixed Sony firmware layout. Sony's
official FTF/SIN service-ROM format is a proprietary container; this
module identifies what it can from the bytes actually present and never
fabricates fields (model/build/partitions) it did not find.
"""

from __future__ import annotations

import struct
import tarfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from .hashing import sha256_file

ANDROID_BOOT_MAGIC = b"ANDROID!"
ANDROID_SPARSE_MAGIC = b"\x3a\xff\x26\xed"  # little-endian 0xED26FF3A
EXT4_SUPERBLOCK_OFFSET = 1024
EXT4_MAGIC = b"\x53\xef"  # little-endian 0xEF53, at superblock offset +0x38
GZIP_MAGIC = b"\x1f\x8b"
ZIP_MAGIC = b"PK\x03\x04"
ZIP_EMPTY_MAGIC = b"PK\x05\x06"

KNOWN_PARTITION_NAMES = {
    "boot.img", "system.img", "vendor.img", "userdata.img", "cache.img",
    "recovery.img", "boot", "system", "vendor", "userdata", "cache",
}


class FirmwareError(ValueError):
    pass


@dataclass
class FirmwareReport:
    path: str
    size_bytes: int
    sha256: str
    format: str
    entries: list[str] = field(default_factory=list)
    partitions_detected: list[str] = field(default_factory=list)
    boot_image_info: dict | None = None
    notes: list[str] = field(default_factory=list)


def _detect_boot_image(data: bytes) -> dict | None:
    """Parse the Android boot image header (v0/v1/v2) if present at offset 0."""
    if not data.startswith(ANDROID_BOOT_MAGIC):
        return None
    # boot_img_hdr v0: magic(8) kernel_size(4) kernel_addr(4) ramdisk_size(4)
    # ramdisk_addr(4) second_size(4) second_addr(4) tags_addr(4) page_size(4)
    # header_version(4) os_version(4) name[16] cmdline[512] ...
    if len(data) < 8 + 4 * 9:
        raise FirmwareError("Truncated Android boot image header")
    fields = struct.unpack_from("<8s9I", data, 0)
    (
        _magic, kernel_size, _kernel_addr, ramdisk_size, _ramdisk_addr,
        second_size, _second_addr, _tags_addr, page_size, header_version,
    ) = fields
    return {
        "kernel_size": kernel_size,
        "ramdisk_size": ramdisk_size,
        "second_size": second_size,
        "page_size": page_size,
        "header_version": header_version,
    }


def _detect_ext4(data: bytes) -> bool:
    sb_off = EXT4_SUPERBLOCK_OFFSET
    if len(data) < sb_off + 0x3A:
        return False
    return data[sb_off + 0x38 : sb_off + 0x3A] == EXT4_MAGIC


def analyze(path: Path) -> FirmwareReport:
    if not path.is_file():
        raise FirmwareError(f"Not a file: {path}")

    size = path.stat().st_size
    digest = sha256_file(path)
    with path.open("rb") as f:
        head = f.read(4096)

    report = FirmwareReport(path=str(path), size_bytes=size, sha256=digest, format="unknown")

    if head[:4] == ANDROID_SPARSE_MAGIC:
        report.format = "android-sparse-image"
        report.notes.append(
            "Android sparse image detected (0xED26FF3A). Must be converted with "
            "simg2img before further inspection; not done automatically."
        )
    elif head.startswith(ANDROID_BOOT_MAGIC):
        report.format = "android-boot-image"
        try:
            report.boot_image_info = _detect_boot_image(head)
        except FirmwareError as exc:
            report.notes.append(f"boot image header parse failed: {exc}")
    elif _detect_ext4(head if size >= 4096 else path.read_bytes()):
        report.format = "ext4-raw-image"
        report.notes.append("Raw ext4 filesystem image (superblock magic 0xEF53 found).")
    elif head[:4] == ZIP_MAGIC or head[:4] == ZIP_EMPTY_MAGIC:
        report.format = "zip-archive"
        try:
            with zipfile.ZipFile(path) as zf:
                names = zf.namelist()
                report.entries = names[:500]
                report.partitions_detected = sorted(
                    n for n in names if Path(n).name.lower() in KNOWN_PARTITION_NAMES
                )
                if zf.testzip() is not None:
                    report.notes.append("ZIP CRC check failed for at least one entry.")
        except zipfile.BadZipFile as exc:
            raise FirmwareError(f"Corrupt ZIP archive: {exc}") from exc
    elif head[:2] == GZIP_MAGIC:
        report.format = "gzip-compressed"
        report.notes.append(
            "Gzip-compressed payload; inner format not identified without decompression."
        )
    elif tarfile.is_tarfile(path):
        report.format = "tar-archive"
        with tarfile.open(path) as tf:
            names = tf.getnames()
            report.entries = names[:500]
            report.partitions_detected = sorted(
                n for n in names if Path(n).name.lower() in KNOWN_PARTITION_NAMES
            )
    else:
        report.notes.append(
            "No known firmware container signature matched (not ZIP/TAR/gzip/"
            "sparse/ext4/boot.img). This may be a proprietary Sony SIN/FTF "
            "container or an unsupported format — treat as EXPERIMENTAL."
        )

    if not report.partitions_detected and report.format in ("zip-archive", "tar-archive"):
        report.notes.append("No recognized partition images found inside the archive.")

    return report


def extract(path: Path, dest: Path, *, system_only=False, boot_only=False,
            vendor_only=False, all_partitions=False) -> list[str]:
    """Extract a ZIP/TAR firmware archive into `dest`.

    Defaults to targeted extraction (only recognized partition images)
    unless `all_partitions` is set. Refuses to extract unknown formats
    rather than guessing.
    """
    report = analyze(path)
    if report.format not in ("zip-archive", "tar-archive"):
        raise FirmwareError(
            f"Cannot extract format '{report.format}': only zip-archive and "
            "tar-archive are supported for extraction in this lab tool."
        )

    filters = []
    if system_only:
        filters.append("system")
    if boot_only:
        filters.append("boot")
    if vendor_only:
        filters.append("vendor")

    def wanted(name: str) -> bool:
        base = Path(name).name.lower()
        if all_partitions or not filters:
            return base in KNOWN_PARTITION_NAMES if not all_partitions else True
        return any(base.startswith(f) for f in filters)

    dest.mkdir(parents=True, exist_ok=True)
    extracted: list[str] = []

    if report.format == "zip-archive":
        with zipfile.ZipFile(path) as zf:
            for name in zf.namelist():
                if wanted(name):
                    zf.extract(name, dest)
                    extracted.append(name)
    else:
        with tarfile.open(path) as tf:
            for member in tf.getmembers():
                if wanted(member.name):
                    # Guard against path traversal from a crafted archive.
                    target = (dest / member.name).resolve()
                    if not str(target).startswith(str(dest.resolve())):
                        raise FirmwareError(f"Unsafe path in archive: {member.name}")
                    tf.extract(member, dest)
                    extracted.append(member.name)

    return extracted
