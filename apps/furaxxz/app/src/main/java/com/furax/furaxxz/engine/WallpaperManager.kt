package com.furax.furaxxz.engine

import android.app.WallpaperManager as AndroidWallpaperManager
import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.Log
import java.io.File
import java.io.IOException

/** Wallpaper engine: preview, local caching, and actually setting the
 * device wallpaper via the real Android WallpaperManager API. */
class WallpaperManager(private val context: Context) {

    class WallpaperError(message: String, cause: Throwable? = null) : Exception(message, cause)

    private val cacheDir: File
        get() = File(context.cacheDir, "wallpapers").apply { mkdirs() }

    /** Decode a wallpaper file to a preview Bitmap without loading it at full
     * resolution into memory (uses inSampleSize). Returns null if unreadable. */
    fun preview(file: File, maxDimension: Int = 512): Bitmap? {
        if (!file.isFile) return null
        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeFile(file.absolutePath, bounds)
        if (bounds.outWidth <= 0 || bounds.outHeight <= 0) return null

        var sample = 1
        while (bounds.outWidth / sample > maxDimension || bounds.outHeight / sample > maxDimension) {
            sample *= 2
        }
        val opts = BitmapFactory.Options().apply { inSampleSize = sample }
        return BitmapFactory.decodeFile(file.absolutePath, opts)
    }

    /** Copy a wallpaper into the app's local cache. Returns the cached file. */
    fun cacheLocally(sourceFile: File): File {
        if (!sourceFile.isFile) throw WallpaperError("Source wallpaper not found: $sourceFile")
        val dest = File(cacheDir, sourceFile.name)
        try {
            sourceFile.copyTo(dest, overwrite = true)
        } catch (e: IOException) {
            throw WallpaperError("Failed to cache wallpaper locally", e)
        }
        return dest
    }

    /** Actually set the device's home-screen wallpaper. Requires the caller
     * to hold SET_WALLPAPER (granted automatically to apps, not a runtime
     * permission), and can fail on devices that restrict it. */
    fun setAsWallpaper(file: File) {
        val bitmap = preview(file, maxDimension = 4096)
            ?: throw WallpaperError("Could not decode image: $file")
        try {
            AndroidWallpaperManager.getInstance(context).setBitmap(bitmap)
        } catch (e: IOException) {
            throw WallpaperError("System rejected the wallpaper", e)
        } finally {
            if (!bitmap.isRecycled) bitmap.recycle()
        }
        Log.i(TAG, "Wallpaper set from ${file.name}")
    }

    fun clearCache() {
        cacheDir.listFiles()?.forEach { it.delete() }
    }

    companion object {
        private const val TAG = "WallpaperManager"
    }
}
