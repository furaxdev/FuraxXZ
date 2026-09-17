package com.furax.furaxxz.engine.pack

/**
 * Mirrors the pack schema documented in `docs/CATALOG.md` and produced by
 * `furaxxz pack create` (`tools/cli/furaxxz/pack.py`).
 *
 * `components` keeps the raw string values FuraxXZ actually knows how to
 * apply today (font/wallpaper file names, a colors map). `icons`,
 * `sounds`, and `bootAnimation` are read out but never silently dropped:
 * [PackApplier] reports them as explicitly skipped (PLANNED), never as
 * applied.
 */
data class PackManifest(
    val schemaVersion: Int,
    val name: String,
    val version: String,
    val font: String?,
    val wallpaper: String?,
    val colors: Map<String, String>?,
    val icons: String?,
    val sounds: String?,
    val bootAnimation: String?,
) {
    /** Component keys present in this pack, in the order the schema defines them. */
    fun declaredComponents(): List<String> = buildList {
        if (font != null) add("font")
        if (wallpaper != null) add("wallpaper")
        if (colors != null) add("colors")
        if (icons != null) add("icons")
        if (sounds != null) add("sounds")
        if (bootAnimation != null) add("bootAnimation")
    }
}
