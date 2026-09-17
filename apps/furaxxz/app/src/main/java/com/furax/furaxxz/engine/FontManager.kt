package com.furax.furaxxz.engine

import android.graphics.Typeface
import android.util.Log
import android.widget.TextView
import java.io.File

/**
 * Font engine for the Android app.
 *
 * What is IMPLEMENTED here: loading a .ttf/.otf as a real [Typeface] and
 * applying it to views within this app (a legitimate, sandboxed operation
 * any app can do). What is NOT implemented: replacing the device's
 * system-wide font. On a locked-bootloader, non-rooted Sony F8331 that
 * requires modifying /system, which this app cannot and will not attempt
 * — see docs/MODIFICATIONS.md and the security gate in the CLI
 * (`furaxxz fonts inject`), which explicitly BLOCKs that path.
 */
class FontManager {

    class FontError(message: String, cause: Throwable? = null) : Exception(message, cause)

    /** Load and validate a font file, returning a usable [Typeface]. */
    fun load(file: File): Typeface {
        if (!file.isFile) throw FontError("Font file not found: $file")
        return try {
            Typeface.createFromFile(file)
        } catch (e: RuntimeException) {
            // Android's Typeface throws RuntimeException for a malformed font.
            throw FontError("Not a valid font file: ${file.name}", e)
        }
    }

    /** Apply a font to this app's own views (in-app preview / theming). */
    fun applyToView(file: File, vararg views: TextView) {
        val typeface = load(file)
        views.forEach { it.typeface = typeface }
        Log.i(TAG, "Applied font ${file.name} to ${views.size} view(s)")
    }

    companion object {
        private const val TAG = "FontManager"
    }
}
