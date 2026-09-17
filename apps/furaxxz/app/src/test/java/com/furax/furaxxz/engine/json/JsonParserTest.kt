package com.furax.furaxxz.engine.json

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Test

class JsonParserTest {

    @Test
    fun `parses an empty object`() {
        val result = JsonParser.parse("{}")
        assertEquals(JsonValue.Obj(emptyMap()), result)
    }

    @Test
    fun `parses an empty array`() {
        val result = JsonParser.parse("[]")
        assertEquals(JsonValue.Arr(emptyList()), result)
    }

    @Test
    fun `parses flat object with string number bool null values`() {
        val result = JsonParser.parse(
            """{"name": "furax", "count": 3, "ok": true, "bad": false, "nothing": null}"""
        )
        val obj = (result as JsonValue.Obj).entries
        assertEquals(JsonValue.Str("furax"), obj["name"])
        assertEquals(JsonValue.Num(3.0), obj["count"])
        assertEquals(JsonValue.Bool(true), obj["ok"])
        assertEquals(JsonValue.Bool(false), obj["bad"])
        assertEquals(JsonValue.Null, obj["nothing"])
    }

    @Test
    fun `parses nested objects and arrays`() {
        val result = JsonParser.parse(
            """{"colors": {"primary": "#7C4DFF"}, "tags": ["a", "b", "c"]}"""
        )
        val obj = (result as JsonValue.Obj).entries
        val colors = obj.stringMapField("colors")
        assertEquals(mapOf("primary" to "#7C4DFF"), colors)
        val tags = obj["tags"]!!.asArrayOrNull()!!.map { (it as JsonValue.Str).value }
        assertEquals(listOf("a", "b", "c"), tags)
    }

    @Test
    fun `parses numbers with decimals negatives and exponents`() {
        val result = JsonParser.parse("""[1, -2, 3.5, -3.5, 1e3, 1.5e-2]""")
        val nums = (result as JsonValue.Arr).items.map { (it as JsonValue.Num).value }
        assertEquals(listOf(1.0, -2.0, 3.5, -3.5, 1000.0, 0.015), nums)
    }

    @Test
    fun `parses string escapes including unicode`() {
        val result = JsonParser.parse(""""line1\nline2\t\"quoted\"A"""")
        assertEquals("line1\nline2\t\"quoted\"A", (result as JsonValue.Str).value)
    }

    @Test
    fun `whitespace around values is tolerated`() {
        val result = JsonParser.parse("  \n  { \"a\" : 1 }  \n ")
        assertEquals(JsonValue.Num(1.0), (result as JsonValue.Obj).entries["a"])
    }

    @Test
    fun `rejects trailing content after a valid value`() {
        assertThrowsParseException { JsonParser.parse("{}garbage") }
    }

    @Test
    fun `rejects unterminated object`() {
        assertThrowsParseException { JsonParser.parse("""{"a": 1""") }
    }

    @Test
    fun `rejects unterminated string`() {
        assertThrowsParseException { JsonParser.parse(""""unterminated""") }
    }

    @Test
    fun `rejects invalid escape sequence`() {
        assertThrowsParseException { JsonParser.parse(""""bad\qescape"""") }
    }

    @Test
    fun `rejects malformed number`() {
        assertThrowsParseException { JsonParser.parse("--1") }
    }

    @Test
    fun `rejects empty input`() {
        assertThrowsParseException { JsonParser.parse("") }
    }

    @Test
    fun `rejects unquoted object key`() {
        assertThrowsParseException { JsonParser.parse("{a: 1}") }
    }

    private fun assertThrowsParseException(block: () -> Unit) {
        try {
            block()
            fail("Expected JsonParseException")
        } catch (e: JsonParseException) {
            assertTrue(e.message?.isNotBlank() == true)
        }
    }
}
