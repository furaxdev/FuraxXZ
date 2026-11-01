package com.furax.furaxxz.launcher

/**
 * An icon pack is a flat map of {packageName: drawableResourceName}. It
 * only overrides apps it explicitly lists — every other installed app
 * keeps rendering its own real icon via PackageManager. This mirrors the
 * `theme.json`/`pack.json` philosophy from `engine/theme`/`engine/pack`:
 * declared-and-applied, never a silent blanket replacement.
 */
data class IconPackManifest(
    val name: String,
    val overrides: Map<String, String>,
)
