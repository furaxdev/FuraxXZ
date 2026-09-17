# Security

## Device profile (single source of truth)

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

Defined once in `tools/cli/furaxxz/device.py::TARGET_DEVICE`; every other
module (security gate, backup manifests, inject banner) reads from here —
nothing duplicates or re-guesses these values.

## `furaxxz security inspect`

Read-only. Reports the device profile, bootloader state (labelled "not
physically verified" — this tool has no ADB/fastboot connection to a real
unit), and `flashCompatibility: UNKNOWN`, plus the standing policy:

```json
{
  "bootloaderBypass": "FORBIDDEN",
  "signatureForgery": "FORBIDDEN",
  "autoFlash": "FORBIDDEN",
  "userdataWipeWithoutConfirmation": "FORBIDDEN"
}
```

## The security gate

`tools/cli/furaxxz/security.py::SecurityContext`:

- Every sensitive CLI operation constructs a `SecurityContext` and prints
  its `.banner()` (device, build, bootloader, operation, compatibility,
  dry-run/live) **before** doing anything.
- `.check()` raises `SecurityBlocked` for any operation named in
  `BOOTLOADER_GATED_OPERATIONS` while `bootloaderUnlockAllowed` is
  `false`. This is not a warning — the operation does not proceed.
- Sensitive operations default to dry-run; `--execute`/equivalent flags
  are required to do anything beyond validation and backup.

## Hard rules (enforced by code, not just policy)

1. Never bypass, exploit, or disable the bootloader lock or Verified Boot.
2. Never forge or strip a signature.
3. Never automate a flash operation.
4. Never wipe `userdata` without an explicit, separate confirmation step
   (not implemented at all in v0.1 — there is no wipe command).
5. Flash compatibility is `UNKNOWN` until an actual verification step
   exists and has run — never hardcoded to `COMPATIBLE`.

## Hashing & backups

All backups are content-addressed with SHA-256
(`tools/cli/furaxxz/hashing.py`). `backup.py::restore_backup` **re-hashes
every file before restoring it** and raises `BackupError` on any mismatch
— a corrupted backup is refused, not silently restored.
