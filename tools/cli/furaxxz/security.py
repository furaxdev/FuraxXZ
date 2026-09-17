"""Security gating for sensitive operations.

Rules (non-negotiable, per project spec):
  - Never claim flash compatibility beyond UNKNOWN until verified.
  - Never bypass, exploit, or disable bootloader/verified-boot protections.
  - Any operation that requires an unlocked bootloader is blocked when
    `bootloader_unlock_allowed` is False on the device profile.
  - Sensitive operations must support --dry-run.
"""

from __future__ import annotations

from dataclasses import dataclass

from .device import COMPATIBILITY_UNKNOWN, TARGET_DEVICE


class SecurityBlocked(RuntimeError):
    """Raised when an operation is blocked by the security gate."""


# Operations that require the bootloader to already be unlocked on-device.
BOOTLOADER_GATED_OPERATIONS = {
    "flash", "fastboot-flash", "unlock-bootloader", "flash-boot",
    "flash-system", "flash-vendor", "flash-recovery",
}


@dataclass
class SecurityContext:
    operation: str
    dry_run: bool = True

    def banner(self) -> str:
        d = TARGET_DEVICE
        return (
            "== FuraxXZ Security Gate ==\n"
            f"Device:        {d.manufacturer} {d.model} ({d.device})\n"
            f"Build:         {d.build}\n"
            f"Android:       {d.android}\n"
            f"Bootloader:    unlock_allowed={d.bootloader_unlock_allowed}\n"
            f"Operation:     {self.operation}\n"
            f"Compatibility: {COMPATIBILITY_UNKNOWN}\n"
            f"Mode:          {'DRY-RUN' if self.dry_run else 'LIVE'}"
        )

    def check(self) -> None:
        gated = self.operation in BOOTLOADER_GATED_OPERATIONS
        if gated and not TARGET_DEVICE.bootloader_unlock_allowed:
            raise SecurityBlocked(
                f"Operation '{self.operation}' requires an unlocked bootloader, "
                "but the device profile records bootloaderUnlockAllowed=false. "
                "FuraxXZ will not bypass, exploit, or override this. BLOCKED."
            )


def inspect() -> dict:
    """Produce a read-only security inspection report. No hardware is
    touched — this reflects the recorded device profile only."""
    d = TARGET_DEVICE
    return {
        "device": d.as_dict(),
        "bootloader": {
            "unlockAllowed": d.bootloader_unlock_allowed,
            "state": "LOCKED (assumed; not physically verified)" if not d.bootloader_unlock_allowed
                     else "UNLOCK ALLOWED (not physically verified)",
        },
        "verifiedBoot": "UNKNOWN (requires on-device `getprop ro.boot.verifiedbootstate`)",
        "flashCompatibility": COMPATIBILITY_UNKNOWN,
        "policy": {
            "bootloaderBypass": "FORBIDDEN",
            "signatureForgery": "FORBIDDEN",
            "autoFlash": "FORBIDDEN",
            "userdataWipeWithoutConfirmation": "FORBIDDEN",
        },
    }
