package com.furax.furaxxz.model

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class CategoryTest {

    @Test
    fun `all returns all seven categories from the spec`() {
        val names = Category.all().map { it.displayName }
        assertEquals(
            listOf("Fonts", "Wallpapers", "Themes", "Icons", "Sounds", "Animations", "Packs"),
            names,
        )
    }

    @Test
    fun `storage dir names are lowercase and unique`() {
        val dirs = Category.all().map { it.storageDirName }
        assertEquals(dirs.size, dirs.toSet().size)
        assertTrue(dirs.all { it == it.lowercase() })
    }

    @Test
    fun `catalog item defaults to not installed`() {
        val item = CatalogItem(id = "a", name = "Test", category = Category.FONTS)
        assertTrue(!item.installed)
    }
}
