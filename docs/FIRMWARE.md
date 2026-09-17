# Firmware — what FuraxXZ actually knows

## Status: EXPERIMENTAL

No real Sony F8331 firmware image has been analyzed by this project yet
(none is available in the development environment — see
`docs/ENVIRONMENT.md`). Everything below is software-only capability,
not a verified result on a real Sony service ROM.

## What `furaxxz firmware analyze` actually detects

It reads real magic bytes/structure — it never guesses:

| Format | Detection | Notes |
|---|---|---|
| ZIP archive | `PK\x03\x04` / `PK\x05\x06` | Lists entries, flags known partition image names, checks CRC |
| TAR archive | `tarfile.is_tarfile()` | Same partition detection |
| gzip | `\x1f\x8b` | Reports compressed, does not auto-decompress |
| Android sparse image | `0xED26FF3A` LE | Flags that `simg2img` conversion is required before further inspection (not done automatically) |
| ext4 raw image | superblock magic `0xEF53` at offset 1024+0x38 | — |
| Android boot image | `ANDROID!` magic | Parses the v0 header: kernel/ramdisk/second sizes, page size, header version |
| Anything else | — | Reported as `unknown`, with a note — **never fabricated** |

## What it does NOT know

Sony's official **FTF** (Flash Tool Firmware) / **SIN** container format
used by Sony's own flashing tools (Flashtool/Newflasher/XFlash-era tools)
is a proprietary, partially-undocumented container. This project has not
implemented a SIN/FTF parser — doing so correctly (including any
signature/hash verification Sony's tooling performs) is future,
EXPERIMENTAL work, not v0.1 scope. If `furaxxz firmware analyze` is
pointed at a `.ftf`/`.sin` file today, it will most likely report
`format: unknown` truthfully, rather than pretend to understand it.

## Extraction

`furaxxz firmware extract` only supports ZIP and TAR containers, and
defaults to **targeted extraction** (only files whose basename matches a
known partition image name: `boot.img`, `system.img`, `vendor.img`, etc.),
per the project's "no assumed structure" rule. `--all` disables the name
filter. TAR extraction is guarded against path traversal.

## The fundamental rule

> A technically possible modification is NOT automatically a flashable
> one.

Nothing in this codebase claims flash-readiness. See `docs/FLASHING.md`
and `docs/SECURITY.md` for how compatibility is reported (`UNKNOWN` until
verified) and gated.
