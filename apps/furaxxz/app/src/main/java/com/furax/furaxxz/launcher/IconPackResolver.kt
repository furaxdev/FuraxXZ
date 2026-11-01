package com.furax.furaxxz.launcher

/** Pure lookup logic, separated from drawable resolution (which needs
 * Android's Resources/PackageManager) so it's directly unit-testable. */
object IconPackResolver {

    /** The drawable resource name to use for `packageName`, or null if
     * this icon pack doesn't override it — callers must fall back to the
     * app's own real icon, never render a blank/placeholder in that case. */
    fun resolve(manifest: IconPackManifest, packageName: String): String? =
        manifest.overrides[packageName]
}
