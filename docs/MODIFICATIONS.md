# Modifications — status per feature

Every modification capability is tagged with exactly one status. Never
presented as more finished than this table says.

| Feature | Status | Where |
|---|---|---|
| Font sfnt parsing/validation/metadata | **IMPLEMENTED** | `tools/cli/furaxxz/fonts.py`, tested in `tests/test_fonts.py` |
| Firmware container detection (ZIP/TAR/gzip/sparse/ext4/boot.img) | **IMPLEMENTED** | `tools/cli/furaxxz/firmware.py`, tested |
| Firmware targeted extraction (ZIP/TAR) | **IMPLEMENTED** | `tools/cli/furaxxz/firmware.py::extract` |
| SHA-256 hashing, checksums, manifests | **IMPLEMENTED** | `tools/cli/furaxxz/hashing.py` |
| Backup create/restore with corruption detection | **IMPLEMENTED** | `tools/cli/furaxxz/backup.py` |
| Theme/Pack manifest create/validate | **IMPLEMENTED** | `tools/cli/furaxxz/theme.py`, `pack.py` |
| Security gate (bootloader-aware blocking, dry-run) | **IMPLEMENTED** | `tools/cli/furaxxz/security.py` |
| Android: catalog browsing (local, offline) | **IMPLEMENTED** | `apps/furaxxz` `engine/CatalogRepository` |
| Android: in-app font application (sandboxed) | **IMPLEMENTED** | `apps/furaxxz` `engine/FontManager` |
| Android: setting device wallpaper | **IMPLEMENTED** | `apps/furaxxz` `engine/WallpaperManager` |
| Android: theme manifest parsing/validation (pure Kotlin, no `org.json`) | **IMPLEMENTED** | `apps/furaxxz` `engine/theme/ThemeManifestParser`, tested in `ThemeManifestParserTest` |
| Android: pack manifest parsing/validation (pure Kotlin) | **IMPLEMENTED** | `apps/furaxxz` `engine/pack/PackManifestParser`, tested in `PackManifestParserTest` |
| Android: theme apply — `colors` (in-app view recolor only), `wallpaper`, `font` | **IMPLEMENTED** | `apps/furaxxz` `engine/theme/ThemeManager::apply` |
| Android: pack apply — `font`/`wallpaper`/`colors` (delegates to `ThemeManager`) | **IMPLEMENTED** | `apps/furaxxz` `engine/pack/PackManager::apply` |
| Android: theme/pack `icons`/`sounds`/`animations`/`bootAnimation` components | **PLANNED** | Never applied and never reported as applied — `ThemeManager`/`PackManager` list them in `skipped`/`skippedComponents` with an explicit reason on every `apply()` call |
| Sony SIN/FTF proprietary format parsing | **PLANNED** | not started — see `docs/FIRMWARE.md` |
| Font injection into a real partition image (repack) | **BLOCKED** | `furaxxz fonts inject --execute` explicitly stops and reports BLOCKED — see `docs/FLASHING.md` |
| Android: system-wide theme/icon/sound application (touching `/system` or launcher-level theming) | **PLANNED/UNSUPPORTED** | Out of reach without root on a locked-bootloader F8331; FuraxXZ only ever recolors its own in-app views — see `docs/BOOTLOADER.md` |
| Bootloader unlock, any form | **UNSUPPORTED** | Will never be implemented — see `docs/BOOTLOADER.md` |
| Remote/hosted catalog | **PLANNED** | `RemoteCatalogSource` is a documented no-op placeholder |

## Rule

> IMPLEMENTED, EXPERIMENTAL, BLOCKED, or PLANNED — pick one, and never
> present PLANNED/EXPERIMENTAL/BLOCKED work as functional.
