# Bootloader

## Target device state

```json
{
  "manufacturer": "Sony",
  "model": "F8331",
  "device": "kagura",
  "android": "8.0.0",
  "build": "41.3.2.A.2.192",
  "bootloaderUnlockAllowed": false
}
```

`bootloaderUnlockAllowed: false` is a recorded fact about this specific
unit (checked via Sony's own "Unlock allowed: No" indicator in service
menu / DRKG check), not a guess. Sony ships some regional/carrier variants
of the F8331 with SIM-lock-tied bootloader restrictions where unlocking is
permanently disallowed by Sony's own servers, independent of anything a
user or this tool could do.

## What this means for FuraxXZ

Every operation tagged `flash`, `fastboot-flash`, `unlock-bootloader`,
`flash-boot`, `flash-system`, `flash-vendor`, or `flash-recovery` in
`tools/cli/furaxxz/security.py::BOOTLOADER_GATED_OPERATIONS` is
**BLOCKED** by `SecurityContext.check()` while
`bootloaderUnlockAllowed` is `false`. This is enforced in code, not just
documented — see `tests/test_device_security.py::test_bootloader_gated_operation_blocked`.

## What FuraxXZ will never do (non-negotiable, per project spec)

- Bypass or exploit a way around the bootloader lock.
- Attempt to force Sony's unlock-allowed check.
- Disable Verified Boot or any other platform security feature.
- Forge or strip a signature to make an image appear valid.
- Automate a flash operation without a human confirming a dry-run first.

## What remains possible on a locked bootloader

Everything this project actually implements today: catalog browsing,
in-app font/wallpaper preview and application (sandboxed, no `/system`
write), firmware **analysis** (read-only), and lab-only modification
experiments that are explicitly never presented as flashable. See
`docs/MODIFICATIONS.md`.
