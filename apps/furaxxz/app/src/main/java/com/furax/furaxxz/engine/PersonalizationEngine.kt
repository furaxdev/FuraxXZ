package com.furax.furaxxz.engine

import android.content.Context
import android.util.Log

/**
 * Central orchestrator for FuraxXZ personalization.
 *
 * v0.1 status: [catalog], [fonts] and [wallpapers] are IMPLEMENTED and
 * functional. Theme/Icon/Sound/Animation/Pack managers described in the
 * project roadmap are PLANNED — deliberately absent rather than stubbed
 * with fake behavior, per project quality rules. Wire them in here once
 * each has a real, tested implementation (see docs/ARCHITECTURE.md).
 */
class PersonalizationEngine(private val context: Context) {

    val catalog = CatalogRepository(context)
    val fonts = FontManager()
    val wallpapers = WallpaperManager(context)

    fun log(action: String, detail: String) {
        Log.i(TAG, "[$action] $detail")
    }

    companion object {
        private const val TAG = "PersonalizationEngine"
    }
}
