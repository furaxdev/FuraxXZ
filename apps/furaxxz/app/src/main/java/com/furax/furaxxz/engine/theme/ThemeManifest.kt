package com.furax.furaxxz.engine.theme

/**
 * Mirrors the theme schema documented in `docs/CATALOG.md` and produced by
 * `furaxxz theme create` (`tools/cli/furaxxz/theme.py`). Kept in lockstep
 * with the CLI schema deliberately — a theme created on the CLI must be
 * loadable here unchanged.
 */
data class ThemeManifest(
    val schemaVersion: Int,
    val name: String,
    val version: String,
    val colors: Map<String, String>,
    val wallpaper: String? = null,
    val icons: String? = null,
    val font: String? = null,
    val sounds: String? = null,
    val animations: String? = null,
)
