package com.furax.furaxxz.engine

import com.furax.furaxxz.model.CatalogItem
import com.furax.furaxxz.model.Category

/**
 * PLANNED — not implemented.
 *
 * Placeholder for a future remote catalog (a hosted index the app could
 * optionally sync). Intentionally unimplemented: the app must work fully
 * offline by default (see project rule in docs/CATALOG.md), and no network
 * client/endpoint has been designed or reviewed yet. Wiring this in requires:
 *  - a versioned remote manifest schema compatible with [CatalogItem]
 *  - explicit user opt-in (never fetched implicitly)
 *  - checksum verification of any downloaded asset before use
 *
 * Calling [listItems] currently returns an empty list rather than throwing,
 * so a [CatalogRepository] can merge it in later without special-casing.
 */
class RemoteCatalogSource : CatalogSource {
    override fun listItems(category: Category): List<CatalogItem> = emptyList()
}
