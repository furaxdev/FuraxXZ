package com.furax.furaxxz.model

/** The seven personalization categories FuraxXZ organizes its catalog into. */
enum class Category(val displayName: String, val storageDirName: String) {
    FONTS("Fonts", "fonts"),
    WALLPAPERS("Wallpapers", "wallpapers"),
    THEMES("Themes", "themes"),
    ICONS("Icons", "icons"),
    SOUNDS("Sounds", "sounds"),
    ANIMATIONS("Animations", "animations"),
    PACKS("Packs", "packs");

    companion object {
        fun all(): List<Category> = values().toList()
    }
}
