package com.furax.furaxxz.engine.pack

import android.content.Context
import android.util.Log
import com.furax.furaxxz.engine.theme.ThemeManager
import com.furax.furaxxz.engine.theme.ThemeManifest
import com.furax.furaxxz.engine.theme.ThemeTargetViews
import java.io.IOException

/**
 * Pack engine for the Android app.
 *
 * IMPLEMENTED: loading + validating a pack manifest, applying its `font`,
 * `wallpaper`, and `colors` components by delegating to [ThemeManager]
 * (a pack is applied as a one-off synthetic theme built from its
 * components — no logic is duplicated).
 *
 * PLANNED: `icons`, `sounds`, `bootAnimation` — always reported in
 * [PackApplyResult.skippedComponents], never silently applied.
 */
class PackManager(context: Context) {

    private val assets = context.assets
    private val themeManager = ThemeManager(context)

    fun loadFromAssets(fileName: String): PackManifest {
        val json = try {
            assets.open("catalog/packs/$fileName").bufferedReader().use { it.readText() }
        } catch (e: IOException) {
            throw PackManifestError("Pack asset not found: catalog/packs/$fileName")
        }
        return PackManifestParser.parse(json)
    }

    fun apply(manifest: PackManifest, targets: ThemeTargetViews): PackApplyResult {
        val syntheticTheme = ThemeManifest(
            schemaVersion = manifest.schemaVersion,
            name = manifest.name,
            version = manifest.version,
            colors = manifest.colors ?: emptyMap(),
            wallpaper = manifest.wallpaper,
            font = manifest.font,
        )

        val themeResult = themeManager.apply(syntheticTheme, targets)

        val applied = mutableListOf<String>()
        val skipped = mutableListOf<String>()

        if (manifest.colors != null) {
            (if (themeResult.colorsApplied) applied else skipped).add("colors")
        }
        if (manifest.wallpaper != null) {
            (if (themeResult.wallpaperApplied) applied else skipped).add("wallpaper")
        }
        if (manifest.font != null) {
            (if (themeResult.fontApplied) applied else skipped).add("font")
        }
        if (manifest.icons != null) skipped.add("icons — PLANNED, not implemented")
        if (manifest.sounds != null) skipped.add("sounds — PLANNED, not implemented")
        if (manifest.bootAnimation != null) skipped.add("bootAnimation — PLANNED, not implemented")

        Log.i(TAG, "Applied pack '${manifest.name}': applied=$applied skipped=$skipped")
        return PackApplyResult(applied, skipped)
    }

    companion object {
        private const val TAG = "PackManager"
    }
}
