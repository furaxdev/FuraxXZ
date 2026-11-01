package com.furax.furaxxz.launcher

import com.furax.furaxxz.engine.json.JsonParseException
import com.furax.furaxxz.engine.json.JsonParser
import com.furax.furaxxz.engine.json.asObjectOrNull
import com.furax.furaxxz.engine.json.stringField
import com.furax.furaxxz.engine.json.stringMapField

class IconPackError(message: String) : Exception(message)

/** Parses an icon pack JSON document: `{"name": "...", "overrides": {"<packageName>": "<drawableName>"}}`.
 * Pure Kotlin, no Android dependency — same reasoning as
 * `engine/theme/ThemeManifestParser`: fully unit-testable on the JVM. */
object IconPackParser {

    fun parse(json: String): IconPackManifest {
        val root = try {
            JsonParser.parse(json)
        } catch (e: JsonParseException) {
            throw IconPackError("Malformed icon pack JSON: ${e.message}")
        }
        val obj = root.asObjectOrNull()
            ?: throw IconPackError("Icon pack manifest must be a JSON object")

        val name = obj.stringField("name")
            ?: throw IconPackError("Icon pack manifest missing required field: name")
        val overrides = obj.stringMapField("overrides")
            ?: throw IconPackError("Icon pack manifest missing required field: overrides")

        return IconPackManifest(name = name, overrides = overrides)
    }
}
