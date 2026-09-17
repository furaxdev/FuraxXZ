package com.furax.furaxxz.engine

import android.content.Context
import com.furax.furaxxz.model.CatalogItem
import com.furax.furaxxz.model.Category

/** Merges catalog sources, local-first. The remote source is currently a
 * no-op placeholder (see [RemoteCatalogSource]) so this always works offline. */
class CatalogRepository(context: Context) {
    private val local: CatalogSource = LocalCatalogSource(context)
    private val remote: CatalogSource = RemoteCatalogSource()

    fun listItems(category: Category): List<CatalogItem> {
        val localItems = local.listItems(category)
        val localIds = localItems.map { it.id }.toSet()
        val remoteItems = remote.listItems(category).filterNot { it.id in localIds }
        return localItems + remoteItems
    }
}
