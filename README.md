# FuraxXZ

**FuraxXZ — Personalize your Xperia.**

A personalization and firmware-analysis lab for the Sony Xperia XZ
(F8331 / `kagura`, Android 8.0.0, build `41.3.2.A.2.192`), built around
the existing Sony firmware rather than a full AOSP/LineageOS rebuild.

> **A technically possible modification is NOT automatically a flashable
> one.** Nothing in this repository claims flash-readiness without proof
> and validation on real hardware. See [docs/FLASHING.md](docs/FLASHING.md).

## What's here today

| Component | Status |
|---|---|
| `furaxxz` CLI — doctor, device profile, firmware analyze/extract, fonts inspect/validate/inject, theme/pack create, backup create/restore, security inspect, validate, clean | **IMPLEMENTED** |
| Android app (`apps/furaxxz/`) — category browser, local offline catalog, font preview, wallpaper setting | **IMPLEMENTED** (builds and passes unit tests — see `docs/ENVIRONMENT.md`) |
| Android theme/pack: manifest parsing+validation, apply colors/wallpaper/font | **IMPLEMENTED** (see `docs/MODIFICATIONS.md`) |
| Android theme/pack: icons/sounds/animations/bootAnimation | **PLANNED** — always reported as skipped, never applied |
| Firmware analysis (ZIP/TAR/sparse/ext4/boot.img detection) | **IMPLEMENTED** |
| Font engine (sfnt parsing/validation/metadata) | **IMPLEMENTED** |
| Sony SIN/FTF proprietary format support | **PLANNED** |
| Actual partition repacking (font injection into a live image) | **BLOCKED** (see `docs/MODIFICATIONS.md`) |
| Bootloader unlock / signature bypass | **UNSUPPORTED**, will never be built |

See [docs/MODIFICATIONS.md](docs/MODIFICATIONS.md) for the full,
feature-by-feature status table.

## Quick start (CLI)

```bash
python3 -m pip install pytest   # for running tests; the CLI itself needs no deps
./scripts/furaxxz doctor
./scripts/furaxxz device profile
./scripts/furaxxz firmware analyze path/to/image.zip
./scripts/furaxxz fonts validate path/to/font.ttf
./scripts/furaxxz security inspect
```

Or install it properly:

```bash
pip install -e .
furaxxz doctor
```

## Quick start (Android app)

```bash
cd apps/furaxxz
./gradlew assembleDebug
```

Requires `ANDROID_HOME` pointing at an Android SDK with platform 34 /
build-tools 34.0.0 installed (`sdkmanager "platforms;android-34"
"build-tools;34.0.0"`). Min SDK 26 (Android 8.0), matching the target
device.

## Repository layout

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full module map.
Top-level structure:

```
apps/furaxxz/      Android app (Kotlin, Views/XML, API 26+)
tools/cli/furaxxz/  Python CLI implementation
scripts/furaxxz     Zero-install wrapper for the CLI
catalog/            Local personalization catalog (fonts/wallpapers/themes/...)
firmware/           Firmware input/extraction/output working directories
lab/                Offline modification lab (never touches a real device)
profiles/           Device/user profiles (stock/furax/minimal/custom)
tests/              pytest suite for the CLI
docs/               Architecture, firmware, bootloader, flashing, security, catalog, environment
```

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/FIRMWARE.md](docs/FIRMWARE.md)
- [docs/BOOTLOADER.md](docs/BOOTLOADER.md)
- [docs/FLASHING.md](docs/FLASHING.md)
- [docs/MODIFICATIONS.md](docs/MODIFICATIONS.md)
- [docs/CATALOG.md](docs/CATALOG.md)
- [docs/SECURITY.md](docs/SECURITY.md)
- [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md)

## Testing

```bash
python3 -m pytest -v          # CLI: 50 tests — fonts, firmware, hashing, backup, theme/pack, CLI, security
cd apps/furaxxz && ./gradlew testDebugUnitTest   # Android: 34 JVM unit tests — model, JSON parser, theme/pack manifests
```

No test modifies a real firmware image or touches a real device; all
firmware/backup tests operate on synthetic fixtures in `tmp_path`, and the
Android theme/pack unit tests are pure-Kotlin manifest parsing (no
Android framework, no emulator/device required).

## License

MIT — see [LICENSE](LICENSE).
