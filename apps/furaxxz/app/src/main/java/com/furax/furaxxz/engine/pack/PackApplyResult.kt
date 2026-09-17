package com.furax.furaxxz.engine.pack

/** Honest per-component report — mirrors [com.furax.furaxxz.engine.theme.ThemeApplyResult]'s
 * "never claim what wasn't done" rule. */
data class PackApplyResult(
    val appliedComponents: List<String>,
    val skippedComponents: List<String>,
)
