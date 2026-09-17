# Device Integration — Phase 10

## Status: BLOCKED

Real device integration — connecting to, reading from, or writing to a
physical Sony F8331 (`kagura`) — is **BLOCKED** in this project, not for
lack of code, but because its own preconditions aren't met:

1. **No physical device is available.** This project has been developed
   entirely in a sandboxed container with no USB access and no F8331
   attached (see `docs/ENVIRONMENT.md`). There has never been a point at
   which device integration code could be tested against real hardware.
2. **No real firmware dump has been analyzed.** Every firmware capability
   in this repo (`furaxxz firmware analyze/extract`, the lab pipeline)
   has only ever been exercised against synthetic test fixtures. See
   `docs/FIRMWARE.md`.
3. **Bootloader unlock is not allowed on this unit.** `bootloaderUnlockAllowed:
   false` in the recorded device profile (`tools/cli/furaxxz/device.py`).
   This is a fact about the specific unit this project targets, not a
   limitation FuraxXZ could route around — and it wouldn't try to.

The project roadmap is explicit about this ordering: "Device integration
uniquement après compréhension complète du boot/flash du F8331" — device
integration only after a complete understanding of the F8331's boot/flash
process. That understanding requires a real firmware dump and/or a real
device to validate against, neither of which this environment has.

## `furaxxz device readiness`

Rather than silently doing nothing for Phase 10, this project implements
a **readiness checklist** — a structured, honest, testable answer to "are
we ready for device integration yet". It:

- Never probes for a connected device (no `adb devices`/`fastboot
  devices` call from this tool, ever — see `tools/cli/furaxxz/readiness.py`).
- Never defaults to "ready". `overall_status()` can only report `OK` if
  every single item is `OK` — and `bootloader_unlock_allowed` and
  `real_firmware_analyzed` are hardcoded `BLOCKED` given the current
  device profile and this repo's actual firmware-analysis history.
- Is fully unit-tested (`tests/test_readiness.py`) including the
  load-bearing assertion that overall status is never `OK` with the
  real F8331 profile.

Run it:

```
furaxxz device readiness
```

## What a future device-integration phase would actually need

Documented here as reference, not as a promise of implementation:

1. **A real firmware dump**, obtained through official Sony channels
   (Xperia Companion backup, or a legitimately obtained service ROM),
   analyzed with `furaxxz firmware analyze` to move partition/format
   claims from assumed to verified.
2. **Sony's own confirmation that bootloader unlock is allowed** for the
   specific unit (checked via Sony's DRKG/unlock-allowed service menu
   check, or `*#*#7378423#*#*` → Service info → Configuration →
   Rooting Status on this device family) — never bypassed, only read.
3. **A physical device connected over USB**, with the user's explicit,
   informed, per-operation authorization — never cached, never inferred.
4. Even then: any write operation (flashing, partition modification)
   would need to go through `furaxxz security.SecurityContext`, which
   already blocks every operation in `BOOTLOADER_GATED_OPERATIONS`
   while unlock is disallowed (see `docs/SECURITY.md`) — that gate does
   not change for this phase and would not be loosened without a
   documented, verified change to the device profile itself.

## General F8331/kagura platform background (public information, informational only)

The F8331 is a 2016 Sony Xperia XZ variant on the `kagura` codename,
Qualcomm Snapdragon 820 (MSM8996) platform, shipped with a
fastboot-capable bootloader (standard for this Sony generation) and
Sony's own partition layout (typically including `boot`, `system`,
`vendor`, `userdata`, `cache`, `modem`, `tz`, `rpm`, `persist`, among
others). This paragraph is general platform knowledge, not something
this project has verified against this unit's actual partition table —
see item 1 above. Treat every specific number/name here as unverified
until `furaxxz firmware analyze` has actually run against a real dump.
