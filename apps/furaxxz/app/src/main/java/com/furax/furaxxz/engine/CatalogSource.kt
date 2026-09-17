package com.furax.furaxxz.engine

import com.furax.furaxxz.model.CatalogItem
import com.furax.furaxxz.model.Category

/** A source the catalog can be read from. Local-first: the app must work
 * fully offline; a remote source is additive, never required. */
interface CatalogSource {
    fun listItems(category: Category): List<CatalogItem>
}
