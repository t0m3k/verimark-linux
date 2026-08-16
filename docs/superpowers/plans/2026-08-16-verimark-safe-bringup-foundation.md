# VeriMark Safe Bring-up Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a tested, non-destructive foundation for using an already Windows-paired Kensington VeriMark Desktop reader on Arch Linux.

**Architecture:** A small Python package validates and atomically installs the existing pairing credential without exposing secret bytes. A commit-pinned Arch package builds the existing native VeriMark libfprint fork while preserving the `libfprint-2.so=2-64` ABI. A read-only Windows PowerShell probe produces a redacted metadata report that will support a separate credential-export plan.

**Tech Stack:** Python 3.14 standard library and `unittest`, PowerShell 5.1+, Arch `makepkg`/PKGBUILD, Meson/Ninja, libfprint, fprintd, GnuTLS, Nettle/Hogweed, GMP, libgusb.

## Global Constraints

- Target only Kensington VeriMark Desktop `047d:00f2` (K62330WW) in this plan.
- Pin the driver source to commit `66591aae03856bcefa7d7b4c0f08ea630f64b623`; never install from a moving branch.
- Preserve the existing Windows pairing. Never invoke bootstrap, reset, unpair, delete-all, or undocumented destructive opcodes.
- Never print, commit, upload, or include `sub1*.bin`, private-key bytes, registry exports, packet captures, crash dumps, or extracted Windows files in a package.
- Do not change PAM, display-manager, lock-screen, or `sudo` configuration.
- Do not send issues, merge requests, email, or other external communication without explicit user authorization.
- Keep stock Arch `libfprint 1.94.100-1` recoverable and preserve the `libfprint-2.so=2-64` dependency required by `fprintd 1.94.5-2`.
- This plan stops after a package is built and inspected and a redacted Windows discovery report is available. Credential extraction and live sensor mutation require the follow-up plan.

## File map

- `verimark_support/credential.py`: parse and validate the Synaptics `sub1` TLV without returning secret fields.
- `verimark_support/install.py`: determine the fprintd service identity and install a validated blob atomically.
- `verimark_support/cli.py`: stable `validate` and `install` command-line interface with redacted output.
- `verimark_support/__init__.py`: public package exports.
- `tools/verimark-credential`: executable repository-local CLI entry point.
- `tests/fixtures.py`: generate synthetic, non-secret TLV blobs for tests.
- `tests/test_credential.py`: parser, file, permission, and redaction tests.
- `tests/test_install.py`: atomic-install, ownership, replacement, and symlink-safety tests.
- `tests/test_cli.py`: CLI output and exit-code tests.
- `packaging/arch/PKGBUILD`: pinned replacement package for the VeriMark libfprint fork.
- `tests/test_pkgbuild.py`: static safety and ABI assertions for the PKGBUILD.
- `windows/Get-VeriMarkPairingMetadata.ps1`: read-only device/driver/registry metadata collector.
- `windows/Test-VeriMarkPairingMetadata.ps1`: built-in PowerShell assertions for report redaction.
- `docs/windows-discovery.md`: exact Windows execution and return-to-Linux workflow.
- `docs/arch-build.md`: package build, inspection, and rollback preparation.
- `README.md`: project status, security warning, and phase boundaries.

---

### Task 1: Credential parser and redacted validation CLI

**Files:**
- Create: `verimark_support/__init__.py`
- Create: `verimark_support/credential.py`
- Create: `verimark_support/cli.py`
- Create: `tools/verimark-credential`
- Create: `tests/__init__.py`
- Create: `tests/fixtures.py`
- Create: `tests/test_credential.py`
- Create: `tests/test_cli.py`

**Interfaces:**
- Produces: `CredentialError(ValueError)`.
- Produces: `ValidationReport(size: int, sha256: str, tags: tuple[tuple[int, int], ...])`.
- Produces: `validate_blob(blob: bytes) -> ValidationReport`.
- Produces: `validate_file(path: pathlib.Path, require_secure_mode: bool = False) -> ValidationReport`.
- Produces: CLI `verimark-credential validate PATH [--require-secure-mode]` with exit `0` on success and `2` on validation failure.

- [ ] **Step 1: Create synthetic fixture helpers and failing parser tests**

Create `tests/fixtures.py` with deterministic non-secret values:

```python
import struct


def record(tag: int, value: bytes) -> bytes:
    return struct.pack("<HHH", tag, len(value), 0) + value


def valid_blob(order: tuple[int, ...] = (2, 1, 4, 3, 0)) -> bytes:
    values = {
        0: b"",
        1: bytes([0x11]) * 400,
        2: bytes(range(32)),
        3: bytes([0x33]) * 400,
        4: bytes([0x44]) * 420,
    }
    return b"".join(record(tag, values[tag]) for tag in order)
```

Create `tests/test_credential.py` covering valid reordered tags, missing tags
1/2/3, duplicate required tags, incorrect required lengths, truncated headers,
truncated values, a blob over 1 MiB, symlink rejection, and insecure mode
rejection when `require_secure_mode=True`.

The core valid case is:

```python
def test_valid_blob_returns_only_metadata(self):
    blob = valid_blob()
    report = validate_blob(blob)
    self.assertEqual(report.size, len(blob))
    self.assertEqual(report.tags, ((2, 32), (1, 400), (4, 420), (3, 400), (0, 0)))
    self.assertNotIn(bytes(range(32)).hex(), repr(report))
```

- [ ] **Step 2: Run the parser tests and verify they fail**

Run: `python -m unittest tests.test_credential -v`

Expected: import failure for `verimark_support.credential`.

- [ ] **Step 3: Implement the minimal TLV validator**

Create `verimark_support/credential.py` with:

```python
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import os
import stat
import struct

MAX_BLOB_SIZE = 1 << 20
REQUIRED_LENGTHS = {1: 400, 2: 32, 3: 400}


class CredentialError(ValueError):
    pass


@dataclass(frozen=True)
class ValidationReport:
    size: int
    sha256: str
    tags: tuple[tuple[int, int], ...]


def validate_blob(blob: bytes) -> ValidationReport:
    if not blob or len(blob) > MAX_BLOB_SIZE:
        raise CredentialError("credential size is outside the accepted range")
    offset = 0
    seen: set[int] = set()
    tags: list[tuple[int, int]] = []
    while offset < len(blob):
        if len(blob) - offset < 6:
            raise CredentialError("truncated TLV header")
        tag, length, reserved = struct.unpack_from("<HHH", blob, offset)
        if reserved != 0:
            raise CredentialError("non-zero TLV reserved field")
        offset += 6
        if length > len(blob) - offset:
            raise CredentialError("truncated TLV value")
        if tag in REQUIRED_LENGTHS:
            if tag in seen:
                raise CredentialError(f"duplicate required tag {tag}")
            if length != REQUIRED_LENGTHS[tag]:
                raise CredentialError(f"invalid length for required tag {tag}")
            seen.add(tag)
        tags.append((tag, length))
        offset += length
    missing = set(REQUIRED_LENGTHS) - seen
    if missing:
        raise CredentialError("missing required credential tags")
    return ValidationReport(len(blob), sha256(blob).hexdigest(), tuple(tags))


def validate_file(path: Path, require_secure_mode: bool = False) -> ValidationReport:
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise CredentialError("credential path must be a regular non-symlink file")
    if require_secure_mode and stat.S_IMODE(info.st_mode) != 0o600:
        raise CredentialError("credential mode must be exactly 0600")
    if info.st_size > MAX_BLOB_SIZE:
        raise CredentialError("credential file is too large")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    with os.fdopen(fd, "rb", closefd=True) as stream:
        opened = os.fstat(stream.fileno())
        if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
            raise CredentialError("credential changed while being opened")
        blob = stream.read(MAX_BLOB_SIZE + 1)
    return validate_blob(blob)
```

Export these names from `verimark_support/__init__.py`.

- [ ] **Step 4: Run parser tests and verify they pass**

Run: `python -m unittest tests.test_credential -v`

Expected: all credential tests pass.

- [ ] **Step 5: Add failing CLI redaction and exit-code tests**

Create `tests/test_cli.py` using `contextlib.redirect_stdout`,
`redirect_stderr`, and a temporary file. Assert that a valid blob returns `0`
and prints only `valid`, byte size, SHA-256, and tag/length pairs. Assert that
an invalid blob returns `2`, prints a concise error to stderr, and never prints
the synthetic private scalar `bytes(range(32)).hex()`.

- [ ] **Step 6: Run the CLI tests and verify they fail**

Run: `python -m unittest tests.test_cli -v`

Expected: import failure for `verimark_support.cli`.

- [ ] **Step 7: Implement the validation CLI and wrapper**

Implement `verimark_support.cli.main(argv: list[str] | None = None) -> int`
with `argparse`. The `validate` handler calls `validate_file`, prints one line
in this exact form, and catches `CredentialError`, `FileNotFoundError`, and
`PermissionError`:

```text
valid size=<decimal> sha256=<hex> tags=<tag:length,tag:length,...>
```

The error form is `invalid: <reason>` on stderr. The wrapper
`tools/verimark-credential` is:

```python
#!/usr/bin/env python3
from verimark_support.cli import main

raise SystemExit(main())
```

- [ ] **Step 8: Run all Task 1 tests and inspect help output**

Run: `python -m unittest tests.test_credential tests.test_cli -v`

Expected: all tests pass.

Run: `python tools/verimark-credential --help`

Expected: help lists the `validate` command and contains no secret-bearing
examples.

- [ ] **Step 9: Commit Task 1**

```bash
git add verimark_support tools tests
git commit -m "feat: validate VeriMark pairing credentials safely"
```

---

### Task 2: Atomic credential installer

**Files:**
- Create: `verimark_support/install.py`
- Modify: `verimark_support/__init__.py`
- Modify: `verimark_support/cli.py`
- Create: `tests/test_install.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- Consumes: `validate_file(path: Path) -> ValidationReport` from Task 1.
- Produces: `ServiceIdentity(uid: int, gid: int, name: str)`.
- Produces: `resolve_fprintd_identity() -> ServiceIdentity`.
- Produces: `install_credential(source: Path, destination: Path, identity: ServiceIdentity) -> ValidationReport`.
- Produces: CLI `verimark-credential install SOURCE --destination PATH` that requires effective UID 0 and refuses an existing destination.

- [ ] **Step 1: Write failing installer tests**

Create `tests/test_install.py` with temporary directories and mocks for
`os.chown`. Cover:

- a valid source is copied byte-for-byte;
- destination mode is exactly `0600`;
- parent mode is exactly `0700` when newly created;
- destination already exists and remains unchanged;
- destination symlink is rejected;
- invalid source creates no destination;
- a simulated write failure leaves no `.tmp-*` file;
- returned report equals validation of the source;
- blank `systemctl show --property=User --value fprintd.service` resolves to
  root UID/GID, while a named user resolves through `pwd.getpwnam`.

- [ ] **Step 2: Run installer tests and verify they fail**

Run: `python -m unittest tests.test_install -v`

Expected: import failure for `verimark_support.install`.

- [ ] **Step 3: Implement identity resolution and atomic installation**

Create `verimark_support/install.py`. `resolve_fprintd_identity` runs:

```python
subprocess.run(
    ["systemctl", "show", "--property=User", "--value", "fprintd.service"],
    check=True,
    capture_output=True,
    text=True,
)
```

Treat blank output as `ServiceIdentity(0, 0, "root")`; otherwise resolve the
account with `pwd.getpwnam`.

`install_credential` must validate before creating anything, reject a
non-absolute destination, reject an existing destination with `FileExistsError`,
create only the dedicated `verimark` directory, open that directory using
`O_DIRECTORY | O_NOFOLLOW`, create a randomized temporary file using the
directory file descriptor, write in a loop, `fchmod(0600)`, `fchown`, `fsync`,
then rename within the same directory and `fsync` the directory. Close and
unlink the temporary file on every failure. Do not implement replacement in
this milestone.

- [ ] **Step 4: Run installer tests and verify they pass**

Run: `python -m unittest tests.test_install -v`

Expected: all installer tests pass.

- [ ] **Step 5: Add failing CLI install tests**

Add tests asserting that non-root execution returns `2` before touching the
destination, success prints only destination path plus the validation hash,
and an existing destination returns `2` without modification. Mock
`os.geteuid`, `resolve_fprintd_identity`, and `install_credential`; do not run
the tests as root.

- [ ] **Step 6: Implement the install subcommand**

Add `install SOURCE` with default destination
`/var/lib/fprintd/verimark/sub1.bin`. Require `os.geteuid() == 0`, call the
identity resolver, and print:

```text
installed path=<absolute-path> owner=<name> mode=0600 sha256=<hex>
```

Never offer `--force`, `--replace`, delete, bootstrap, or reset options.

- [ ] **Step 7: Run the complete Python suite**

Run: `python -m unittest discover -s tests -v`

Expected: all credential, installer, and CLI tests pass.

- [ ] **Step 8: Commit Task 2**

```bash
git add verimark_support tests
git commit -m "feat: install VeriMark credentials atomically"
```

---

### Task 3: Commit-pinned Arch libfprint package

**Files:**
- Create: `packaging/arch/PKGBUILD`
- Create: `tests/test_pkgbuild.py`
- Create after validation: `packaging/arch/.SRCINFO`
- Modify: `.gitignore`

**Interfaces:**
- Produces: package `libfprint-verimark` version `1.94.10.r1.g66591aa-1`.
- Provides: `libfprint` and `libfprint-2.so=2-64` for the installed fprintd dependency.
- Conflicts: `libfprint`.
- Consumes: source commit `66591aae03856bcefa7d7b4c0f08ea630f64b623`.

- [ ] **Step 1: Write failing PKGBUILD safety tests**

Create `tests/test_pkgbuild.py` to load `packaging/arch/PKGBUILD` as text and
assert all of the following literal requirements:

```python
PIN = "66591aae03856bcefa7d7b4c0f08ea630f64b623"
self.assertIn(f"_commit={PIN}", text)
self.assertIn('#commit=$_commit', text)
self.assertNotIn("pkgver()", text)
self.assertIn("conflicts=(libfprint)", text)
self.assertIn("provides=(libfprint libfprint-2.so)", text)
for dependency in ("gnutls", "nettle", "gmp", "libgusb"):
    self.assertRegex(text, rf"(?m)^  {dependency}$")
self.assertIn('test "$(git rev-parse HEAD)" = "$_commit"', text)
self.assertNotRegex(text, r"sub1.*bin")
```

- [ ] **Step 2: Run the package tests and verify they fail**

Run: `python -m unittest tests.test_pkgbuild -v`

Expected: failure because `packaging/arch/PKGBUILD` does not exist.

- [ ] **Step 3: Create the pinned PKGBUILD**

Base it on Arch's `libfprint 1.94.100-1` PKGBUILD, but set:

```bash
pkgname=libfprint-verimark
pkgver=1.94.10.r1.g66591aa
pkgrel=1
pkgdesc="Library for fingerprint readers with experimental Kensington VeriMark support"
_commit=66591aae03856bcefa7d7b4c0f08ea630f64b623
provides=(libfprint libfprint-2.so)
conflicts=(libfprint)
source=("libfprint::git+https://gitlab.freedesktop.org/s-celles/libfprint.git#commit=$_commit")
b2sums=(SKIP)
```

Copy Arch's current runtime/build/check dependencies, then add runtime
dependencies `gnutls`, `nettle`, and `gmp` because the VeriMark driver links
them directly. In `prepare()`, enter `libfprint` and run the exact commit
comparison from the static test. In `build()`, configure the main tree with
`arch-meson libfprint build -D drivers=all -D installed-tests=false`, compile
it, configure `libfprint/libfprint/drivers/verimark` into
`build-verimark-tests` with `--werror`, and compile that test tree. In
`check()`, run both Meson test suites with `--print-errorlogs`. Install only
the main `build` tree.

- [ ] **Step 4: Run static tests and shell syntax checks**

Run: `python -m unittest tests.test_pkgbuild -v`

Expected: all assertions pass.

Run: `bash -n packaging/arch/PKGBUILD`

Expected: exit `0`.

- [ ] **Step 5: Generate and inspect `.SRCINFO`**

Run from `packaging/arch`: `makepkg --printsrcinfo > .SRCINFO`

Expected: package base is `libfprint-verimark`, source contains the exact
commit fragment, and dependencies include `gnutls`, `nettle`, and `gmp`.

Run: `git diff --check`

Expected: exit `0`.

- [ ] **Step 6: Verify the remote source and build without installing**

Run from `packaging/arch`: `makepkg --verifysource`

Expected: the Git source resolves and `prepare()` later enforces the exact
commit.

Run from `packaging/arch`: `makepkg --cleanbuild --clean --syncdeps --noconfirm`

Expected: a signed-local package file is produced only after both Meson test
suites pass. If dependency installation needs privilege, obtain explicit user
approval before this command. Do not use `--skippgpcheck`, `--nocheck`, or
`--nodeps`.

- [ ] **Step 7: Inspect package metadata and contents**

Run: `pacman -Qp packaging/arch/libfprint-verimark-*.pkg.tar.*`

Expected: `libfprint-verimark 1.94.10.r1.g66591aa-1`.

Run: `pacman -Qip packaging/arch/libfprint-verimark-*.pkg.tar.*`

Expected: provides `libfprint` and `libfprint-2.so=2-64`, conflicts with
`libfprint`, and lists no credential file.

Run: `pacman -Qlp packaging/arch/libfprint-verimark-*.pkg.tar.*`

Expected: normal libfprint library, headers, GIR, udev/hwdb, docs, and
metainfo; no `sub1`, Windows, capture, or crash artifacts.

- [ ] **Step 8: Commit Task 3**

```bash
git add .gitignore packaging/arch tests/test_pkgbuild.py
git commit -m "build: package pinned VeriMark libfprint fork"
```

---

### Task 4: Read-only Windows pairing discovery

**Files:**
- Create: `windows/Get-VeriMarkPairingMetadata.ps1`
- Create: `windows/Test-VeriMarkPairingMetadata.ps1`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `verimark-windows-metadata.json`, deliberately ignored by Git.
- Report schema: `schema`, `generatedUtc`, `device`, `driver`, and `registryValueMetadata`.
- Never produces: registry value data, DPAPI plaintext, private keys, biometric templates, or modifications.

- [ ] **Step 1: Create the PowerShell report test first**

Write `windows/Test-VeriMarkPairingMetadata.ps1` to accept `-Path`, parse JSON,
and fail unless:

- `schema` equals `verimark-pairing-metadata-v1`;
- `device.instanceId` begins with `USB\\VID_047D&PID_00F2`;
- `driver.providerName`, `driver.version`, `driver.infName`, and
  `driver.service` are non-empty;
- every registry entry contains exactly `path`, `name`, `kind`, and
  `byteLength` properties;
- recursive property-name inspection finds none of the exact names `data`,
  `valueBytes`, `plaintext`, or `privateKey`;
- serialized JSON contains no hexadecimal string longer than 64 characters.

The test prints `metadata report passed redaction checks` and exits `0` only
when all assertions pass.

- [ ] **Step 2: Implement the read-only collector**

Write `windows/Get-VeriMarkPairingMetadata.ps1` with
`[CmdletBinding(SupportsShouldProcess=$false)]`, `Set-StrictMode -Version
Latest`, and `$ErrorActionPreference = 'Stop'`.

The script must:

1. Query `Get-PnpDevice -PresentOnly` for the exact VID/PID.
2. Query `Win32_PnPSignedDriver` for the matching PNPDeviceID.
3. Read the device instance registry key under
   `HKLM:\SYSTEM\CurrentControlSet\Enum\USB` and derive its `Driver` and
   `Service` values.
4. Inspect only these derived scopes: the exact Enum instance key, its
   `Device Parameters` child, its exact class-driver key under
   `HKLM:\SYSTEM\CurrentControlSet\Control\Class`, and its exact service key
   under `HKLM:\SYSTEM\CurrentControlSet\Services`.
5. For each value, record only registry path, value name, registry kind, and
   byte length. Never place the value itself in an object or output stream.
6. Write UTF-8 JSON only after recursively checking the object property names
   against the forbidden names in the test script.
7. Refuse an existing output path unless `-Force` is supplied. `-Force`
   replaces only the report file and does not change registry state.

- [ ] **Step 3: Add generated reports to `.gitignore`**

Add:

```gitignore
verimark-windows-metadata*.json
```

- [ ] **Step 4: Run Windows parser and redaction checks**

On the paired Windows installation, open an elevated PowerShell in the project
directory and run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\windows\Get-VeriMarkPairingMetadata.ps1 -OutputPath .\verimark-windows-metadata.json
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\windows\Test-VeriMarkPairingMetadata.ps1 -Path .\verimark-windows-metadata.json
```

Expected: the first command identifies one `047d:00f2` device and the second
prints `metadata report passed redaction checks`. If multiple matching devices
exist, the collector must stop and require an explicit `-InstanceId`.

- [ ] **Step 5: Review the report locally without committing it**

Return the ignored JSON file to this project by direct local transfer. Run:

```bash
git check-ignore -v verimark-windows-metadata.json
python -m json.tool verimark-windows-metadata.json
git status --short
```

Expected: `.gitignore` matches the report, JSON is valid, and `git status`
does not list it. Review only names, types, and sizes to determine the exact
pairing record for the follow-up exporter plan.

- [ ] **Step 6: Commit Task 4 source files only**

```bash
git add .gitignore windows
git commit -m "feat: discover VeriMark Windows pairing metadata safely"
```

---

### Task 5: Operator documentation and foundation verification

**Files:**
- Create: `README.md`
- Create: `docs/windows-discovery.md`
- Create: `docs/arch-build.md`

**Interfaces:**
- Consumes: Tasks 1–4 commands and artifacts.
- Produces: a clear boundary between safe foundation work and the later live-device plan.

- [ ] **Step 1: Write README security and status sections**

Document the exact device ID, unsupported stock behavior, chosen fork commit,
credential sensitivity, commands for the Python test suite, package tests,
and Windows metadata probe. State prominently that the current phase does not
extract a credential, install the package, modify PAM, or mutate the sensor.

- [ ] **Step 2: Write the Windows discovery runbook**

Document prerequisites, elevated PowerShell commands from Task 4, expected
fields, redaction validation, direct local transfer, and deletion of the
report after the follow-up plan is written. Include an explicit warning not to
send `sub1.bin`, registry exports, or raw registry values.

- [ ] **Step 3: Write the Arch build and rollback-preparation runbook**

Document:

```bash
pacman -Q libfprint fprintd
lsusb -d 047d:00f2
python -m unittest discover -s tests -v
makepkg --verifysource
makepkg --cleanbuild --clean --syncdeps --noconfirm
pacman -Qip libfprint-verimark-*.pkg.tar.*
pacman -Qlp libfprint-verimark-*.pkg.tar.*
```

Also document how to confirm the stock package is in `/var/cache/pacman/pkg`
or available from `extra`, but do not document patched-package installation in
this phase.

- [ ] **Step 4: Run the complete local verification suite**

Run: `python -m unittest discover -s tests -v`

Expected: all tests pass.

Run: `git diff --check`

Expected: exit `0`.

Run: `git status --short`

Expected: only Task 5 documentation is uncommitted; all secret/report patterns
remain ignored.

- [ ] **Step 5: Commit Task 5**

```bash
git add README.md docs/windows-discovery.md docs/arch-build.md
git commit -m "docs: add VeriMark bring-up runbooks"
```

- [ ] **Step 6: Mark the foundation ready for its follow-up plan**

Run: `git log --oneline --decorate -6`

Expected: separate commits for specification, credential validation,
credential installation, Arch packaging, Windows discovery, and runbooks.

The next plan may begin only after reviewing the redacted Windows metadata. It
will specify the exact DPAPI export operation, credential installation,
patched-package installation, read-only sensor inspection, one test
enrollment, repeated verification, targeted deletion, reboot tests, and final
Windows regression check.
