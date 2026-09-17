package com.furax.furaxxz.engine.theme

import android.content.Context
import android.graphics.Color
import android.util.Log
import android.view.View
import android.widget.TextView
import com.furax.furaxxz.engine.FontManager
import com.furax.furaxxz.engine.WallpaperManager
import java.io.File
import java.io.IOException

/**
 * Theme engine for the Android app.
 *
 * IMPLEMENTED: loading + validating a theme manifest, and applying its
 * `colors` (recolors the views handed to it — nothing outside this app),
 * `wallpaper` (delegates to the real [WallpaperManager]), and `font`
 * (delegates to the real [FontManager]) components, if the referenced
 * asset is actually bundled under `assets/catalog/`.
 *
 * PLANNED: `icons`, `sounds`, `animations` — see docs/MODIFICATIONS.md.
 * [apply] always reports these in [ThemeApplyResult.skipped] rather than
 * pretending they were applied.
 */
class ThemeManager(private val context: Context) {

    private val fontManager = FontManager()
    private val wallpaperManager = WallpaperManager(context)

    /** Load and validate `assets/catalog/themes/<fileName>`. */
    fun loadFromAssets(fileName: String): ThemeManifest {
        val json = try {
            context.assets.open("catalog/themes/$fileName").bufferedReader().use { it.readText() }
        } catch (e: IOException) {
            throw ThemeManifestError("Theme asset not found: catalog/themes/$fileName")
        }
        return ThemeManifestParser.parse(json)
    }

    /** Apply what this manifest declares and this engine actually supports. */
    fun apply(manifest: ThemeManifest, targets: ThemeTargetViews): ThemeApplyResult {
        val skipped = mutableListOf<String>()

        val colorsApplied = applyColors(manifest.colors, targets)

        val wallpaperApplied = manifest.wallpaper?.let { fileName ->
            applyWallpaperAsset(fileName)
        } ?: false
        if (manifest.wallpaper != null && !wallpaperApplied) {
            skipped.add("wallpaper (declared as '${manifest.wallpaper}' but not bundled in assets/catalog/wallpapers/)")
        }

        val fontApplied = manifest.font?.let { fileName ->
            applyFontAsset(fileName, targets.accentTexts)
        } ?: false
        if (manifest.font != null && !fontApplied) {
            skipped.add("font (declared as '${manifest.font}' but not bundled in assets/catalog/fonts/)")
        }

        if (manifest.icons != null) skipped.add("icons — PLANNED, not implemented (see docs/MODIFICATIONS.md)")
        if (manifest.sounds != null) skipped.add("sounds — PLANNED, not implemented (see docs/MODIFICATIONS.md)")
        if (manifest.animations != null) {
            skipped.add("animations — PLANNED, not implemented (see docs/MODIFICATIONS.md)")
        }

        Log.i(TAG, "Applied theme '${manifest.name}': colors=$colorsApplied wallpaper=$wallpaperApplied font=$fontApplied skipped=$skipped")
        return ThemeApplyResult(colorsApplied, wallpaperApplied, fontApplied, skipped)
    }

    private fun applyColors(colors: Map<String, String>, targets: ThemeTargetViews): Boolean {
        if (colors.isEmpty()) return false
        val background = colors["background"]
        val primary = colors["primary"]

        var applied = false
        if (background != null) {
            runCatching { Color.parseColor(background) }.getOrNull()?.let {
                targets.background?.setBackgroundColor(it)
                applied = true
            }
        }
        if (primary != null) {
            runCatching { Color.parseColor(primary) }.getOrNull()?.let { color ->
                targets.accentTexts.forEach { it.setTextColor(color) }
                if (targets.accentTexts.isNotEmpty()) applied = true
            }
        }
        return applied
    }

    private fun applyWallpaperAsset(fileName: String): Boolean {
        val file = copyAssetToCache("catalog/wallpapers/$fileName", fileName) ?: return false
        return try {
            wallpaperManager.setAsWallpaper(file)
            true
        } catch (e: WallpaperManager.WallpaperError) {
            Log.w(TAG, "Wallpaper asset present but could not be applied: ${e.message}")
            false
        }
    }

    private fun applyFontAsset(fileName: String, targetTexts: List<TextView>): Boolean {
        if (targetTexts.isEmpty()) return false
        val file = copyAssetToCache("catalog/fonts/$fileName", fileName) ?: return false
        return try {
            fontManager.applyToView(file, *targetTexts.toTypedArray())
            true
        } catch (e: FontManager.FontError) {
            Log.w(TAG, "Font asset present but invalid: ${e.message}")
            false
        }
    }

    private fun copyAssetToCache(assetPath: String, outputName: String): File? {
        return try {
            context.assets.open(assetPath).use { input ->
                val dest = File(context.cacheDir, "theme-assets").apply { mkdirs() }
                    .resolve(outputName)
                dest.outputStream().use { output -> input.copyTo(output) }
                dest
            }
        } catch (e: IOException) {
            null
        }
    }

    companion object {
        private const val TAG = "ThemeManager"
    }
}
