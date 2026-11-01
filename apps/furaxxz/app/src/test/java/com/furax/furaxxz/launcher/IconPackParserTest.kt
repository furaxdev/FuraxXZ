package com.furax.furaxxz.launcher

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Test

class IconPackParserTest {

    @Test
    fun `parses a valid icon pack manifest`() {
        val json = """
            {
              "name": "Furax Demo Icons",
              "overrides": {
                "com.android.settings": "ic_override_gear",
                "com.example.app": "ic_override_example"
              }
            }
        """.trimIndent()

        val manifest = IconPackParser.parse(json)

        assertEquals("Furax Demo Icons", manifest.name)
        assertEquals("ic_override_gear", manifest.overrides["com.android.settings"])
        assertEquals("ic_override_example", manifest.overrides["com.example.app"])
    }

    @Test
    fun `rejects missing name`() {
        assertThrows(IconPackError::class.java) {
            IconPackParser.parse("""{"overrides": {"a.b": "c"}}""")
        }
    }

    @Test
    fun `rejects missing overrides`() {
        assertThrows(IconPackError::class.java) {
            IconPackParser.parse("""{"name": "x"}""")
        }
    }

    @Test
    fun `accepts an empty overrides map`() {
        // Valid but pointless — same spirit as an empty theme catalog:
        // not an error, just nothing to override yet.
        val manifest = IconPackParser.parse("""{"name": "x", "overrides": {}}""")
        assertEquals(emptyMap<String, String>(), manifest.overrides)
    }

    @Test
    fun `rejects malformed json`() {
        assertThrows(IconPackError::class.java) {
            IconPackParser.parse("not json")
        }
    }

    @Test
    fun `rejects a json array as the root`() {
        assertThrows(IconPackError::class.java) {
            IconPackParser.parse("[]")
        }
    }
}
