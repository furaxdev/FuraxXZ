package com.furax.furaxxz.engine.pack

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Test

class PackManifestParserTest {

    @Test
    fun `parses a full pack manifest`() {
        val json = """
            {
              "schemaVersion": 1,
              "name": "Furax Essentials",
              "version": "0.1.0",
              "components": {
                "font": "Inter.ttf",
                "wallpaper": "wall.jpg",
                "colors": {"primary": "#00E5C7"},
                "icons": "furax-icon-pack"
              }
            }
        """.trimIndent()

        val manifest = PackManifestParser.parse(json)

        assertEquals("Furax Essentials", manifest.name)
        assertEquals("Inter.ttf", manifest.font)
        assertEquals("wall.jpg", manifest.wallpaper)
        assertEquals(mapOf("primary" to "#00E5C7"), manifest.colors)
        assertEquals("furax-icon-pack", manifest.icons)
        assertNull(manifest.sounds)
        assertNull(manifest.bootAnimation)
    }

    @Test
    fun `declaredComponents lists only present components in schema order`() {
        val manifest = PackManifestParser.parse(
            """{"name": "x", "version": "1", "components": {"sounds": "s.ogg", "font": "f.ttf"}}"""
        )
        assertEquals(listOf("font", "sounds"), manifest.declaredComponents())
    }

    @Test
    fun `rejects missing components object`() {
        assertThrows(PackManifestError::class.java) {
            PackManifestParser.parse("""{"name": "x", "version": "1"}""")
        }
    }

    @Test
    fun `rejects empty components`() {
        assertThrows(PackManifestError::class.java) {
            PackManifestParser.parse("""{"name": "x", "version": "1", "components": {}}""")
        }
    }

    @Test
    fun `rejects missing name`() {
        assertThrows(PackManifestError::class.java) {
            PackManifestParser.parse("""{"version": "1", "components": {"font": "f.ttf"}}""")
        }
    }

    @Test
    fun `rejects missing version`() {
        assertThrows(PackManifestError::class.java) {
            PackManifestParser.parse("""{"name": "x", "components": {"font": "f.ttf"}}""")
        }
    }

    @Test
    fun `rejects malformed json`() {
        assertThrows(PackManifestError::class.java) {
            PackManifestParser.parse("{not valid")
        }
    }
}
