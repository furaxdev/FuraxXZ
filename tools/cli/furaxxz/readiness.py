"""Phase 10 — device integration readiness checklist.

This module never touches a device. It does not run `adb`/`fastboot`,
does not probe for USB devices, and does not assume one is connected —
this sandboxed development environment never has the physical F8331
attached, and the project rule is to never automate anything that could
touch it. What this gives instead is an honest, structured answer to
"are we ready for device integration yet": a checklist, each item backed
by something this repo actually knows, with the overall answer never
defaulting to ready.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass

from .device import TARGET_DEVICE


@dataclass
class ReadinessItem:
    id: str
    description: str
    status: str  # "OK" | "BLOCKED" | "UNKNOWN"
    detail: str


def compute_readiness() -> list[ReadinessItem]:
    items = []

    items.append(
        ReadinessItem(
            id="bootloader_unlock_allowed",
            description="Bootloader unlock is allowed on the target unit",
            status="OK" if TARGET_DEVICE.bootloader_unlock_allowed else "BLOCKED",
            detail=(
                "bootloaderUnlockAllowed=False on this recorded device profile — "
                "Sony's own unlock-allowed check denies it for this unit/region. "
                "FuraxXZ will not attempt to bypass this (see docs/BOOTLOADER.md)."
                if not TARGET_DEVICE.bootloader_unlock_allowed
                else "bootloaderUnlockAllowed=True on this recorded device profile."
            ),
        )
    )

    items.append(
        ReadinessItem(
            id="real_firmware_analyzed",
            description="A real F8331 firmware dump has been analyzed by this project",
            status="BLOCKED",
            detail=(
                "No physical device or real Sony firmware image is available in this "
                "development environment (see docs/ENVIRONMENT.md). Every firmware "
                "capability in this repo has only been exercised against synthetic "
                "test fixtures — see docs/FIRMWARE.md."
            ),
        )
    )

    adb = shutil.which("adb")
    fastboot = shutil.which("fastboot")
    items.append(
        ReadinessItem(
            id="platform_tools_available",
            description="adb/fastboot are available on this machine (informational only)",
            status="OK" if (adb and fastboot) else "UNKNOWN",
            detail=(
                f"adb={adb or 'not found'}, fastboot={fastboot or 'not found'}. "
                "This check only looks at PATH — it never runs `adb devices` or "
                "`fastboot devices`, since this tool does not probe for a connected "
                "device."
            ),
        )
    )

    items.append(
        ReadinessItem(
            id="physical_device_presence",
            description="Whether a physical F8331 is connected",
            status="UNKNOWN",
            detail=(
                "Not checked by this tool, by design. FuraxXZ never probes for or "
                "interacts with a connected device automatically — verify manually "
                "with `adb devices` / `fastboot devices` outside this tool if needed."
            ),
        )
    )

    items.append(
        ReadinessItem(
            id="explicit_user_authorization",
            description="Explicit, informed user authorization for a device-touching operation",
            status="UNKNOWN",
            detail=(
                "Can only be given by a human, per-operation, at the time — never "
                "inferred or cached by this tool."
            ),
        )
    )

    return items


def overall_status(items: list[ReadinessItem]) -> str:
    if any(i.status == "BLOCKED" for i in items):
        return "BLOCKED"
    if any(i.status == "UNKNOWN" for i in items):
        return "UNKNOWN"
    return "OK"
