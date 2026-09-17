"""Font engine: real SFNT (TTF/OTF) parsing, validation and metadata.

Implemented without third-party font libraries (fontTools is not guaranteed
to be installed — see docs/ENVIRONMENT.md) by reading the sfnt table
directory and the `name`/`OS/2`/`head` tables directly, per the OpenType
spec.
"""

from __future__ import annotations

import contextlib
import struct
from dataclasses import dataclass, field
from pathlib import Path

from .hashing import sha256_file

SFNT_VERSIONS = {
    b"\x00\x01\x00\x00": "TrueType",
    b"OTTO": "OpenType (CFF)",
    b"true": "TrueType (Apple)",
    b"ttcf": "TrueType Collection",
}

NAME_ID_FAMILY = 1
NAME_ID_SUBFAMILY = 2
NAME_ID_FULL_NAME = 4
NAME_ID_VERSION = 5
NAME_ID_LICENSE = 13

# Windows platform (3) / Unicode BMP encoding (1), and Mac platform (1).
PLATFORM_WINDOWS = 3
PLATFORM_MAC = 1

FONT_PROFILES = ["System", "Readable", "Modern", "Gaming", "Anime", "Developer", "Custom"]


class FontValidationError(ValueError):
    pass


@dataclass
class FontMetadata:
    path: str
    format: str
    family: str | None = None
    subfamily: str | None = None
    full_name: str | None = None
    version: str | None = None
    license: str | None = None
    num_glyphs: int | None = None
    units_per_em: int | None = None
    weight_class: int | None = None
    is_italic: bool | None = None
    tables: list[str] = field(default_factory=list)
    size_bytes: int = 0
    sha256: str = ""


def _read_name_table(data: bytes, offset: int, length: int) -> dict:
    """Parse the sfnt `name` table into {name_id: str}, preferring Windows
    Unicode records and falling back to Mac Roman ASCII records."""
    _fmt, count, string_offset = struct.unpack_from(">HHH", data, offset)
    records = []
    pos = offset + 6
    for _ in range(count):
        platform_id, encoding_id, language_id, name_id, rec_len, rec_off = struct.unpack_from(
            ">HHHHHH", data, pos
        )
        records.append((platform_id, encoding_id, language_id, name_id, rec_len, rec_off))
        pos += 12

    result: dict[int, str] = {}
    # Two passes: Mac Roman first (fills gaps), then Windows overrides.
    for platform_id, encoding_id, _lang, name_id, rec_len, rec_off in records:
        raw = data[offset + string_offset + rec_off : offset + string_offset + rec_off + rec_len]
        if platform_id == PLATFORM_MAC:
            with contextlib.suppress(UnicodeDecodeError):
                result.setdefault(name_id, raw.decode("mac_roman"))
    for platform_id, encoding_id, _lang, name_id, rec_len, rec_off in records:
        raw = data[offset + string_offset + rec_off : offset + string_offset + rec_off + rec_len]
        if platform_id == PLATFORM_WINDOWS:
            with contextlib.suppress(UnicodeDecodeError):
                result[name_id] = raw.decode("utf-16-be")
    return result


def parse_font(path: Path) -> FontMetadata:
    """Parse a TTF/OTF file's sfnt structure. Raises FontValidationError on
    anything that doesn't look like a real, well-formed font file."""
    if not path.is_file():
        raise FontValidationError(f"Not a file: {path}")

    data = path.read_bytes()
    if len(data) < 12:
        raise FontValidationError("File too small to contain an sfnt header")

    sig = data[0:4]
    fmt = SFNT_VERSIONS.get(sig)
    if fmt is None:
        raise FontValidationError(
            f"Unrecognized font signature {sig!r}; expected TTF/OTF/TTC magic"
        )
    if fmt == "TrueType Collection":
        raise FontValidationError("TrueType Collection (.ttc) is not supported for injection")

    num_tables = struct.unpack_from(">H", data, 4)[0]
    if num_tables == 0 or num_tables > 128:
        raise FontValidationError(f"Implausible table count: {num_tables}")

    tables: dict[str, tuple[int, int]] = {}
    pos = 12
    for _ in range(num_tables):
        if pos + 16 > len(data):
            raise FontValidationError("Truncated table directory")
        tag, _checksum, offset, length = struct.unpack_from(">4sIII", data, pos)
        tag_str = tag.decode("latin-1")
        if offset + length > len(data):
            raise FontValidationError(f"Table '{tag_str}' extends past end of file")
        tables[tag_str] = (offset, length)
        pos += 16

    for required in ("head", "name"):
        if required not in tables:
            raise FontValidationError(f"Missing required sfnt table: '{required}'")

    meta = FontMetadata(
        path=str(path),
        format=fmt,
        tables=sorted(tables.keys()),
        size_bytes=len(data),
        sha256=sha256_file(path),
    )

    head_off, head_len = tables["head"]
    if head_len >= 54:
        # head table layout: unitsPerEm at +18, macStyle at +44.
        units_per_em = struct.unpack_from(">H", data, head_off + 18)[0]
        mac_style = struct.unpack_from(">H", data, head_off + 44)[0]
        meta.units_per_em = units_per_em
        # macStyle bit 1 (0x02) = italic
        meta.is_italic = bool(mac_style & 0x02)

    if "maxp" in tables:
        maxp_off, maxp_len = tables["maxp"]
        if maxp_len >= 6:
            meta.num_glyphs = struct.unpack_from(">H", data, maxp_off + 4)[0]

    if "OS/2" in tables:
        os2_off, os2_len = tables["OS/2"]
        if os2_len >= 6:
            meta.weight_class = struct.unpack_from(">H", data, os2_off + 4)[0]

    name_off, name_len = tables["name"]
    try:
        names = _read_name_table(data, name_off, name_len)
    except struct.error as exc:
        raise FontValidationError(f"Malformed 'name' table: {exc}") from exc

    meta.family = names.get(NAME_ID_FAMILY)
    meta.subfamily = names.get(NAME_ID_SUBFAMILY)
    meta.full_name = names.get(NAME_ID_FULL_NAME)
    meta.version = names.get(NAME_ID_VERSION)
    meta.license = names.get(NAME_ID_LICENSE)

    return meta


def validate_font(path: Path) -> tuple[bool, str, FontMetadata | None]:
    """Return (is_valid, message, metadata_or_None)."""
    try:
        meta = parse_font(path)
    except FontValidationError as exc:
        return False, str(exc), None
    return True, "OK: well-formed sfnt font", meta
