package com.furax.furaxxz.engine

import android.content.Context
import android.util.Log
import com.furax.furaxxz.engine.pack.PackManager
import com.furax.furaxxz.engine.theme.ThemeManager

/**
 * Central orchestrator for FuraxXZ personalization.
 *
 * v0.1 status: [catalog], [fonts], [wallpapers], [themes], and [packs]
 * are IMPLEMENTED. Icon/Sound/Animation managers described in the
 * project roadmap remain PLANNED — deliberately absent rather than
 * stubbed with fake behavior. [themes] and [packs] report their own
 * PLANNED sub-components (icons/sounds/animations) per-apply rather than
 * silently skipping them — see docs/MODIFICATIONS.md.
 */
class PersonalizationEngine(private val context: Context) {

    val catalog = CatalogRepository(context)
    val fonts = FontManager()
    val wallpapers = WallpaperManager(context)
    val themes = ThemeManager(context)
    val packs = PackManager(context)

    fun log(action: String, detail: String) {
        Log.i(TAG, "[$action] $detail")
    }

    companion object {
        private const val TAG = "PersonalizationEngine"
    }
}
