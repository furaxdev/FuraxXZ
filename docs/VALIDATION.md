# Validation — Phase 9

This is a point-in-time audit of the whole repo, not a one-off test run.
It exists to catch drift that per-module tests can't: stale docs, CI
commands that were never actually executed as written, and schema
divergence between the CLI and the Android app.

## What Phase 9 checked and fixed

1. **CI was silently broken.** `.github/workflows/ci.yml` ran
   `python -m tools.cli.furaxxz validate || true` — `tools` is not a
   Python package (no `__init__.py`), so this command has never actually
   run `furaxxz validate` in CI; the `|| true` swallowed the failure
   silently, which is exactly the kind of silent error this project's
   quality rules forbid. Fixed to `python -m furaxxz validate` with
   `PYTHONPATH=tools/cli` (matching how the test suite itself imports
   the package), verified locally, and the `|| true` removed so a real
   catalog validation failure now fails CI. `ruff` in CI also didn't
   lint `scripts/`; added it to match local usage. The Android CI job
   only ran `assembleDebug`, never `testDebugUnitTest`; added.
2. **Cross-runtime schema drift has no other guard.** The CLI
   (`theme.py`/`pack.py`) and the Android app
   (`engine/theme`/`engine/pack`) each independently parse and validate
   the same theme/pack JSON schema. Nothing kept them in sync except a
   one-off manual check done in Phase 7. Formalized as
   `tests/test_cross_runtime_consistency.py` (6 tests): every bundled
   Android demo manifest must pass the CLI validator, a CLI-created
   theme must byte-match the bundled Android demo, and — reading the
   Kotlin source directly — the `HEX_COLOR` regex literal in
   `ThemeManifestParser.kt` must be textually identical to the CLI's.
   This turns "someone edits one side and forgets the other" from a
   silent bug into an immediate CI failure.
3. **Doc staleness.** Test counts quoted in `README.md` were checked
   against a live `pytest -q` run and corrected (74 → 80 after this
   phase's additions). `docs/ENVIRONMENT.md`'s Android test count
   cross-checked against a live `./gradlew testDebugUnitTest` run.
4. **No fake/placeholder code.** Repo-wide grep for `TODO`/`FIXME`/`XXX`/
   `NotImplementedError` across `tools/cli/furaxxz` and the Android
   `java/` tree: zero matches. Every unfinished feature is represented
   as an absence (nothing stubbed) plus a `PLANNED`/`BLOCKED` line in
   `docs/MODIFICATIONS.md`, not as dead code that looks finished.

## Full suite results at Phase 9 completion

| Suite | Result |
|---|---|
| CLI `pytest -q` | 80/80 passed |
| CLI `ruff check tools/cli tests scripts` | clean |
| CLI `furaxxz validate` (catalog) | all entries valid |
| CLI `furaxxz doctor` | all checks OK except `android-sdk` (documented gap, see `docs/ENVIRONMENT.md`) |
| Android `./gradlew assembleDebug` | `app-debug.apk` built |
| Android `./gradlew testDebugUnitTest` | see `docs/ENVIRONMENT.md` for the exact count at last run |

## What Phase 9 deliberately did not do

- No new user-facing feature. This phase is an audit + the fixes an
  audit turns up, not new functionality — consistent with "Phase 9:
  Validation complète" in the project roadmap.
- No firmware or device interaction of any kind.

## Known, accepted gaps (unchanged by this phase, tracked elsewhere)

See `docs/MODIFICATIONS.md` for the full status table. Nothing found
during this audit was reclassified from `PLANNED`/`BLOCKED` to
`IMPLEMENTED` — Phase 9 fixed process gaps (CI, doc drift, missing
regression coverage), not feature gaps.
