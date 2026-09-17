"""Target device profile for FuraxXZ.

The profile is the single source of truth for which physical device this
project targets. Every sensitive operation must read compatibility from
here rather than assuming it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class DeviceProfile:
    manufacturer: str
    model: str
    device: str
    android: str
    build: str
    bootloader_unlock_allowed: bool

    def as_dict(self) -> dict:
        d = asdict(self)
        # Match the JSON shape documented in the project spec.
        return {
            "manufacturer": d["manufacturer"],
            "model": d["model"],
            "device": d["device"],
            "android": d["android"],
            "build": d["build"],
            "bootloaderUnlockAllowed": d["bootloader_unlock_allowed"],
        }


TARGET_DEVICE = DeviceProfile(
    manufacturer="Sony",
    model="F8331",
    device="kagura",
    android="8.0.0",
    build="41.3.2.A.2.192",
    bootloader_unlock_allowed=False,
)


# Flash compatibility is UNKNOWN until it has actually been verified against
# a real image/device. Never hardcode a "compatible" result.
COMPATIBILITY_UNKNOWN = "UNKNOWN"
COMPATIBILITY_COMPATIBLE = "COMPATIBLE"
COMPATIBILITY_INCOMPATIBLE = "INCOMPATIBLE"
