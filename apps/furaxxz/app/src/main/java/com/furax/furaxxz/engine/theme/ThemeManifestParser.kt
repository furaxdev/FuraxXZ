package com.furax.furaxxz.engine.theme

import com.furax.furaxxz.engine.json.JsonParseException
import com.furax.furaxxz.engine.json.JsonParser
import com.furax.furaxxz.engine.json.JsonValue
import com.furax.furaxxz.engine.json.asObjectOrNull
import com.furax.furaxxz.engine.json.stringField
import com.furax.furaxxz.engine.json.stringMapField

class ThemeManifestError(message: String) : Exception(message)

private val HEX_COLOR = Regex("^#[0-9A-Fa-f]{6}$")

/** Parses and validates a `theme.json` document. Same rules as the CLI's
 * `theme.py::validate_theme`: `name`/`version`/`colors` required, every
 * color a `#RRGGBB` hex string. */
object ThemeManifestParser {

    fun parse(json: String): ThemeManifest {
        val root = try {
            JsonParser.parse(json)
        } catch (e: JsonParseException) {
            throw ThemeManifestError("Malformed theme JSON: ${e.message}")
        }
        val obj = root.asObjectOrNull()
            ?: throw ThemeManifestError("Theme manifest must be a JSON object")

        val name = obj.stringField("name")
            ?: throw ThemeManifestError("Theme manifest missing required field: name")
        val version = obj.stringField("version")
            ?: throw ThemeManifestError("Theme manifest missing required field: version")
        val colors = obj.stringMapField("colors")
            ?: throw ThemeManifestError("Theme manifest missing required field: colors")
        if (colors.isEmpty()) {
            throw ThemeManifestError("Theme 'colors' must be a non-empty object")
        }
        for ((key, value) in colors) {
            if (!HEX_COLOR.matches(value)) {
                throw ThemeManifestError("Color '$key' must be a hex string like '#RRGGBB', got '$value'")
            }
        }

        val schemaVersion = (obj["schemaVersion"] as? JsonValue.Num)?.value?.toInt() ?: 1

        return ThemeManifest(
            schemaVersion = schemaVersion,
            name = name,
            version = version,
            colors = colors,
            wallpaper = obj.stringField("wallpaper"),
            icons = obj.stringField("icons"),
            font = obj.stringField("font"),
            sounds = obj.stringField("sounds"),
            animations = obj.stringField("animations"),
        )
    }
}
