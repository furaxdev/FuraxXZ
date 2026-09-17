# engine/

This directory exists per the project's architecture spec as a placeholder
for a possible future **shared, cross-platform** personalization engine
(usable by both the CLI and the Android app without duplication).

As of v0.1 there is no such shared engine yet — duplicating logic here
would just be dead code. The real, working implementations are:

- **CLI / offline lab engine** (fonts, firmware, theme, pack, backup,
  security): `tools/cli/furaxxz/`
- **Android in-app engine** (catalog, fonts, wallpapers, orchestration):
  `apps/furaxxz/app/src/main/java/com/furax/furaxxz/engine/`

If/when logic needs to be shared verbatim between the CLI and the app
(e.g. the sfnt font parser), it should be extracted into this directory
as a deliberate refactor — not stubbed preemptively.
