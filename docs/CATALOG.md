# Catalog

## Local-first, always

The catalog (`catalog/` at the repo root, and `assets/catalog/` bundled
into the Android app) must work with zero network access. The Android
`CatalogRepository` merges a `LocalCatalogSource` (reads
`assets/catalog/<category>/manifest.json`) with a `RemoteCatalogSource`
that is currently a documented no-op — see `engine/RemoteCatalogSource.kt`.
Nothing in the app blocks on network I/O.

## Categories

Fonts, Wallpapers, Themes, Icons, Sounds, Animations, Packs — one
directory per category under both `catalog/` (CLI-facing) and
`apps/furaxxz/app/src/main/res` + `assets/catalog/` (app-facing).

## Manifest schema

### Theme (`catalog/themes/<name>/theme.json`)

```json
{
  "schemaVersion": 1,
  "name": "midnight",
  "version": "0.1.0",
  "colors": { "primary": "#7C4DFF", "background": "#0E0E12" },
  "wallpaper": "optional-file-name",
  "icons": "optional",
  "font": "optional",
  "sounds": "optional",
  "animations": "optional"
}
```

Validated by `tools/cli/furaxxz/theme.py::validate_theme`: `name`,
`version`, `colors` required; every color value must be a `#RRGGBB`-style
hex string.

### Pack (`catalog/packs/<name>/pack.json`)

```json
{
  "schemaVersion": 1,
  "name": "furax-dark",
  "version": "0.1.0",
  "components": { "font": "...", "wallpaper": "...", "colors": {...} }
}
```

At least one component is required (`pack.py::validate_pack`).

### Font entry (Android manifest, `assets/catalog/fonts/manifest.json`)

```json
[{ "id": "inter-regular", "name": "Inter", "author": "Google Fonts", "license": "OFL-1.1", "file": "Inter-Regular.ttf" }]
```

## Licensing

Do not bundle or auto-embed wallpapers/fonts without a license that
permits redistribution. The catalog ships empty (`[]` manifests) in this
repo; populating it with real assets is a separate, license-checked step
— not automated here.

## Validating the catalog

```
furaxxz validate
```

Walks every `theme.json`, `pack.json`, and `.ttf`/`.otf` under `catalog/`
and reports problems (schema violations, malformed fonts) with a non-zero
exit code on failure — see `cmd_validate` in
`tools/cli/furaxxz/__main__.py`.
