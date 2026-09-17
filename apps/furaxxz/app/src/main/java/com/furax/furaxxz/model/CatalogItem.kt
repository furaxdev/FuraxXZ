package com.furax.furaxxz.model

/** A single installable item inside a category (a font, a wallpaper, ...). */
data class CatalogItem(
    val id: String,
    val name: String,
    val category: Category,
    val author: String? = null,
    val license: String? = null,
    val fileName: String? = null,
    val installed: Boolean = false,
)
