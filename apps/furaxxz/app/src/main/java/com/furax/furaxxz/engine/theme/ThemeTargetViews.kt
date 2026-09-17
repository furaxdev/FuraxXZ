package com.furax.furaxxz.engine.theme

import android.view.View
import android.widget.TextView

/** The subset of the current screen a theme/pack's `colors` component is
 * allowed to recolor. FuraxXZ only ever recolors its own views in-app —
 * it never touches the Android system theme or `/system` resources. */
data class ThemeTargetViews(
    val background: View? = null,
    val accentTexts: List<TextView> = emptyList(),
)
