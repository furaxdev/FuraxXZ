"""FuraxXZ CLI entry point.

    furaxxz doctor
    furaxxz device profile
    furaxxz firmware analyze <file>
    furaxxz firmware extract <file> [--system-only|--boot-only|--vendor-only|--all]
    furaxxz fonts list
    furaxxz fonts inspect <font>
    furaxxz fonts validate <font>
    furaxxz fonts inject <image> <font> [--dry-run]
    furaxxz theme create <name> --colors k=v [k=v ...]
    furaxxz pack create <name>
    furaxxz backup create <file> [<file> ...] --to <dir>
    furaxxz backup restore <dir> --to <dir>
    furaxxz security inspect
    furaxxz lab init <source_dir> --session <name>
    furaxxz lab apply <session> --replace <rel_path> <file>
    furaxxz lab apply <session> --add <rel_path> <file>
    furaxxz lab apply <session> --remove <rel_path>
    furaxxz lab build <session>
    furaxxz lab verify <session>
    furaxxz device readiness
    furaxxz validate
    furaxxz clean
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from . import __version__, environment
from . import backup as backup_mod
from . import firmware as firmware_mod
from . import fonts as fonts_mod
from . import lab as lab_mod
from . import pack as pack_mod
from . import readiness as readiness_mod
from . import security as security_mod
from . import theme as theme_mod
from .device import TARGET_DEVICE
from .hashing import sha256_file

REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG_FONTS = REPO_ROOT / "catalog" / "fonts"
CATALOG_THEMES = REPO_ROOT / "catalog" / "themes"
CATALOG_PACKS = REPO_ROOT / "catalog" / "packs"
LAB_DIR = REPO_ROOT / "lab"


def _print_json(obj) -> None:
    print(json.dumps(obj, indent=2, default=str))


def cmd_doctor(args) -> int:
    results = environment.run_doctor(str(REPO_ROOT))
    all_ok = True
    for r in results:
        status = "OK  " if r.ok else "FAIL"
        if not r.ok:
            all_ok = False
        print(f"[{status}] {r.name:<14} {r.detail}")
    print()
    if all_ok:
        print("Environment is READY")
    else:
        print("Environment has MISSING pieces — see docs/ENVIRONMENT.md")
    return 0 if all_ok else 1


def cmd_device_profile(args) -> int:
    _print_json(TARGET_DEVICE.as_dict())
    return 0


def cmd_device_readiness(args) -> int:
    items = readiness_mod.compute_readiness()
    for item in items:
        print(f"[{item.status:<7}] {item.id}: {item.description}")
        print(f"           {item.detail}")
    overall = readiness_mod.overall_status(items)
    print(f"\nOverall device-integration readiness: {overall}")
    if overall != "OK":
        print(
            "Device integration (Phase 10) remains BLOCKED — see "
            "docs/DEVICE_INTEGRATION.md. Nothing in this tool will attempt to "
            "flash, unlock, or otherwise modify a real device."
        )
    return 0 if overall == "OK" else 1


def cmd_firmware_analyze(args) -> int:
    try:
        report = firmware_mod.analyze(Path(args.file))
    except firmware_mod.FirmwareError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    _print_json(vars(report))
    return 0


def cmd_firmware_extract(args) -> int:
    dest = Path(args.dest) if args.dest else LAB_DIR / "extracted" / Path(args.file).stem
    try:
        extracted = firmware_mod.extract(
            Path(args.file), dest,
            system_only=args.system_only, boot_only=args.boot_only,
            vendor_only=args.vendor_only, all_partitions=args.all,
        )
    except firmware_mod.FirmwareError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Extracted {len(extracted)} entr{'y' if len(extracted) == 1 else 'ies'} to {dest}")
    for name in extracted:
        print(f"  {name}")
    return 0


def cmd_fonts_list(args) -> int:
    CATALOG_FONTS.mkdir(parents=True, exist_ok=True)
    fonts = sorted(p for p in CATALOG_FONTS.rglob("*") if p.suffix.lower() in (".ttf", ".otf"))
    if not fonts:
        print(f"No fonts found in {CATALOG_FONTS} (catalog is empty).")
        return 0
    for f in fonts:
        ok, _msg, meta = fonts_mod.validate_font(f)
        label = meta.family if ok and meta and meta.family else "?"
        print(f"{f.relative_to(REPO_ROOT)}  family={label}  valid={ok}")
    return 0


def cmd_fonts_inspect(args) -> int:
    target = Path(args.target)
    if target.suffix.lower() in (".ttf", ".otf"):
        try:
            meta = fonts_mod.parse_font(target)
        except fonts_mod.FontValidationError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        _print_json(vars(meta))
        return 0
    # Otherwise treat as a firmware image and report where fonts might live.
    print(f"'{target}' is not a .ttf/.otf file.")
    print("Locating font storage inside a firmware image requires extraction first:")
    print(f"  furaxxz firmware extract {target} --system-only")
    print("then inspecting fonts typically found under system/fonts/ once extracted —")
    print("this path is NOT assumed; verify it exists in the extracted tree before use.")
    return 1


def cmd_fonts_validate(args) -> int:
    ok, msg, meta = fonts_mod.validate_font(Path(args.font))
    print(msg)
    if ok:
        _print_json(vars(meta))
    return 0 if ok else 1


def cmd_fonts_inject(args) -> int:
    image = Path(args.image)
    font = Path(args.font)

    ctx = security_mod.SecurityContext(operation="fonts-inject", dry_run=not args.execute)
    print(ctx.banner())

    ok, msg, _meta = fonts_mod.validate_font(font)
    print(f"\n1. Format check: {msg}")
    if not ok:
        return 1

    if not image.is_file():
        print(f"2. error: firmware image not found: {image}", file=sys.stderr)
        return 1
    print("2. Compatibility check: image exists (deep compatibility check requires "
          "extraction — not performed by this stub).")

    free_bytes = shutil.disk_usage(image.parent).free
    print(f"3. Space check: {free_bytes / (1024**2):.1f} MiB free at {image.parent}")

    original_hash = sha256_file(image)
    print(f"4. Original hash (sha256): {original_hash}")

    lab_target = LAB_DIR / "modified" / image.name
    lab_target.parent.mkdir(parents=True, exist_ok=True)

    if not args.execute:
        print("5. DRY-RUN: no backup written, no modification performed.")
        print("6. DRY-RUN: no modification performed (font injection into a live "
              "partition image requires format-specific repacking — EXPERIMENTAL, "
              "not implemented — see docs/MODIFICATIONS.md).")
        print("Result: DRY-RUN complete. Re-run with --execute to write a backup into lab/ "
              "(actual partition repacking remains EXPERIMENTAL/BLOCKED until validated).")
        return 0

    backup_path = LAB_DIR / "original" / image.name
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(image, backup_path)
    print(f"5. Backup written: {backup_path}")

    print("6. BLOCKED: repacking the font into this partition image format is not "
          "implemented (requires per-partition-format tooling that has not been "
          "validated against real F8331 firmware). No modification was made.")
    return 2


def cmd_theme_create(args) -> int:
    colors = dict(item.split("=", 1) for item in args.colors)
    try:
        path = theme_mod.create_theme(CATALOG_THEMES, args.name, colors)
    except theme_mod.ThemeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Theme created: {path}")
    return 0


def cmd_pack_create(args) -> int:
    try:
        path = pack_mod.create_pack(CATALOG_PACKS, args.name)
    except pack_mod.PackError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Pack created: {path}")
    return 0


def cmd_backup_create(args) -> int:
    sources = [Path(f) for f in args.files]
    dest = Path(args.to)
    try:
        manifest_path = backup_mod.create_backup(sources, dest)
    except backup_mod.BackupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Backup manifest written: {manifest_path}")
    return 0


def cmd_backup_restore(args) -> int:
    try:
        restored = backup_mod.restore_backup(Path(args.backup_dir), Path(args.to))
    except backup_mod.BackupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Restored {len(restored)} file(s) to {args.to}")
    for name in restored:
        print(f"  {name}")
    return 0


def cmd_security_inspect(args) -> int:
    _print_json(security_mod.inspect())
    return 0


def cmd_lab_init(args) -> int:
    ctx = security_mod.SecurityContext(operation="lab-modify", dry_run=True)
    print(ctx.banner())
    print()
    try:
        session = lab_mod.init_session(LAB_DIR, Path(args.source_dir), args.session)
    except lab_mod.LabError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    manifest_count = len(session.load_operations())
    print(f"Session '{args.session}' initialized from {args.source_dir}")
    print(f"  original: {session.original_tree}")
    print(f"  modified: {session.modified_tree} (working copy, {manifest_count} operations so far)")
    return 0


def cmd_lab_apply(args) -> int:
    op_types = [t for t in ("replace", "add", "remove") if getattr(args, t)]
    if len(op_types) != 1:
        print("error: specify exactly one of --replace, --add, --remove", file=sys.stderr)
        return 1
    op_type = op_types[0]
    if op_type == "remove":
        rel_path = args.remove
        source_file = None
    else:
        rel_path, source = getattr(args, op_type)
        source_file = Path(source)

    ctx = security_mod.SecurityContext(operation="lab-modify", dry_run=True)
    print(ctx.banner())
    print()

    session = lab_mod.LabSession(session_id=args.session, lab_root=LAB_DIR)
    try:
        result = lab_mod.apply_operation(session, op_type, rel_path, source_file)
    except lab_mod.LabError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Applied {op_type} on '{rel_path}'")
    print(f"  sha256 before: {result.sha256_before}")
    print(f"  sha256 after:  {result.sha256_after}")
    return 0


def cmd_lab_build(args) -> int:
    ctx = security_mod.SecurityContext(operation="lab-modify", dry_run=True)
    print(ctx.banner())
    print()

    session = lab_mod.LabSession(session_id=args.session, lab_root=LAB_DIR)
    try:
        report = lab_mod.build_session(session)
    except lab_mod.LabError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    _print_json(report)
    return 0


def cmd_lab_verify(args) -> int:
    session = lab_mod.LabSession(session_id=args.session, lab_root=LAB_DIR)
    try:
        result = lab_mod.verify_session(session, LAB_DIR / "reports" / args.session)
    except lab_mod.LabError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Original intact: {result.original_intact}")
    if result.original_mismatches:
        print(f"  mismatches: {result.original_mismatches}")
    print(f"Reproducible:    {result.reproducible}")
    if result.reproduction_mismatches:
        print(f"  mismatches: {result.reproduction_mismatches}")
    print("VERIFY PASSED" if result.ok else "VERIFY FAILED")
    return 0 if result.ok else 1


def cmd_validate(args) -> int:
    problems = []
    for theme_path in CATALOG_THEMES.glob("*/theme.json"):
        try:
            theme_mod.load_theme(theme_path)
        except theme_mod.ThemeError as exc:
            problems.append(f"{theme_path}: {exc}")
    for pack_path in CATALOG_PACKS.glob("*/pack.json"):
        try:
            pack_mod.load_pack(pack_path)
        except pack_mod.PackError as exc:
            problems.append(f"{pack_path}: {exc}")
    for font_path in CATALOG_FONTS.rglob("*"):
        if font_path.suffix.lower() in (".ttf", ".otf"):
            ok, msg, _ = fonts_mod.validate_font(font_path)
            if not ok:
                problems.append(f"{font_path}: {msg}")

    if problems:
        print(f"{len(problems)} problem(s) found:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("All catalog entries valid (themes, packs, fonts).")
    return 0


def cmd_clean(args) -> int:
    targets = [REPO_ROOT / "firmware" / "extracted", REPO_ROOT / "lab" / "extracted"]
    cleaned = []
    for t in targets:
        if t.exists():
            for child in t.iterdir():
                if child.name == ".gitkeep":
                    continue
                if args.dry_run:
                    cleaned.append(str(child))
                else:
                    if child.is_dir():
                        shutil.rmtree(child)
                    else:
                        child.unlink()
                    cleaned.append(str(child))
    verb = "Would remove" if args.dry_run else "Removed"
    print(f"{verb} {len(cleaned)} item(s):")
    for c in cleaned:
        print(f"  {c}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="furaxxz", description="FuraxXZ toolkit")
    parser.add_argument("--version", action="version", version=f"furaxxz {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("doctor", help="Check the local environment")

    p.set_defaults(func=cmd_doctor)

    device = sub.add_parser("device", help="Device profile commands")
    device_sub = device.add_subparsers(dest="device_command", required=True)
    p = device_sub.add_parser("profile", help="Print the target device profile")
    p.set_defaults(func=cmd_device_profile)
    p = device_sub.add_parser("readiness", help="Device integration readiness checklist (Phase 10)")
    p.set_defaults(func=cmd_device_readiness)

    fw = sub.add_parser("firmware", help="Firmware analysis/extraction")
    fw_sub = fw.add_subparsers(dest="firmware_command", required=True)
    p = fw_sub.add_parser("analyze", help="Analyze a firmware file")
    p.add_argument("file")
    p.set_defaults(func=cmd_firmware_analyze)
    p = fw_sub.add_parser("extract", help="Extract a firmware archive")
    p.add_argument("file")
    p.add_argument("--dest")
    p.add_argument("--system-only", action="store_true")
    p.add_argument("--boot-only", action="store_true")
    p.add_argument("--vendor-only", action="store_true")
    p.add_argument("--all", action="store_true")
    p.set_defaults(func=cmd_firmware_extract)

    fonts = sub.add_parser("fonts", help="Font engine commands")
    fonts_sub = fonts.add_subparsers(dest="fonts_command", required=True)
    p = fonts_sub.add_parser("list", help="List fonts in the local catalog")
    p.set_defaults(func=cmd_fonts_list)
    p = fonts_sub.add_parser("inspect", help="Inspect a font file or image")
    p.add_argument("target")
    p.set_defaults(func=cmd_fonts_inspect)
    p = fonts_sub.add_parser("validate", help="Validate a font file")
    p.add_argument("font")
    p.set_defaults(func=cmd_fonts_validate)
    p = fonts_sub.add_parser("inject", help="Inject a font into a firmware image (lab only)")
    p.add_argument("image")
    p.add_argument("font")
    p.add_argument(
        "--execute", action="store_true", help="Perform the backup step (default: dry-run)"
    )
    p.set_defaults(func=cmd_fonts_inject)

    theme = sub.add_parser("theme", help="Theme engine commands")
    theme_sub = theme.add_subparsers(dest="theme_command", required=True)
    p = theme_sub.add_parser("create", help="Create a theme manifest")
    p.add_argument("name")
    p.add_argument("--colors", nargs="+", default=["primary=#7C4DFF", "background=#0E0E12"],
                    help="key=#hex pairs")
    p.set_defaults(func=cmd_theme_create)

    pack = sub.add_parser("pack", help="Pack engine commands")
    pack_sub = pack.add_subparsers(dest="pack_command", required=True)
    p = pack_sub.add_parser("create", help="Create a pack manifest")
    p.add_argument("name")
    p.set_defaults(func=cmd_pack_create)

    backup = sub.add_parser("backup", help="Backup manager")
    backup_sub = backup.add_subparsers(dest="backup_command", required=True)
    p = backup_sub.add_parser("create", help="Create a backup")
    p.add_argument("files", nargs="+")
    p.add_argument("--to", required=True)
    p.set_defaults(func=cmd_backup_create)
    p = backup_sub.add_parser("restore", help="Restore a backup")
    p.add_argument("backup_dir")
    p.add_argument("--to", required=True)
    p.set_defaults(func=cmd_backup_restore)

    security = sub.add_parser("security", help="Security analyzer")
    security_sub = security.add_subparsers(dest="security_command", required=True)
    p = security_sub.add_parser("inspect", help="Inspect device security posture")
    p.set_defaults(func=cmd_security_inspect)

    lab = sub.add_parser("lab", help="Offline system modification lab (never flashable)")
    lab_sub = lab.add_subparsers(dest="lab_command", required=True)
    p = lab_sub.add_parser("init", help="Snapshot a source tree into a new lab session")
    p.add_argument("source_dir")
    p.add_argument("--session", required=True)
    p.set_defaults(func=cmd_lab_init)
    p = lab_sub.add_parser("apply", help="Apply a recorded file operation to a session")
    p.add_argument("session")
    p.add_argument("--replace", nargs=2, metavar=("REL_PATH", "FILE"))
    p.add_argument("--add", nargs=2, metavar=("REL_PATH", "FILE"))
    p.add_argument("--remove", metavar="REL_PATH")
    p.set_defaults(func=cmd_lab_apply)
    p = lab_sub.add_parser("build", help="Package a session's modified tree (never flashable)")
    p.add_argument("session")
    p.set_defaults(func=cmd_lab_build)
    p = lab_sub.add_parser("verify", help="Verify a session is intact and reproducible")
    p.add_argument("session")
    p.set_defaults(func=cmd_lab_verify)

    p = sub.add_parser("validate", help="Validate the local catalog")

    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("clean", help="Clean transient extraction directories")
    p.add_argument("--dry-run", action="store_true", default=False)
    p.set_defaults(func=cmd_clean)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
