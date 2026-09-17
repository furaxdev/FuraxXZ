package com.furax.furaxxz.engine.json

/**
 * A minimal JSON value tree, produced by [JsonParser].
 *
 * Why not `org.json`: `org.json.*` classes ship inside `android.jar` as
 * unimplemented stubs — calling them from a local (JVM) unit test throws
 * `RuntimeException("... not mocked")` unless the project pulls in
 * Robolectric or enables `returnDefaultValues` (which silently returns
 * null/0/false instead of really parsing). Neither is worth a new
 * dependency for parsing small, well-defined theme/pack manifests, so
 * this module is plain Kotlin and fully testable on the JVM.
 */
sealed class JsonValue {
    data object Null : JsonValue()
    data class Bool(val value: Boolean) : JsonValue()
    data class Num(val value: Double) : JsonValue()
    data class Str(val value: String) : JsonValue()
    data class Arr(val items: List<JsonValue>) : JsonValue()
    data class Obj(val entries: Map<String, JsonValue>) : JsonValue()
}

fun JsonValue.asObjectOrNull(): Map<String, JsonValue>? = (this as? JsonValue.Obj)?.entries

fun JsonValue.asStringOrNull(): String? = (this as? JsonValue.Str)?.value

fun JsonValue.asArrayOrNull(): List<JsonValue>? = (this as? JsonValue.Arr)?.items

/** Reads a string field from a parsed object, or null if absent/not a string. */
fun Map<String, JsonValue>.stringField(key: String): String? = this[key]?.asStringOrNull()

/** Reads a `Map<String, String>` field (e.g. `colors`), skipping non-string values. */
fun Map<String, JsonValue>.stringMapField(key: String): Map<String, String>? =
    this[key]?.asObjectOrNull()?.mapNotNull { (k, v) -> v.asStringOrNull()?.let { k to it } }?.toMap()
