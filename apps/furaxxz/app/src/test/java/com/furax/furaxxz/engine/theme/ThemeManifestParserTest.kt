package com.furax.furaxxz.engine.theme

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Test

class ThemeManifestParserTest {

    @Test
    fun `parses a full theme manifest`() {
        val json = """
            {
              "schemaVersion": 1,
              "name": "Furax Dark",
              "version": "0.1.0",
              "colors": {"primary": "#7C4DFF", "background": "#0E0E12"},
              "wallpaper": "wall.jpg",
              "font": "Inter.ttf"
            }
        """.trimIndent()

        val manifest = ThemeManifestParser.parse(json)

        assertEquals("Furax Dark", manifest.name)
        assertEquals("0.1.0", manifest.version)
        assertEquals(mapOf("primary" to "#7C4DFF", "background" to "#0E0E12"), manifest.colors)
        assertEquals("wall.jpg", manifest.wallpaper)
        assertEquals("Inter.ttf", manifest.font)
        assertNull(manifest.icons)
    }

    @Test
    fun `defaults schemaVersion to 1 when absent`() {
        val manifest = ThemeManifestParser.parse(
            """{"name": "x", "version": "1", "colors": {"primary": "#000000"}}"""
        )
        assertEquals(1, manifest.schemaVersion)
    }

    @Test
    fun `rejects missing name`() {
        assertThrows(ThemeManifestError::class.java) {
            ThemeManifestParser.parse("""{"version": "1", "colors": {"primary": "#000000"}}""")
        }
    }

    @Test
    fun `rejects missing version`() {
        assertThrows(ThemeManifestError::class.java) {
            ThemeManifestParser.parse("""{"name": "x", "colors": {"primary": "#000000"}}""")
        }
    }

    @Test
    fun `rejects missing colors`() {
        assertThrows(ThemeManifestError::class.java) {
            ThemeManifestParser.parse("""{"name": "x", "version": "1"}""")
        }
    }

    @Test
    fun `rejects empty colors`() {
        assertThrows(ThemeManifestError::class.java) {
            ThemeManifestParser.parse("""{"name": "x", "version": "1", "colors": {}}""")
        }
    }

    @Test
    fun `rejects non-hex color value`() {
        assertThrows(ThemeManifestError::class.java) {
            ThemeManifestParser.parse("""{"name": "x", "version": "1", "colors": {"primary": "purple"}}""")
        }
    }

    @Test
    fun `rejects short hex color missing hash`() {
        assertThrows(ThemeManifestError::class.java) {
            ThemeManifestParser.parse("""{"name": "x", "version": "1", "colors": {"primary": "7C4DFF"}}""")
        }
    }

    @Test
    fun `rejects malformed json`() {
        assertThrows(ThemeManifestError::class.java) {
            ThemeManifestParser.parse("not json at all")
        }
    }

    @Test
    fun `rejects a json array as the root`() {
        assertThrows(ThemeManifestError::class.java) {
            ThemeManifestParser.parse("[]")
        }
    }
}
