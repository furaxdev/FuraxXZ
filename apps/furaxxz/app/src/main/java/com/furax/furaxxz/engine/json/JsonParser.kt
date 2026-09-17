package com.furax.furaxxz.engine.json

class JsonParseException(message: String) : Exception(message)

/**
 * A small recursive-descent JSON parser (RFC 8259), scoped to what
 * FuraxXZ's theme/pack manifests need. No external dependency, and — see
 * [JsonValue] — that's the point: it must run in a plain JVM unit test.
 */
object JsonParser {

    fun parse(text: String): JsonValue {
        val reader = Reader(text)
        reader.skipWhitespace()
        val value = reader.readValue()
        reader.skipWhitespace()
        if (!reader.atEnd()) {
            throw JsonParseException("Unexpected trailing content at offset ${reader.pos}")
        }
        return value
    }

    private class Reader(private val text: String) {
        var pos = 0
            private set

        fun atEnd() = pos >= text.length

        private fun peek(): Char {
            if (atEnd()) throw JsonParseException("Unexpected end of input")
            return text[pos]
        }

        private fun advance(): Char = peek().also { pos++ }

        fun skipWhitespace() {
            while (!atEnd() && text[pos].isWhitespace()) pos++
        }

        private fun expect(c: Char) {
            if (atEnd() || text[pos] != c) {
                throw JsonParseException("Expected '$c' at offset $pos")
            }
            pos++
        }

        fun readValue(): JsonValue {
            skipWhitespace()
            return when (peek()) {
                '{' -> readObject()
                '[' -> readArray()
                '"' -> JsonValue.Str(readString())
                't', 'f' -> readBoolean()
                'n' -> readNull()
                else -> readNumber()
            }
        }

        private fun readObject(): JsonValue.Obj {
            expect('{')
            val entries = LinkedHashMap<String, JsonValue>()
            skipWhitespace()
            if (!atEnd() && peek() == '}') {
                pos++
                return JsonValue.Obj(entries)
            }
            while (true) {
                skipWhitespace()
                if (peek() != '"') throw JsonParseException("Expected string key at offset $pos")
                val key = readString()
                skipWhitespace()
                expect(':')
                val value = readValue()
                entries[key] = value
                skipWhitespace()
                when (advance()) {
                    ',' -> continue
                    '}' -> break
                    else -> throw JsonParseException("Expected ',' or '}' at offset ${pos - 1}")
                }
            }
            return JsonValue.Obj(entries)
        }

        private fun readArray(): JsonValue.Arr {
            expect('[')
            val items = mutableListOf<JsonValue>()
            skipWhitespace()
            if (!atEnd() && peek() == ']') {
                pos++
                return JsonValue.Arr(items)
            }
            while (true) {
                items.add(readValue())
                skipWhitespace()
                when (advance()) {
                    ',' -> continue
                    ']' -> break
                    else -> throw JsonParseException("Expected ',' or ']' at offset ${pos - 1}")
                }
            }
            return JsonValue.Arr(items)
        }

        private fun readString(): String {
            expect('"')
            val sb = StringBuilder()
            while (true) {
                if (atEnd()) throw JsonParseException("Unterminated string")
                val c = advance()
                when {
                    c == '"' -> return sb.toString()
                    c == '\\' -> {
                        if (atEnd()) throw JsonParseException("Unterminated escape sequence")
                        when (val esc = advance()) {
                            '"' -> sb.append('"')
                            '\\' -> sb.append('\\')
                            '/' -> sb.append('/')
                            'b' -> sb.append('\b')
                            'f' -> sb.append('')
                            'n' -> sb.append('\n')
                            'r' -> sb.append('\r')
                            't' -> sb.append('\t')
                            'u' -> {
                                if (pos + 4 > text.length) throw JsonParseException("Truncated \\u escape")
                                val hex = text.substring(pos, pos + 4)
                                pos += 4
                                sb.append(hex.toInt(16).toChar())
                            }
                            else -> throw JsonParseException("Invalid escape '\\$esc' at offset ${pos - 1}")
                        }
                    }
                    c.code < 0x20 -> throw JsonParseException("Unescaped control character in string")
                    else -> sb.append(c)
                }
            }
        }

        private fun readBoolean(): JsonValue.Bool {
            return when {
                text.startsWith("true", pos) -> { pos += 4; JsonValue.Bool(true) }
                text.startsWith("false", pos) -> { pos += 5; JsonValue.Bool(false) }
                else -> throw JsonParseException("Invalid literal at offset $pos")
            }
        }

        private fun readNull(): JsonValue {
            if (text.startsWith("null", pos)) {
                pos += 4
                return JsonValue.Null
            }
            throw JsonParseException("Invalid literal at offset $pos")
        }

        private fun readNumber(): JsonValue.Num {
            val start = pos
            if (!atEnd() && peek() == '-') pos++
            if (atEnd() || !peek().isDigit()) throw JsonParseException("Invalid number at offset $pos")
            while (!atEnd() && peek().isDigit()) pos++
            if (!atEnd() && peek() == '.') {
                pos++
                if (atEnd() || !peek().isDigit()) throw JsonParseException("Invalid number at offset $pos")
                while (!atEnd() && peek().isDigit()) pos++
            }
            if (!atEnd() && (peek() == 'e' || peek() == 'E')) {
                pos++
                if (!atEnd() && (peek() == '+' || peek() == '-')) pos++
                if (atEnd() || !peek().isDigit()) throw JsonParseException("Invalid number exponent at offset $pos")
                while (!atEnd() && peek().isDigit()) pos++
            }
            val token = text.substring(start, pos)
            return JsonValue.Num(token.toDouble())
        }
    }
}
