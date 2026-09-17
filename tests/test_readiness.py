from furaxxz import readiness


def test_bootloader_item_is_blocked_for_this_device():
    items = readiness.compute_readiness()
    bootloader_item = next(i for i in items if i.id == "bootloader_unlock_allowed")
    assert bootloader_item.status == "BLOCKED"


def test_real_firmware_item_is_blocked():
    items = readiness.compute_readiness()
    fw_item = next(i for i in items if i.id == "real_firmware_analyzed")
    assert fw_item.status == "BLOCKED"


def test_physical_device_presence_is_never_auto_confirmed():
    items = readiness.compute_readiness()
    presence_item = next(i for i in items if i.id == "physical_device_presence")
    assert presence_item.status == "UNKNOWN"


def test_explicit_authorization_is_never_auto_confirmed():
    items = readiness.compute_readiness()
    auth_item = next(i for i in items if i.id == "explicit_user_authorization")
    assert auth_item.status == "UNKNOWN"


def test_overall_status_is_blocked_given_any_blocked_item():
    items = readiness.compute_readiness()
    assert readiness.overall_status(items) == "BLOCKED"


def test_overall_status_never_ok_with_current_device_profile():
    # This is the load-bearing assertion for the whole module: given the
    # real F8331 profile (bootloaderUnlockAllowed=False, no real firmware
    # analyzed), readiness must never report OK.
    items = readiness.compute_readiness()
    assert readiness.overall_status(items) != "OK"


def test_overall_status_logic_in_isolation():
    Item = readiness.ReadinessItem
    all_ok = [Item("a", "d", "OK", "detail")]
    assert readiness.overall_status(all_ok) == "OK"

    with_unknown = [Item("a", "d", "OK", "detail"), Item("b", "d", "UNKNOWN", "detail")]
    assert readiness.overall_status(with_unknown) == "UNKNOWN"

    with_blocked = [Item("a", "d", "UNKNOWN", "detail"), Item("b", "d", "BLOCKED", "detail")]
    assert readiness.overall_status(with_blocked) == "BLOCKED"
