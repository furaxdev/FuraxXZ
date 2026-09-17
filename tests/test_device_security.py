import pytest
from furaxxz import security
from furaxxz.device import COMPATIBILITY_UNKNOWN, TARGET_DEVICE


def test_device_profile_matches_spec():
    d = TARGET_DEVICE.as_dict()
    assert d == {
        "manufacturer": "Sony",
        "model": "F8331",
        "device": "kagura",
        "android": "8.0.0",
        "build": "41.3.2.A.2.192",
        "bootloaderUnlockAllowed": False,
    }


def test_security_inspect_reports_unknown_compatibility():
    report = security.inspect()
    assert report["flashCompatibility"] == COMPATIBILITY_UNKNOWN


def test_bootloader_gated_operation_blocked():
    ctx = security.SecurityContext(operation="flash-boot", dry_run=True)
    with pytest.raises(security.SecurityBlocked):
        ctx.check()


def test_non_gated_operation_passes():
    ctx = security.SecurityContext(operation="fonts-inject", dry_run=True)
    ctx.check()  # should not raise


def test_banner_contains_device_and_operation():
    ctx = security.SecurityContext(operation="fonts-inject")
    banner = ctx.banner()
    assert "F8331" in banner
    assert "fonts-inject" in banner
    assert "UNKNOWN" in banner
