# FuraxXZ — Architecture

## Two runtimes, one catalog format

FuraxXZ has two independent runtimes that share the same on-disk catalog
schema (JSON manifests for themes/packs, sfnt fonts, image assets):

1. **CLI (`tools/cli/furaxxz/`, Python 3.10+, stdlib only)** — the offline
   lab: firmware analysis/extraction, font validation/inspection, theme &
   pack manifest management, hashing, backup/restore, and the security
   gate. Runs anywhere Python runs; no Android device or SDK required.
2. **Android app (`apps/furaxxz/`, Kotlin, Views/XML, API 26+)** — the
   on-device personalization UI: browse the catalog, preview items, set a
   wallpaper, apply a font within the app. It does **not** touch `/system`
   or flash anything — see [MODIFICATIONS.md](MODIFICATIONS.md) for why.

## CLI module map

| Module | Responsibility |
|---|---|
| `device.py` | The target device profile (Sony F8331/kagura) — single source of truth |
| `security.py` | Bootloader/flash gating, dry-run banners, `SecurityBlocked` |
| `firmware.py` | Real container/format detection (ZIP/TAR/sparse/ext4/boot.img), targeted extraction |
| `fonts.py` | sfnt (TTF/OTF) parsing, validation, metadata, hashing |
| `theme.py` / `pack.py` | Manifest schema, creation, validation |
| `hashing.py` | SHA-256, checksums.sha256, manifests |
| `backup.py` | Hashed backup create/restore with corruption detection |
| `lab.py` | Offline system modification lab: session snapshot, recorded file operations (replace/add/remove), reproducibility+tamper verification, ZIP packaging — every write confined to `lab/`, output never claimed flashable |
| `environment.py` | `doctor` — real, non-assumed environment checks |
| `__main__.py` | argparse-based CLI wiring all of the above |

## Android module map

| Package | Responsibility |
|---|---|
| `model/` | `Category`, `CatalogItem` — plain data types |
| `engine/CatalogSource` + `LocalCatalogSource` + `RemoteCatalogSource` | Catalog reading, local-first, offline by default (remote is a documented no-op placeholder, see `RemoteCatalogSource.kt`) |
| `engine/CatalogRepository` | Merges sources |
| `engine/FontManager` | Loads/validates a font as a real `Typeface`, applies it to in-app views |
| `engine/WallpaperManager` | Preview, local cache, and actually setting the device wallpaper via `android.app.WallpaperManager` |
| `engine/json/JsonValue` + `JsonParser` | A small, dependency-free recursive-descent JSON parser. Exists because `org.json` (Android's bundled JSON lib) throws `RuntimeException("not mocked")` in local JVM unit tests — verified empirically — and pulling in Robolectric just to parse a flat theme/pack manifest isn't worth a new dependency. Fully unit-tested (`JsonParserTest`) |
| `engine/theme/ThemeManifest` + `ThemeManifestParser` | Theme schema mirroring the CLI's `theme.py` exactly; pure Kotlin, unit-tested (`ThemeManifestParserTest`) |
| `engine/theme/ThemeManager` | Loads a theme from `assets/catalog/themes/`, applies `colors` (recolors the views it's given — never anything outside the app), `wallpaper`/`font` (delegates to the managers above); reports `icons`/`sounds`/`animations` as explicitly skipped (PLANNED), never as applied |
| `engine/pack/PackManifest` + `PackManifestParser` | Pack schema mirroring `pack.py`; pure Kotlin, unit-tested (`PackManifestParserTest`) |
| `engine/pack/PackManager` | Loads a pack from `assets/catalog/packs/`, applies `font`/`wallpaper`/`colors` by delegating to `ThemeManager` (no duplicated logic); reports `icons`/`sounds`/`bootAnimation` as explicitly skipped |
| `engine/PersonalizationEngine` | Orchestrator wiring `catalog`, `fonts`, `wallpapers`, `themes`, `packs`; Icon/Sound/Animation managers remain absent, not stubbed |
| `ui/` | `MainActivity` (category grid) → `CategoryActivity` (catalog list; tapping a Theme/Pack item shows a confirmation dialog, then applies it and reports exactly what was applied vs. skipped) |

## Why not one shared engine yet

See `engine/README.md` at the repo root: a cross-runtime shared engine is
a legitimate future refactor once logic (e.g. the sfnt parser) is
duplicated for real, not something to scaffold empty ahead of need.

## Data flow (typical: inspect + validate a font before considering
personalization)

```
user font file
     │
     ▼
furaxxz fonts validate <font>   (tools/cli/furaxxz/fonts.py: parse_font)
     │  sfnt signature → table directory → head/maxp/OS2/name tables
     ▼
FontMetadata (family, weights, glyph count, sha256, ...)
     │
     ▼
furaxxz fonts inject <image> <font>   (security-gated, dry-run by default)
     │  1) validate  2) compatibility  3) space  4) hash  5) backup  6) modify (lab/ only)
     ▼
report: what was actually done, or why it was BLOCKED
```

## Data flow (offline lab session — Phase 8)

```
source tree (e.g. furaxxz firmware extract output, or any directory)
     │
     ▼
furaxxz lab init <source_dir> --session s1
     │  copy → lab/original/s1/tree/ (hashed, immutable)
     │  copy → lab/modified/s1/tree/ (working copy) + operations.json = []
     ▼
furaxxz lab apply s1 --replace <rel_path> <file>   (repeatable; each call appends to operations.json)
     │  modifies lab/modified/s1/tree/ only; rejects path traversal
     ▼
furaxxz lab verify s1
     │  1) re-hash lab/original/s1/tree/ against its init-time checksums (tamper check)
     │  2) replay operations.json onto a FRESH copy of the original, diff vs lab/modified/s1/tree/
     ▼
furaxxz lab build s1   (only meaningful once verify passes)
     │  package lab/modified/s1/tree/ → lab/rebuilt/s1/s1.zip
     ▼
lab/reports/s1/report.json   {"status": "EXPERIMENTAL", "flashable": false, ...}
```
