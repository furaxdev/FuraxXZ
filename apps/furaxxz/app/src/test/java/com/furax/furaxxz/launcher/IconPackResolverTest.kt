package com.furax.furaxxz.launcher

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class IconPackResolverTest {

    private val manifest = IconPackManifest(
        name = "Test Pack",
        overrides = mapOf("com.android.settings" to "ic_override_gear"),
    )

    @Test
    fun `resolves an overridden package`() {
        assertEquals("ic_override_gear", IconPackResolver.resolve(manifest, "com.android.settings"))
    }

    @Test
    fun `returns null for a non-overridden package (caller must fall back to the real icon)`() {
        assertNull(IconPackResolver.resolve(manifest, "com.whatsapp"))
    }

    @Test
    fun `an empty icon pack overrides nothing`() {
        val empty = IconPackManifest(name = "Empty", overrides = emptyMap())
        assertNull(IconPackResolver.resolve(empty, "com.android.settings"))
    }
}
