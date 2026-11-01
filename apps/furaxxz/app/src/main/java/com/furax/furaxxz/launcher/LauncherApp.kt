package com.furax.furaxxz.launcher

import android.graphics.drawable.Drawable

/** A single entry in the app drawer. `icon` is already resolved — either
 * the icon pack override or the app's real icon — so the UI layer never
 * has to know which. */
data class LauncherApp(
    val label: String,
    val packageName: String,
    val activityClassName: String,
    val icon: Drawable,
)
