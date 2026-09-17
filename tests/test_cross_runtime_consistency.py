"""Phase 9 — cross-runtime consistency checks.

The CLI (tools/cli/furaxxz/theme.py, pack.py) and the Android app
(apps/furaxxz/.../engine/theme, engine/pack) implement independent
parsers for the *same* manifest schema, documented in docs/CATALOG.md.
Nothing automatically keeps them in sync — these tests exist so a schema
drift between the two runtimes fails CI immediately instead of being
discovered by a user with a theme that loads on one side and not the
other.
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

from furaxxz import pack as pack_mod
from furaxxz import theme as theme_mod

REPO_ROOT = Path(__file__).resolve().parents[1]
ANDROID_ASSETS = REPO_ROOT / "apps" / "furaxxz" / "app" / "src" / "main" / "assets" / "catalog"

HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _bundled_theme_files():
    return sorted((ANDROID_ASSETS / "themes").glob("*.json"))


def _bundled_pack_files():
    return sorted((ANDROID_ASSETS / "packs").glob("*.json"))


def test_android_bundles_at_least_one_demo_theme_and_pack():
    themes = [f for f in _bundled_theme_files() if f.name != "manifest.json"]
    packs = [f for f in _bundled_pack_files() if f.name != "manifest.json"]
    assert themes, "expected at least one demo theme.json bundled under assets/catalog/themes/"
    assert packs, "expected at least one demo pack.json bundled under assets/catalog/packs/"


def test_every_bundled_android_theme_passes_the_cli_validator():
    """A theme.json shipped in the Android assets must be loadable by the
    CLI's validate_theme() unchanged — same schema, same rules."""
    for theme_file in _bundled_theme_files():
        if theme_file.name == "manifest.json":
            continue
        manifest = json.loads(theme_file.read_text())
        theme_mod.validate_theme(manifest)  # raises ThemeError on drift


def test_every_bundled_android_pack_passes_the_cli_validator():
    for pack_file in _bundled_pack_files():
        if pack_file.name == "manifest.json":
            continue
        manifest = json.loads(pack_file.read_text())
        pack_mod.validate_pack(manifest)  # raises PackError on drift


def test_cli_created_theme_matches_bundled_android_demo_theme():
    """Round-trip: create the exact bundled 'Furax Dark' demo theme via
    the CLI and confirm the colors are byte-identical to what Android
    ships. Catches a divergence in either the CLI or the fixture."""
    demo_path = ANDROID_ASSETS / "themes" / "furax-dark.json"
    demo = json.loads(demo_path.read_text())

    with tempfile.TemporaryDirectory() as tmp:
        cli_path = theme_mod.create_theme(Path(tmp), demo["name"], demo["colors"])
        cli_manifest = json.loads(cli_path.read_text())

    assert cli_manifest["colors"] == demo["colors"]
    assert cli_manifest["name"] == demo["name"]


def test_theme_color_regex_matches_between_cli_and_docs():
    """The CLI's HEX_COLOR regex (tools/cli/furaxxz/theme.py) must match
    what docs/CATALOG.md and the Android ThemeManifestParser both claim:
    strict #RRGGBB, 6 hex digits, nothing else."""
    assert theme_mod.HEX_COLOR.pattern == HEX_COLOR.pattern
    assert theme_mod.HEX_COLOR.match("#7C4DFF")
    assert not theme_mod.HEX_COLOR.match("#7C4")
    assert not theme_mod.HEX_COLOR.match("7C4DFF")
    assert not theme_mod.HEX_COLOR.match("#7C4DFFAA")


def test_android_theme_manifest_parser_kotlin_regex_matches_cli():
    """Read the Kotlin source directly and confirm its HEX_COLOR regex
    literal is the same pattern as the CLI's — the two are hand-written
    independently and nothing else enforces they stay equal."""
    kt_path = (
        REPO_ROOT / "apps" / "furaxxz" / "app" / "src" / "main" / "java"
        / "com" / "furax" / "furaxxz" / "engine" / "theme" / "ThemeManifestParser.kt"
    )
    kt_source = kt_path.read_text()
    match = re.search(r'HEX_COLOR = Regex\("(.+?)"\)', kt_source)
    assert match, "could not find HEX_COLOR Regex(...) literal in ThemeManifestParser.kt"
    kotlin_pattern = match.group(1)
    assert kotlin_pattern == theme_mod.HEX_COLOR.pattern
