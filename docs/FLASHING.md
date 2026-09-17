# Flashing — status and vocabulary

FuraxXZ uses four precise terms everywhere. Never substitute one for
another when describing a modification:

| Term | Meaning |
|---|---|
| **Official Sony flashing** | Flashing an unmodified, Sony-signed firmware image using Sony's own tools (Xperia Companion, Newflasher, Emma). Always safe on this device model when the correct image is used. FuraxXZ does not perform this — it is out of scope. |
| **Modified image** | A Sony image that has been altered (e.g. a font swapped inside `system.img`) by tooling in this repo, inside `lab/`. Never signed by Sony. Flashability is `UNKNOWN` by definition — see below. |
| **Experimental** | A code path that runs and produces output, but has not been validated against real F8331 hardware or a real firmware dump. Everything in `firmware.py`/`fonts.py`'s injection path is currently experimental until tested on a real image. |
| **Unsupported** | Explicitly out of scope: bootloader unlock bypass, signature forgery, anything in `security.SecurityContext.BOOTLOADER_GATED_OPERATIONS` while unlock is disallowed. |

## Flash compatibility is always `UNKNOWN` until verified

`furaxxz security inspect` and `furaxxz fonts inject` both report
`flashCompatibility: "UNKNOWN"` unconditionally
(`device.COMPATIBILITY_UNKNOWN`). There is no code path in this
repository that upgrades that value to `COMPATIBLE` — doing so requires
an actual verification step (checksum-level comparison against a known
Sony partition layout, or a real flash test) that has not been built or
is not safe to automate. See `docs/SECURITY.md`.

## What `furaxxz fonts inject` currently does, precisely

1. Validates the font format (real sfnt parsing).
2. Checks the image file exists (does **not** yet deep-inspect partition
   compatibility — that requires extraction, which is a separate step).
3. Reports free disk space.
4. Computes and prints the original image's SHA-256.
5. In dry-run (default): stops here, prints what *would* happen.
6. With `--execute`: writes a verified backup to `lab/original/`, then
   **stops and reports `BLOCKED`** — actual partition repacking
   (rebuilding a valid `system.img`/ext4 image with the new font byte-for-
   byte in place) is not implemented. Claiming otherwise would violate the
   project's core rule.

Nothing produced by this repository should ever be flashed to a real
device without independent verification outside this tool.

## The Phase 8 offline lab (`furaxxz lab ...`)

`lab init` / `lab apply` / `lab build` / `lab verify` (see
`docs/MODIFICATIONS.md` and `tools/cli/furaxxz/lab.py`) let you
experiment with file-level changes to an already-extracted directory
tree — replace/add/remove a file, then rebuild. This is a different,
more honest workflow than `fonts inject`'s partition-image path:

- It never touches a raw partition image (`.img`) — only a directory
  tree, e.g. one produced by `furaxxz firmware extract`.
- `lab build`'s output is a plain ZIP archive, not a partition image.
  Its `report.json` hardcodes `"flashable": false` and
  `"status": "EXPERIMENTAL"` — there is no code path that changes this.
- It exists to make modifications **reproducible and auditable**
  (every change is a recorded operation, replayable and hash-verified
  by `lab verify`), not to produce something flashable.

If real partition repacking is ever implemented, it would consume a
`lab build` output as input — it does not exist yet (see
`docs/MODIFICATIONS.md`: still `BLOCKED`).
