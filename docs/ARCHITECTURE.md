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
| `engine/PersonalizationEngine` | Orchestrator wiring the above; managers not yet implemented (Theme/Icon/Sound/Animation/Pack) are absent, not stubbed |
| `ui/` | `MainActivity` (category grid) → `CategoryActivity` (catalog list) |

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
