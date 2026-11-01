package com.furax.furaxxz.launcher

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ResolveInfo
import android.util.Log
import java.io.IOException

/**
 * Real app drawer data source: queries PackageManager for every activity
 * that declares itself launchable (ACTION_MAIN + CATEGORY_LAUNCHER) —
 * exactly what every other Android launcher does. Icons come from the
 * bundled icon pack when overridden, otherwise from the app's own real
 * icon via PackageManager — never a placeholder.
 */
class InstalledAppsRepository(private val context: Context) {

    private val packageManager = context.packageManager
    private val iconPack: IconPackManifest? = loadBundledIconPack()

    private fun loadBundledIconPack(): IconPackManifest? {
        return try {
            val json = context.assets.open("catalog/icons/pack.json")
                .bufferedReader().use { it.readText() }
            IconPackParser.parse(json)
        } catch (e: IOException) {
            Log.i(TAG, "No bundled icon pack at catalog/icons/pack.json")
            null
        } catch (e: IconPackError) {
            Log.e(TAG, "Bundled icon pack is malformed: ${e.message}")
            null
        }
    }

    fun listLaunchableApps(): List<LauncherApp> {
        val intent = Intent(Intent.ACTION_MAIN).apply { addCategory(Intent.CATEGORY_LAUNCHER) }
        @Suppress("DEPRECATION") // flags=0 overload: correct, minSdk-26-compatible form
        val resolved: List<ResolveInfo> = packageManager.queryIntentActivities(intent, 0)

        return resolved
            .map { info -> toLauncherApp(info) }
            .sortedBy { it.label.lowercase() }
    }

    private fun toLauncherApp(info: ResolveInfo): LauncherApp {
        val packageName = info.activityInfo.packageName
        val label = info.loadLabel(packageManager).toString()
        val icon = resolveIcon(packageName, info)
        return LauncherApp(
            label = label,
            packageName = packageName,
            activityClassName = info.activityInfo.name,
            icon = icon,
        )
    }

    private fun resolveIcon(packageName: String, info: ResolveInfo) =
        iconPack?.let { pack ->
            IconPackResolver.resolve(pack, packageName)?.let { drawableName ->
                loadOwnDrawable(drawableName)
            }
        } ?: info.loadIcon(packageManager)

    private fun loadOwnDrawable(drawableName: String) =
        try {
            val resId = context.resources.getIdentifier(drawableName, "drawable", context.packageName)
            if (resId != 0) context.resources.getDrawable(resId, context.theme) else null
        } catch (e: android.content.res.Resources.NotFoundException) {
            Log.w(TAG, "Icon pack references missing drawable '$drawableName'")
            null
        }

    fun launchIntentFor(app: LauncherApp): Intent =
        Intent(Intent.ACTION_MAIN).apply {
            addCategory(Intent.CATEGORY_LAUNCHER)
            setClassName(app.packageName, app.activityClassName)
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }

    companion object {
        private const val TAG = "InstalledAppsRepository"
    }
}
