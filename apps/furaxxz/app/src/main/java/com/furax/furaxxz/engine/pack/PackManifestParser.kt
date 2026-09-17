package com.furax.furaxxz.engine.pack

import com.furax.furaxxz.engine.json.JsonParseException
import com.furax.furaxxz.engine.json.JsonParser
import com.furax.furaxxz.engine.json.JsonValue
import com.furax.furaxxz.engine.json.asObjectOrNull
import com.furax.furaxxz.engine.json.stringField
import com.furax.furaxxz.engine.json.stringMapField

class PackManifestError(message: String) : Exception(message)

/** Parses and validates a `pack.json` document. Same rule as the CLI's
 * `pack.py::validate_pack`: `name`/`version` required, at least one
 * component declared under `components`. */
object PackManifestParser {

    fun parse(json: String): PackManifest {
        val root = try {
            JsonParser.parse(json)
        } catch (e: JsonParseException) {
            throw PackManifestError("Malformed pack JSON: ${e.message}")
        }
        val obj = root.asObjectOrNull()
            ?: throw PackManifestError("Pack manifest must be a JSON object")

        val name = obj.stringField("name")
            ?: throw PackManifestError("Pack manifest missing required field: name")
        val version = obj.stringField("version")
            ?: throw PackManifestError("Pack manifest missing required field: version")
        val components = obj["components"]?.asObjectOrNull()
            ?: throw PackManifestError("Pack manifest must have a 'components' object")
        if (components.isEmpty()) {
            throw PackManifestError("Pack must declare at least one component")
        }

        val schemaVersion = (obj["schemaVersion"] as? JsonValue.Num)?.value?.toInt() ?: 1

        return PackManifest(
            schemaVersion = schemaVersion,
            name = name,
            version = version,
            font = components.stringField("font"),
            wallpaper = components.stringField("wallpaper"),
            colors = components.stringMapField("colors"),
            icons = components.stringField("icons"),
            sounds = components.stringField("sounds"),
            bootAnimation = components.stringField("bootAnimation"),
        )
    }
}
