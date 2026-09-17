package com.furax.furaxxz.engine

import android.content.Context
import android.util.Log
import com.furax.furaxxz.model.CatalogItem
import com.furax.furaxxz.model.Category
import org.json.JSONArray
import java.io.IOException

/**
 * Reads the catalog from `assets/catalog/<category>/manifest.json`, an
 * array of `{id, name, author, license, file}` objects. Missing or empty
 * manifests are not errors — the category is simply shown empty; the app
 * must never require network access to function.
 */
class LocalCatalogSource(private val context: Context) : CatalogSource {

    override fun listItems(category: Category): List<CatalogItem> {
        val path = "catalog/${category.storageDirName}/manifest.json"
        val json = try {
            context.assets.open(path).bufferedReader().use { it.readText() }
        } catch (e: IOException) {
            Log.i(TAG, "No local manifest at $path (empty category)")
            return emptyList()
        }

        return try {
            val array = JSONArray(json)
            (0 until array.length()).map { i ->
                val obj = array.getJSONObject(i)
                CatalogItem(
                    id = obj.getString("id"),
                    name = obj.getString("name"),
                    category = category,
                    author = obj.optString("author").ifBlank { null },
                    license = obj.optString("license").ifBlank { null },
                    fileName = obj.optString("file").ifBlank { null },
                )
            }
        } catch (e: org.json.JSONException) {
            Log.e(TAG, "Malformed manifest at $path: ${e.message}")
            emptyList()
        }
    }

    companion object {
        private const val TAG = "LocalCatalogSource"
    }
}
