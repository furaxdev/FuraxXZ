
import pytest
from furaxxz import fonts


def test_parse_valid_ttf(tmp_path, valid_ttf_bytes):
    font_path = tmp_path / "test.ttf"
    font_path.write_bytes(valid_ttf_bytes)

    meta = fonts.parse_font(font_path)

    assert meta.format == "TrueType"
    assert meta.family == "FuraxXZ Test Sans"
    assert meta.subfamily == "Regular"
    assert meta.units_per_em == 2048
    assert meta.num_glyphs == 42
    assert meta.weight_class == 400
    assert meta.is_italic is False
    assert len(meta.sha256) == 64


def test_parse_italic_and_weight(tmp_path, ttf_builder):
    font_path = tmp_path / "bold-italic.ttf"
    font_path.write_bytes(ttf_builder(weight_class=700, italic=True))

    meta = fonts.parse_font(font_path)
    assert meta.weight_class == 700
    assert meta.is_italic is True


def test_reject_garbage_file(tmp_path):
    bad = tmp_path / "not-a-font.ttf"
    bad.write_bytes(b"this is definitely not a font file, just text padding out to be long enough")

    with pytest.raises(fonts.FontValidationError):
        fonts.parse_font(bad)


def test_reject_missing_file(tmp_path):
    with pytest.raises(fonts.FontValidationError):
        fonts.parse_font(tmp_path / "does-not-exist.ttf")


def test_reject_truncated_table(tmp_path):
    truncated = tmp_path / "truncated.ttf"
    # Valid signature + table count, but no actual table directory bytes.
    truncated.write_bytes(b"\x00\x01\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00")
    with pytest.raises(fonts.FontValidationError):
        fonts.parse_font(truncated)


def test_validate_font_returns_tuple(tmp_path, valid_ttf_bytes):
    font_path = tmp_path / "ok.ttf"
    font_path.write_bytes(valid_ttf_bytes)

    ok, msg, meta = fonts.validate_font(font_path)
    assert ok is True
    assert meta is not None
    assert "OK" in msg


def test_validate_font_invalid_returns_none_meta(tmp_path):
    bad = tmp_path / "bad.otf"
    bad.write_bytes(b"garbage")
    ok, _msg, meta = fonts.validate_font(bad)
    assert ok is False
    assert meta is None
