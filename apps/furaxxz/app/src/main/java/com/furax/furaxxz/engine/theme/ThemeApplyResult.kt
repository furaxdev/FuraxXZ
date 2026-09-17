package com.furax.furaxxz.engine.theme

/**
 * Honest report of what a theme apply actually did. A component the theme
 * declares but this engine cannot yet apply (icons/sounds/animations) is
 * always listed in [skipped] with a reason — never silently dropped and
 * never counted as applied.
 */
data class ThemeApplyResult(
    val colorsApplied: Boolean = false,
    val wallpaperApplied: Boolean = false,
    val fontApplied: Boolean = false,
    val skipped: List<String> = emptyList(),
)
