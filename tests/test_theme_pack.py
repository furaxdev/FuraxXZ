import pytest
from furaxxz import pack as pack_mod
from furaxxz import theme as theme_mod


def test_create_theme_and_load(tmp_path):
    path = theme_mod.create_theme(tmp_path, "midnight", {"primary": "#7C4DFF", "background": "#000000"})
    loaded = theme_mod.load_theme(path)
    assert loaded["name"] == "midnight"
    assert loaded["colors"]["primary"] == "#7C4DFF"


def test_theme_rejects_empty_name(tmp_path):
    with pytest.raises(theme_mod.ThemeError):
        theme_mod.create_theme(tmp_path, "", {"primary": "#FFFFFF"})


def test_theme_rejects_non_hex_color(tmp_path):
    with pytest.raises(theme_mod.ThemeError):
        theme_mod.create_theme(tmp_path, "bad", {"primary": "purple"})


def test_theme_rejects_unknown_field(tmp_path):
    with pytest.raises(theme_mod.ThemeError):
        theme_mod.create_theme(tmp_path, "bad", {"primary": "#FFFFFF"}, notAField="x")


def test_create_pack_and_load(tmp_path):
    path = pack_mod.create_pack(tmp_path, "furax-dark", font="Inter.ttf", colors={"primary": "#111"})
    loaded = pack_mod.load_pack(path)
    assert loaded["name"] == "furax-dark"
    assert loaded["components"]["font"] == "Inter.ttf"


def test_pack_rejects_empty_components(tmp_path):
    with pytest.raises(pack_mod.PackError):
        pack_mod.create_pack(tmp_path, "empty")


def test_pack_rejects_unknown_component(tmp_path):
    with pytest.raises(pack_mod.PackError):
        pack_mod.create_pack(tmp_path, "bad", notAComponent="x")
