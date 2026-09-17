import struct
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools" / "cli"))


def _name_record(platform_id, encoding_id, language_id, name_id, text, is_utf16):
    encoded = text.encode("utf-16-be") if is_utf16 else text.encode("mac_roman")
    return (platform_id, encoding_id, language_id, name_id, encoded)


def build_minimal_ttf(family="FuraxXZ Test Sans", weight_class=400, italic=False) -> bytes:
    """Build a minimal, structurally valid TTF file with head/maxp/OS2/name
    tables — enough for fonts.parse_font to succeed without a real font
    binary checked into the repo."""
    records = [
        _name_record(3, 1, 0x409, 1, family, True),
        _name_record(3, 1, 0x409, 2, "Regular", True),
        _name_record(3, 1, 0x409, 4, f"{family} Regular", True),
    ]
    string_data = b"".join(r[4] for r in records)
    name_header = struct.pack(">HHH", 0, len(records), 6 + 12 * len(records))
    name_records = b""
    offset = 0
    for platform_id, encoding_id, language_id, name_id, encoded in records:
        name_records += struct.pack(
            ">HHHHHH", platform_id, encoding_id, language_id, name_id, len(encoded), offset
        )
        offset += len(encoded)
    name_table = name_header + name_records + string_data

    mac_style = 0x02 if italic else 0x00
    head_table = (
        b"\x00\x01\x00\x00"          # version 1.0
        + b"\x00\x01\x00\x00"        # fontRevision
        + b"\x00\x00\x00\x00"        # checkSumAdjustment
        + b"\x5f\x0f\x3c\xf5"        # magicNumber
        + struct.pack(">H", 0)       # flags
        + struct.pack(">H", 2048)    # unitsPerEm (offset 18)
        + b"\x00" * 8                # created
        + b"\x00" * 8                # modified
        + struct.pack(">hhhh", 0, 0, 0, 0)  # xMin/yMin/xMax/yMax
        + struct.pack(">H", mac_style)      # macStyle (offset 44)
        + struct.pack(">H", 0)       # lowestRecPPEM
        + struct.pack(">h", 0)       # fontDirectionHint
        + struct.pack(">h", 0)       # indexToLocFormat
        + struct.pack(">h", 0)       # glyphDataFormat
    )
    assert len(head_table) == 54

    maxp_table = struct.pack(">I", 0x00010000) + struct.pack(">H", 42) + b"\x00" * 26

    os2_table = struct.pack(">HH", 0, 0) + struct.pack(">H", weight_class) + b"\x00" * 60

    tables = {"head": head_table, "maxp": maxp_table, b"OS/2".decode(): os2_table, "name": name_table}
    tag_order = ["head", "maxp", "OS/2", "name"]

    num_tables = len(tag_order)
    header = struct.pack(">4sHHHH", b"\x00\x01\x00\x00", num_tables, 0, 0, 0)

    dir_size = 16 * num_tables
    body_offset = 12 + dir_size
    directory = b""
    body = b""
    for tag in tag_order:
        data = tables[tag]
        directory += struct.pack(">4sIII", tag.encode("latin-1"), 0, body_offset + len(body), len(data))
        body += data

    return header + directory + body


@pytest.fixture
def valid_ttf_bytes():
    return build_minimal_ttf()


@pytest.fixture
def ttf_builder():
    return build_minimal_ttf


@pytest.fixture
def repo_root():
    return REPO_ROOT
