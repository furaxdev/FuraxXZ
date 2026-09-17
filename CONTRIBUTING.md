# Contributing to FuraxXZ

## Ground rules

1. **A technically possible modification is not automatically a flashable
   one.** Never mark a firmware modification path as ready/safe without
   documented proof it was validated against real hardware.
2. **Status honesty.** Every feature is `IMPLEMENTED`, `EXPERIMENTAL`,
   `BLOCKED`, or `PLANNED` — see `docs/MODIFICATIONS.md`. Never present a
   stub as done.
3. **No bootloader bypass, signature forgery, or auto-flash.** These are
   hard `FORBIDDEN` in `tools/cli/furaxxz/security.py` and will not be
   accepted in any PR, regardless of framing.
4. **Real functionality only.** No fake TODOs, no mocked-and-presented-
   as-real behavior, no invented compatibility claims, no silent error
   swallowing.

## Development setup

```bash
python3 -m pip install pytest ruff
python3 -m pytest -v
```

For the Android app, see `README.md`'s Android quick-start.

## Before opening a PR

- Run `python3 -m pytest -v` — all tests must pass.
- Run `furaxxz validate` if you touched `catalog/`.
- If you touched the Android app, run `./gradlew testDebugUnitTest` from
  `apps/furaxxz/` (and `assembleDebug` if you can — Android SDK required).
- Update the relevant `docs/*.md` file if you changed a feature's status.
- Keep `lab/`, `firmware/extracted/`, etc. out of your commit — they're
  gitignored working directories, not source.

## Adding a catalog entry

See `docs/CATALOG.md` for the manifest schema. Do not add assets you do
not have redistribution rights to (see `LICENSE`).

## Coding conventions

- CLI: Python 3.10+, stdlib only unless there's a strong reason for a
  dependency (there currently is none).
- Android: Kotlin, Views/XML, no Jetpack Compose, minSdk 26.
- No comments explaining *what* code does — only *why*, when non-obvious.
