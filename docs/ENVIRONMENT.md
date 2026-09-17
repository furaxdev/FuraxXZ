# FuraxXZ — Environment Audit

_Generated during Phase 0. Reflects the actual state of the development container at audit time — nothing here is assumed._

Audit date: 2026-09-17

## Host

| Item | Value |
|---|---|
| OS / Kernel | Linux 6.18.44-fc-v33 (x86_64) |
| Architecture | x86_64 |
| User | root (uid=0, gid=0) |
| Disk (`/`) | 252G total, 7.1G used, 30G available (20% used) |

## Toolchain

| Tool | Status | Version / Path |
|---|---|---|
| git | ✅ present | 2.43.0 |
| Java (JDK) | ✅ present | OpenJDK 21.0.10 (Ubuntu build) |
| Gradle | ✅ present | 8.14.3 (`/opt/gradle/bin/gradle`), bundled Kotlin 2.0.21 |
| Android SDK | ❌ **missing** | `ANDROID_HOME` / `ANDROID_SDK_ROOT` unset, no `sdkmanager` on PATH |
| Python | ✅ present | 3.11.15 |
| pip | ✅ present | 24.0 (`python3 -m pip`) |
| Node.js | ✅ present | v22.22.2 |
| npm | ✅ present | 10.9.7 |
| unzip / zip | ✅ present | `/usr/bin/unzip`, `/usr/bin/zip` |
| tar | ✅ present | `/usr/bin/tar` |
| file | ✅ present | `/usr/bin/file` |
| sha256sum | ✅ present | `/usr/bin/sha256sum` |
| openssl | ✅ present | `/usr/bin/openssl` |
| jq | ✅ present | `/usr/bin/jq` |
| xxd | ❌ missing | not installed (use `od -An -tx1` as a fallback) |
| apktool | ❌ missing | not installed |

## Consequences for this project

- **Android SDK was not pre-installed**, but this container does have outbound network access (through the pre-configured proxy), so the SDK (`platform-tools`, `platforms;android-34`, `build-tools;34.0.0`) and the Gradle wrapper were installed/generated during Phase 0–1. `./gradlew assembleDebug` and `./gradlew testDebugUnitTest` were both run successfully for `apps/furaxxz` — the app **does build** and its JVM unit tests **do pass** (verified: `app-debug.apk` produced, `CategoryTest` 3/3 green). Maven Central occasionally returns HTTP 429 through the proxy on a cold cache; retrying resolves it. A machine without network access would need a locally provisioned SDK — `furaxxz doctor` reports whether `ANDROID_HOME`/`sdkmanager` are present.
- No physical Sony F8331 (`kagura`) device or firmware image is attached to this container. Every firmware/security claim in this repo is therefore software-only analysis; anything requiring the real device is marked `BLOCKED` or `EXPERIMENTAL` until verified on hardware.
- No `apktool`/`xxd`: extraction tooling avoids depending on them; Python's own `zipfile`, `tarfile`, and `struct` modules are used instead where possible.
- Python 3.11 + stdlib is the implementation language for the CLI (`furaxxz`) since it's guaranteed present, needs no network install, and keeps the toolchain lightweight (per project rule: no unnecessary dependencies).

## Re-running this audit

```
python3 tools/cli/furaxxz doctor
```

`furaxxz doctor` re-checks this table programmatically and should be re-run whenever the container/environment changes.
