# VeriMark Desktop Factory-Fresh Beta Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `v0.1.0-beta.1` and an AUR package that let a factory-fresh Kensington VeriMark Desktop (`047d:00f2`) pair and enroll through ordinary fprintd interfaces, while preserving an already Windows-paired reader and never exposing pairing secrets.

**Architecture:** Keep the protocol implementation in the libfprint VeriMark driver as an ordered patch series against immutable commit `66591aae03856bcefa7d7b4c0f08ea630f64b623`. An asynchronous provisioning state machine starts only from the enroll vfunc, persists a versioned per-device recovery identity before the USB mutation, finalizes it through a dirfd-safe storage backend, and then resumes the existing TLS/enrollment path. The project repository also provides immutable Arch packaging, a read-only `verimarkctl`, automated security gates, and redacted hardware evidence.

**Tech Stack:** C11, GLib/GObject/GIO, libfprint `FpiSsm`, OpenSSL, Meson, Python 3 standard library, `unittest`, Bash, Arch `makepkg`/`devtools`, GitHub Actions.

## Global Constraints

- The supported device is only Kensington VeriMark Desktop USB ID `047d:00f2`; `047d:8054` and all other Tudor-family devices are out of scope.
- Pairing begins only after an explicit fprintd `EnrollStart`; discovery, daemon startup, read-only diagnostics, and device open remain non-mutating.
- All pairing USB work uses libfprint asynchronous state machines; nested main loops, synchronous wrappers, and unbounded waits are forbidden.
- An already-paired or ambiguous response is terminal: never reset, replace, re-pair, generate a second identity, or retry with a different identity.
- The public beta is blocked unless an interrupted transaction has a demonstrated same-identity recovery path that cannot replace the sensor pairing slot.
- State lives under `/var/lib/fprint/verimark/`; directories are `0700`, files are root-owned `0600`, and every mutation uses dirfd-pinned, symlink-safe, atomic, no-replace writes with required `fsync` boundaries.
- Private keys, credential blobs, certificate bodies, session secrets, biometric data, raw serials, Windows registry data, packet captures, and unrestricted journals must never appear in logs, reports, commits, packages, or release archives.
- Preserve the existing Windows-compatible credential reader internally, but ship no Windows extraction, DPAPI, registry, import, export, or credential-install tooling.
- The package must not pair hardware, enable PAM, enroll a finger, reset a device, or create a credential during installation or upgrade.
- The AUR package is `libfprint-verimark`, provides/conflicts with `libfprint`, and preserves the stock `libfprint-2.so` ABI required by fprintd.
- Do not create a GitHub repository, release, issue, author contact, AUR package, or upstream merge request without a fresh explicit user authorization for that external action.
- The existing Windows-paired reader and its credential are protected fixtures: never remove the credential, send an unauthenticated pairing request to that reader, reset it, or delete an unknown template.
- Run all simulated interruption tests before the single physical pairing attempt on the ordered factory-fresh reader; do not deliberately interrupt that unit.

## File and Component Map

Project-repository files:

- `.gitignore`: excludes `.driver-worktrees/`, build roots, packages, hardware-local reports, credentials, traces, and transient reports.
- `patches/libfprint/series`: authoritative ordered patch names applied to the pinned libfprint commit.
- `patches/libfprint/*.patch`: reviewable Desktop-only driver, persistence, provisioning, and test changes with preserved authorship.
- `tools/export-libfprint-patches`: reproducibly exports the reviewed driver branch into `patches/libfprint/`.
- `tools/verimarkctl`: installed read-only CLI entry point.
- `verimark_support/credential.py`: pure parser for the legacy 1284-byte `sub1` credential.
- `verimark_support/probe.py`: injectable, read-only system and fprintd observations.
- `verimark_support/report.py`: typed status model and redaction-safe JSON rendering.
- `verimark_support/cli.py`: `status`, `doctor`, and `report` argument handling only.
- `packaging/arch/PKGBUILD`: immutable build, check, install, ABI, and file-permission rules.
- `packaging/arch/.SRCINFO`: generated AUR metadata.
- `packaging/arch/verimarkctl.1`: installed command manual.
- `tests/`: project, patch-series, CLI, redaction, package, archive, and release-policy tests.
- `docs/hardware/`: redacted reference-reader and factory-fresh acceptance reports.
- `docs/release/`: security notice, installation, rollback, release checklist, and beta release notes.
- `.github/workflows/ci.yml`: Python, patch-application, libfprint, sanitizer, and package-source checks.
- `.github/ISSUE_TEMPLATE/verimark-report.yml`: privacy-safe diagnostic issue form.
- `README.md`, `LICENSES/`, `SECURITY.md`, `CONTRIBUTING.md`: public project metadata.

Files created or changed by the driver patches after they are applied to libfprint:

- `libfprint/drivers/verimark/bootstrap.[ch]`: pure identity generation, request construction, and complete response parsing.
- `libfprint/drivers/verimark/persist-format.[ch]`: versioned record serializer/parser and secret clearing.
- `libfprint/drivers/verimark/persist-store.[ch]`: dirfd-safe storage backend and injectable filesystem operations.
- `libfprint/drivers/verimark/provision.[ch]`: asynchronous pairing/recovery `FpiSsm` and terminal-result mapping.
- `libfprint/drivers/verimark/verimark.[ch]`: non-mutating open plus enroll-time provisioning integration.
- `libfprint/drivers/verimark/meson.build`: Desktop-only sources and unit tests.
- `libfprint/drivers/verimark/tests/test-bootstrap.c`: synthetic protocol vectors.
- `libfprint/drivers/verimark/tests/test-persist-format.c`: record parser and serializer tests.
- `libfprint/drivers/verimark/tests/test-persist-store.c`: filesystem fault and race tests.
- `libfprint/drivers/verimark/tests/test-provision.c`: fake-transport state-machine tests.
- `libfprint/drivers/verimark/tests/fuzz-persist-format.c`: persistence parser fuzz target.
- `libfprint/drivers/verimark/tests/fuzz-pair-response.c`: pair-response parser fuzz target.
- `libfprint/drivers/verimark/tools/verimark-pair-lab.c`: uninstalled developer-only recovery-characterization harness.

## Milestone Gates

- **G1 — protocol recoverability:** Task 7 must identify and simulate a same-identity recovery operation before integration, and Task 14 must confirm its assumptions during the single normal fprintd pairing operation. If either half fails, keep factory pairing behind the existing experimental opt-in and stop release work.
- **G2 — existing-reader safety:** Task 13 must show no pairing command is sent and the current Windows-paired reader still verifies after restart, reconnect, and reboot.
- **G3 — factory-fresh acceptance:** Task 14 must show exactly one pair operation and stable persisted identity through the full acceptance matrix.
- **G4 — release reproducibility:** Task 15 must pass clean-chroot, archive, history, ABI, upgrade, and rollback checks from immutable inputs.
- **G5 — external authorization:** Task 16 pauses before each GitHub or AUR mutation and proceeds only after explicit user approval.

---

### Task 1: Create the Clean Factory-Beta Lineage

**Files:**
- Modify: `.gitignore`
- Carry forward: `tests/__init__.py`
- Carry forward: `tests/fixtures.py`
- Carry forward: `tests/test_cli.py`
- Carry forward: `tests/test_credential.py`
- Carry forward: `tools/verimark-credential`
- Carry forward: `verimark_support/__init__.py`
- Carry forward: `verimark_support/cli.py`
- Carry forward: `verimark_support/credential.py`
- Carry forward: `packaging/arch/PKGBUILD`
- Carry forward: `packaging/arch/.SRCINFO`
- Carry forward: `packaging/arch/fix-generated-data-checks.patch`
- Carry forward: `tests/test_arch_package.py`

**Interfaces:**
- Consumes: `main` at the commit containing this plan; reviewed commits `8012553`, `723ccef`, `cbba957`, and `4bbe85c`.
- Produces: branch `feature/verimark-factory-beta` in isolated worktree `.worktrees/verimark-factory-beta`, with credential validation and deterministic Arch package tests but no Windows or PAM tooling.

- [ ] **Step 1: Create the isolated worktree using the required worktree skill**

Run `superpowers:using-git-worktrees`, then execute:

```bash
git worktree add .worktrees/verimark-factory-beta -b feature/verimark-factory-beta main
```

Expected: a clean worktree whose `HEAD` contains this plan.

- [ ] **Step 2: Carry forward only the reviewed safe commits**

```bash
git cherry-pick 8012553 723ccef cbba957 4bbe85c
```

Expected: four clean cherry-picks; `windows/`, `verimark_support/install.py`, `tests/test_install.py`, and PAM documentation remain absent.

- [ ] **Step 3: Add lineage-policy tests before changing ignores**

Create `tests/test_release_lineage.py` with assertions that the forbidden paths are absent, `.gitignore` contains the exact sensitive patterns below, and `git ls-files` contains no filename matching them:

```python
FORBIDDEN_PATHS = {
    "windows",
    "verimark_support/install.py",
    "tests/test_install.py",
    "docs/fingerprint-first-pam-design.md",
}
SENSITIVE_PATTERNS = (
    "sub1*.bin",
    "*.pcap",
    "*.pcapng",
    "*.reg",
    "hardware-local/",
    ".driver-worktrees/",
)
```

- [ ] **Step 4: Run the lineage test and observe the missing ignore entries**

```bash
python -m unittest -v tests.test_release_lineage
```

Expected: FAIL because `.driver-worktrees/` and `hardware-local/` are not yet ignored.

- [ ] **Step 5: Add the exact private-artifact ignore policy**

Append these entries to `.gitignore` without removing existing rules:

```gitignore
.driver-worktrees/
hardware-local/
sub1*.bin
*.pcap
*.pcapng
*.reg
*.pkg.tar.*
```

- [ ] **Step 6: Verify the clean baseline**

```bash
python -m unittest discover -s tests -v
git ls-files | grep -E '(^windows/|sub1.*\.bin$|\.pcap(ng)?$|\.reg$|(^|/)install\.py$)'
git status --short
```

Expected: all collected tests PASS; the `grep` command exits 1 with no output; only the intentional `.gitignore` and new lineage-test changes are present.

- [ ] **Step 7: Commit the lineage guard**

```bash
git add .gitignore tests/test_release_lineage.py
git commit -m "test: guard public VeriMark release lineage"
```

### Task 2: Establish a Reproducible Driver Patch Workflow

**Files:**
- Create: `patches/libfprint/series`
- Create: `tools/export-libfprint-patches`
- Create: `tests/test_patch_series.py`
- Modify: `.gitignore`
- Modify: `packaging/arch/PKGBUILD`

**Interfaces:**
- Consumes: external base commit `66591aae03856bcefa7d7b4c0f08ea630f64b623`; ignored driver checkout `.driver-worktrees/libfprint`.
- Produces: newline-delimited `patches/libfprint/series`; executable `tools/export-libfprint-patches BASE_COMMIT DRIVER_REF`; package application in exactly that order.

- [ ] **Step 1: Write failing patch-series contract tests**

In `tests/test_patch_series.py`, define `BASE_COMMIT =
"66591aae03856bcefa7d7b4c0f08ea630f64b623"` and add named tests for a
nonempty ordered unique series, plain patch filenames, absence of unlisted
patches, mail headers and license-compatible target files, clean application
to the exact base, PKGBUILD application in series order, and exporter refusal
for a dirty or wrong-base checkout.

The filename validator accepts only `^[0-9]{4}-[a-z0-9][a-z0-9-]*\.patch$` and rejects `/`, `..`, blank lines, duplicates, and symlinks.

- [ ] **Step 2: Run the new contract tests and confirm the missing workflow**

```bash
python -m unittest -v tests.test_patch_series
```

Expected: FAIL because `patches/libfprint/series` and `tools/export-libfprint-patches` do not exist.

- [ ] **Step 3: Implement the exporter with deterministic mail patches**

`tools/export-libfprint-patches` must:

```text
1. require exactly BASE_COMMIT and DRIVER_REF arguments;
2. resolve BASE_COMMIT to exactly 66591aae03856bcefa7d7b4c0f08ea630f64b623;
3. reject a dirty `.driver-worktrees/libfprint` checkout;
4. reject merges in BASE_COMMIT..DRIVER_REF;
5. export with `git format-patch --zero-commit --no-signature --numbered-files`;
6. normalize names to `0001-subject.patch`, `0002-subject.patch`, and so on;
7. write a sibling temporary directory and atomically rename it into place;
8. write `series` from the exact exported order; and
9. leave the previous series untouched on any failure.
```

Use `mktemp -d` and a cleanup trap. Do not accept an arbitrary output directory.

- [ ] **Step 4: Seed the driver branch with the existing generated-data fix**

Create `.driver-worktrees/libfprint` from the exact fork commit, create branch
`verimark-factory-beta-driver`, apply
`packaging/arch/fix-generated-data-checks.patch`, and commit it as `build: make
generated-data checks deterministic`. Export it using:

```bash
git clone https://gitlab.freedesktop.org/s-celles/libfprint.git .driver-worktrees/libfprint
git -C .driver-worktrees/libfprint checkout --detach 66591aae03856bcefa7d7b4c0f08ea630f64b623
git -C .driver-worktrees/libfprint switch -c verimark-factory-beta-driver
git -C .driver-worktrees/libfprint apply ../../packaging/arch/fix-generated-data-checks.patch
git -C .driver-worktrees/libfprint add data/autosuspend.hwdb libfprint/fprint-list-udev-hwdb.c tests/meson.build
git -C .driver-worktrees/libfprint commit -m "build: make generated-data checks deterministic"
tools/export-libfprint-patches 66591aae03856bcefa7d7b4c0f08ea630f64b623 verimark-factory-beta-driver
```

Expected: `series` lists every mail patch once, in commit order.

Configure the reusable full and standalone test builds:

```bash
meson setup .driver-worktrees/libfprint/build .driver-worktrees/libfprint -Ddrivers=all -Dinstalled-tests=false -Dwerror=true
meson setup .driver-worktrees/libfprint/build-verimark-tests .driver-worktrees/libfprint/libfprint/drivers/verimark -Dwerror=true
```

Expected: both build directories configure against the same exact source
checkout.

- [ ] **Step 5: Make PKGBUILD apply the checked series**

Replace its single local patch application with a loop that reads only validated entries from `patches/libfprint/series`; include every listed patch in `source=()` and `b2sums=()`. The `prepare()` phase applies with:

```bash
while IFS= read -r patch_name; do
  git apply --index "${srcdir}/${patch_name}"
done < "${srcdir}/series"
```

- [ ] **Step 6: Verify patch determinism and package metadata**

```bash
python -m unittest -v tests.test_patch_series tests.test_arch_package
(cd packaging/arch && makepkg --printsrcinfo) > /tmp/verimark-srcinfo.generated
diff -u packaging/arch/.SRCINFO /tmp/verimark-srcinfo.generated
```

Expected: tests PASS and the metadata diff is empty after regenerating `packaging/arch/.SRCINFO` from its directory.

- [ ] **Step 7: Commit the patch workflow**

```bash
git add .gitignore patches/libfprint tools/export-libfprint-patches tests/test_patch_series.py packaging/arch/PKGBUILD packaging/arch/.SRCINFO
git commit -m "build: export deterministic libfprint patch series"
```

### Task 3: Enforce the Desktop-Only Support Boundary

**Files:**
- Modify in driver: `libfprint/drivers/verimark/verimark.c`
- Modify in driver: `libfprint/drivers/verimark/meson.build`
- Create in driver: `libfprint/drivers/verimark/tests/test-supported-devices.c`
- Modify: `tests/test_arch_package.py`
- Regenerate: `patches/libfprint/series`
- Regenerate: `packaging/arch/.SRCINFO`

**Interfaces:**
- Consumes: libfprint device table and Meson driver registration.
- Produces: exactly one public VeriMark USB match, `{ .vid = 0x047d, .pid = 0x00f2 }`; no `0x8054` match in driver data, udev rules, hwdb, or package artifacts.

- [ ] **Step 1: Write failing driver and package tests**

The C test enumerates the driver id table and asserts:

```c
g_assert_true (has_usb_id (0x047d, 0x00f2));
g_assert_false (has_usb_id (0x047d, 0x8054));
g_assert_cmpuint (count_vendor_matches (0x047d), ==, 1);
```

Add Python artifact checks that `047d:8054`, `047D:8054`, `v047Dp8054`, and `VID_047D&PID_8054` do not occur in generated hwdb, udev rules, installed files, or package metadata.

- [ ] **Step 2: Run the focused tests and confirm the IT device is exposed**

```bash
meson test -C .driver-worktrees/libfprint/build-verimark-tests test-supported-devices --print-errorlogs
python -m unittest -v tests.test_arch_package
```

Expected: FAIL because the inherited fork still registers `047d:8054`.

- [ ] **Step 3: Restrict registration without deleting reusable protocol code**

Remove `047d:8054` from the public device table and generated device metadata. Keep unrelated IT implementation files unregistered so the beta does not claim support and the code remains separable for future work.

- [ ] **Step 4: Regenerate derived libfprint data and run the full driver suite**

```bash
meson compile -C .driver-worktrees/libfprint/build
meson compile -C .driver-worktrees/libfprint/build-verimark-tests
meson test -C .driver-worktrees/libfprint/build --print-errorlogs
meson test -C .driver-worktrees/libfprint/build-verimark-tests --print-errorlogs
```

Expected: all upstream and VeriMark tests PASS; generated data contains `047d:00f2` and no `047d:8054`.

- [ ] **Step 5: Export, package-test, and commit**

```bash
git -C .driver-worktrees/libfprint add libfprint/drivers/verimark
git -C .driver-worktrees/libfprint commit -m "driver: limit VeriMark beta to Desktop reader"
tools/export-libfprint-patches 66591aae03856bcefa7d7b4c0f08ea630f64b623 verimark-factory-beta-driver
python -m unittest -v tests.test_patch_series tests.test_arch_package
git add patches/libfprint packaging/arch tests/test_arch_package.py
git commit -m "feat: publish Desktop-only driver series"
```

### Task 4: Define Pairing Identity and Versioned Persistence Records

**Files:**
- Create in driver: `libfprint/drivers/verimark/persist-format.h`
- Create in driver: `libfprint/drivers/verimark/persist-format.c`
- Modify in driver: `libfprint/drivers/verimark/bootstrap.h`
- Modify in driver: `libfprint/drivers/verimark/bootstrap.c`
- Create in driver: `libfprint/drivers/verimark/tests/test-persist-format.c`
- Modify in driver: `libfprint/drivers/verimark/meson.build`
- Regenerate: `patches/libfprint/series`

**Interfaces:**
- Consumes: existing `VerimarkPairingData` fields `client_cert[400]`, `client_priv_be[32]`, and `server_pub_uncompressed[65]`; canonical 1284-byte legacy `sub1` encoder/validator.
- Produces:

```c
typedef enum {
  VERIMARK_PERSIST_PENDING = 1,
  VERIMARK_PERSIST_READY = 2,
} VerimarkPersistKind;

typedef struct {
  guint8 client_priv_be[32];
  guint8 client_cert[400];
} VerimarkBootstrapIdentity;

typedef struct {
  guint16 format_version;
  VerimarkPersistKind kind;
  guint8 biometric_serial[6];
  union {
    VerimarkBootstrapIdentity pending;
    guint8 sub1[1284];
  } body;
} VerimarkPersistRecord;

gboolean verimark_bootstrap_identity_generate (VerimarkBootstrapIdentity *out,
                                                GError **error);
void verimark_bootstrap_identity_clear (VerimarkBootstrapIdentity *identity);
GBytes *verimark_persist_serialize (const VerimarkPersistRecord *record,
                                    GError **error);
gboolean verimark_persist_parse (GBytes *bytes,
                                 const guint8 expected_serial[6],
                                 VerimarkPersistRecord *out,
                                 GError **error);
void verimark_persist_record_clear (VerimarkPersistRecord *record);
```

The version-1 wire header is exactly: 8 bytes `VMKPAIR\0`, little-endian `u16 version=1`, `u8 kind`, `u8 reserved=0`, 6 raw serial bytes, little-endian `u32 body_length`, 32-byte SHA-256 of the body, then the body. Pending body length is 432 bytes; ready body length is 1284 bytes.

- [ ] **Step 1: Write parser tests before the implementation**

Cover round trips for pending and ready records plus exact rejection of bad magic, version 0/2, kind 0/3, nonzero reserved byte, short and oversized body, wrong body length, wrong serial, digest mismatch, invalid private scalar, malformed client certificate, and invalid legacy ready credential.

- [ ] **Step 2: Run the parser test and confirm it fails to link**

```bash
meson test -C .driver-worktrees/libfprint/build-verimark-tests test-persist-format --print-errorlogs
```

Expected: FAIL because the persistence symbols are not implemented.

- [ ] **Step 3: Split identity generation from the USB exchange**

Move P-256 private-key and client-certificate generation out of the existing synchronous bootstrap function into `verimark_bootstrap_identity_generate()`. Ensure failure clears the entire output and every exit path calls `OPENSSL_cleanse()` through the public clear functions.

- [ ] **Step 4: Implement strict record serialization and parsing**

Use checked addition before allocating, require the exact total length, compare SHA-256 with `CRYPTO_memcmp()`, parse into a temporary zeroed record, validate the contained identity or legacy credential, then copy to `out` only on success.

- [ ] **Step 5: Run focused tests under sanitizers**

```bash
meson setup --wipe .driver-worktrees/libfprint/build-verimark-asan .driver-worktrees/libfprint/libfprint/drivers/verimark -Db_sanitize=address,undefined -Dwerror=true
meson test -C .driver-worktrees/libfprint/build-verimark-asan test-persist-format --print-errorlogs
```

Expected: all persistence-format tests PASS with no sanitizer finding.

- [ ] **Step 6: Export and commit**

```bash
git -C .driver-worktrees/libfprint add libfprint/drivers/verimark
git -C .driver-worktrees/libfprint commit -m "feat: define versioned VeriMark pairing records"
tools/export-libfprint-patches 66591aae03856bcefa7d7b4c0f08ea630f64b623 verimark-factory-beta-driver
python -m unittest -v tests.test_patch_series
git add patches/libfprint
git commit -m "feat: add versioned pairing-record patch"
```

### Task 5: Implement the Symlink-Safe Persistence Store

**Files:**
- Create in driver: `libfprint/drivers/verimark/persist-store.h`
- Create in driver: `libfprint/drivers/verimark/persist-store.c`
- Create in driver: `libfprint/drivers/verimark/tests/test-persist-store.c`
- Modify in driver: `libfprint/drivers/verimark/meson.build`
- Regenerate: `patches/libfprint/series`

**Interfaces:**
- Consumes: `VerimarkPersistRecord`, `verimark_persist_parse()`, and `verimark_persist_serialize()` from Task 4.
- Produces:

```c
typedef enum {
  VERIMARK_STORE_MISSING,
  VERIMARK_STORE_PENDING_FOUND,
  VERIMARK_STORE_READY_FOUND,
  VERIMARK_STORE_CORRUPT,
  VERIMARK_STORE_IO_ERROR,
} VerimarkStoreResult;

typedef struct _VerimarkPersistStore VerimarkPersistStore;

VerimarkPersistStore *verimark_persist_store_open (const char *root,
                                                   GError **error);
VerimarkStoreResult verimark_persist_store_load (VerimarkPersistStore *store,
                                                 const guint8 serial[6],
                                                 VerimarkPersistRecord *out,
                                                 GError **error);
gboolean verimark_persist_store_publish_pending (VerimarkPersistStore *store,
                                                 const VerimarkPersistRecord *record,
                                                 GError **error);
gboolean verimark_persist_store_publish_ready (VerimarkPersistStore *store,
                                               const VerimarkPersistRecord *pending,
                                               const VerimarkPersistRecord *ready,
                                               GError **error);
void verimark_persist_store_free (VerimarkPersistStore *store);
```

Files are `v1-<12-lowercase-hex-serial>.pending` and `v1-<12-lowercase-hex-serial>.pairing`. Publication of ready state requires the existing pending file to match the supplied pending identity; it creates ready with no-replace semantics and retains pending as recovery evidence.

- [ ] **Step 1: Build an injectable filesystem fixture and failing tests**

Test exact modes and ownership assumptions plus failures at `mkdirat`, temporary `openat`, each write, file `fsync`, final `linkat`/`renameat2`, directory `fsync`, and cleanup. Test symlink root, symlink leaf, directory replacement, `EEXIST` races, truncated files, regular-file checks, wrong device, invalid serial, read-only directory, and `ENOSPC`.

- [ ] **Step 2: Confirm failures before implementation**

```bash
meson test -C .driver-worktrees/libfprint/build-verimark-tests test-persist-store --print-errorlogs
```

Expected: FAIL because the store API is missing.

- [ ] **Step 3: Implement pinned traversal and no-replace publication**

Open `/var/lib/fprint` then `verimark` one component at a time using `openat()` with `O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC`. Create with `mkdirat(fprint_dirfd, "verimark", 0700)`, verify `fstat()` reports a directory owned by effective uid, and never reconstruct an absolute child path after obtaining the directory fd. Create temporary regular files with `O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC`, mode `0600`; write completely; `fsync()` the file; publish without replacement; then `fsync()` the directory.

- [ ] **Step 4: Enforce failure invariants**

On failure before publication, unlink only the exact temporary name created by this process. Never unlink pending or ready files. If ready publication succeeds but directory `fsync` fails, return an ambiguity error and leave both records. If either canonical filename already exists, load and compare it; accept byte-identical idempotence and reject every mismatch.

- [ ] **Step 5: Run filesystem tests as an unprivileged user**

```bash
meson test -C .driver-worktrees/libfprint/build-verimark-tests test-persist-store --print-errorlogs
meson test -C .driver-worktrees/libfprint/build-verimark-asan test-persist-store --print-errorlogs
```

Expected: all cases PASS in a test-owned temporary root; no test writes `/var/lib/fprint`.

- [ ] **Step 6: Export and commit**

```bash
git -C .driver-worktrees/libfprint add libfprint/drivers/verimark
git -C .driver-worktrees/libfprint commit -m "feat: persist VeriMark identity without replacement"
tools/export-libfprint-patches 66591aae03856bcefa7d7b4c0f08ea630f64b623 verimark-factory-beta-driver
git add patches/libfprint
git commit -m "feat: add hardened pairing-store patch"
```

### Task 6: Replace Synchronous Bootstrap with an Asynchronous Provisioning SSM

**Files:**
- Create in driver: `libfprint/drivers/verimark/provision.h`
- Create in driver: `libfprint/drivers/verimark/provision.c`
- Modify in driver: `libfprint/drivers/verimark/bootstrap.h`
- Modify in driver: `libfprint/drivers/verimark/bootstrap.c`
- Create in driver: `libfprint/drivers/verimark/tests/test-bootstrap.c`
- Create in driver: `libfprint/drivers/verimark/tests/test-provision.c`
- Modify in driver: `libfprint/drivers/verimark/meson.build`
- Regenerate: `patches/libfprint/series`

**Interfaces:**
- Consumes: Task 4 identity types and Task 5 store.
- Produces:

```c
typedef enum {
  VERIMARK_PAIR_SUCCESS,
  VERIMARK_PAIR_ALREADY_PAIRED,
  VERIMARK_PAIR_PROTOCOL_ERROR,
  VERIMARK_PAIR_TRANSPORT_AMBIGUOUS,
} VerimarkPairResult;

typedef struct {
  void (*submit_pair) (FpDevice *device,
                       GBytes *request,
                       GCancellable *cancellable,
                       GAsyncReadyCallback callback,
                       gpointer user_data);
  GBytes *(*submit_pair_finish) (FpDevice *device,
                                 GAsyncResult *result,
                                 GError **error);
} VerimarkPairTransport;

void verimark_provision_start (FpDevice *device,
                               VerimarkPersistStore *store,
                               const guint8 serial[6],
                               const VerimarkPairTransport *transport,
                               GCancellable *cancellable,
                               GAsyncReadyCallback callback,
                               gpointer user_data);
gboolean verimark_provision_finish (FpDevice *device,
                                    GAsyncResult *result,
                                    VerimarkPairingData *out,
                                    GError **error);
```

- [ ] **Step 1: Write synthetic response-parser tests**

Use fixed non-secret test keys and responses to cover complete success, short header, short certificate, trailing bytes, invalid certificate, status `0x0406`, every other nonzero status, duplicated callback, callback after cancellation, timeout, and disconnect.

- [ ] **Step 2: Write state-machine tests with a fake transport and store**

Assert the exact event order for fresh success:

```text
load(missing) -> generate(identity A) -> publish_pending(A) ->
submit_pair(A) -> parse_success -> publish_ready(A,response) -> complete_once
```

Assert pending recovery always submits identity A; a failure never generates identity B; ready state makes zero pair submissions; corrupt, mismatched, and already-paired states terminate once.

- [ ] **Step 3: Confirm the new tests fail**

```bash
meson test -C .driver-worktrees/libfprint/build-verimark-tests test-bootstrap test-provision --print-errorlogs
```

Expected: FAIL because the async provisioning API is absent and bootstrap still performs synchronous I/O.

- [ ] **Step 4: Make bootstrap pure and bounded**

Retain only request construction and complete response validation in `bootstrap.c`. Require exact packet sizes and status mappings. Remove direct USB submission and every environment-variable or marker-file decision from that module.

- [ ] **Step 5: Implement the `FpiSsm` coordinator**

Use explicit states `LOAD`, `GENERATE`, `PUBLISH_PENDING`, `SEND_PAIR`, `PARSE_RESPONSE`, `PUBLISH_READY`, and `COMPLETE`. Attach a single completion guard; set a finite transport timeout using existing driver constants; propagate cancellation at every state. After pair submission begins, cancellation or disconnect returns `VERIMARK_PAIR_TRANSPORT_AMBIGUOUS` and preserves pending state.

- [ ] **Step 6: Verify every terminal path and sanitizer run**

```bash
meson test -C .driver-worktrees/libfprint/build-verimark-tests test-bootstrap test-provision --print-errorlogs
meson test -C .driver-worktrees/libfprint/build-verimark-asan test-bootstrap test-provision --print-errorlogs
```

Expected: all protocol/state tests PASS; fake logs show at most one pair submission and one completion per operation.

- [ ] **Step 7: Export and commit**

```bash
git -C .driver-worktrees/libfprint add libfprint/drivers/verimark
git -C .driver-worktrees/libfprint commit -m "feat: provision VeriMark with asynchronous state machine"
tools/export-libfprint-patches 66591aae03856bcefa7d7b4c0f08ea630f64b623 verimark-factory-beta-driver
git add patches/libfprint
git commit -m "feat: add asynchronous provisioning patch"
```

### Task 7: Prove Same-Identity Recovery Before Enabling Factory Pairing

**Files:**
- Create in driver: `libfprint/drivers/verimark/tools/verimark-pair-lab.c`
- Create in driver: `libfprint/drivers/verimark/tests/test-pair-recovery.c`
- Modify in driver: `libfprint/drivers/verimark/meson.build`
- Create: `docs/hardware/pairing-recoverability-protocol.md`
- Create: `tests/test_hardware_reports.py`
- Regenerate: `patches/libfprint/series`

**Interfaces:**
- Consumes: exact pending identity, pair request/response parser, fake transport, and persistence store from Tasks 4–6.
- Produces: an uninstalled `verimark-pair-lab` binary with `inspect`, `render-request`, and `simulate-recovery` modes; a redacted signed-off protocol report; the pre-integration half of G1.

- [ ] **Step 1: Add policy tests for the lab harness**

Assert Meson marks the binary `install: false`; only `inspect` may open a real USB device and it sends no mutating opcode; `render-request` consumes a synthetic identity file in a test-owned directory; `simulate-recovery` uses the fake transport; and no real pair, reset, erase, credential dump, or second-identity command is linked.

- [ ] **Step 2: Add deterministic recovery simulations**

For every boundary in `publish_pending`, pair submission, response arrival, and `publish_ready`, restart the fake operation from on-disk state. Require zero identities before pending publication, exactly identity A after it, and no code path that produces identity B. Record the exact transition matrix in `docs/hardware/pairing-recoverability-protocol.md`.

- [ ] **Step 3: Run all simulated recovery tests before connecting fresh hardware**

```bash
meson test -C .driver-worktrees/libfprint/build-verimark-tests test-pair-recovery --print-errorlogs
python -m unittest -v tests.test_hardware_reports
```

Expected: PASS; the matrix has an explicit action and safe terminal state for every boundary.

- [ ] **Step 4: Perform read-only protocol inspection on the factory-fresh unit**

After the ordered unit arrives and the user explicitly authorizes access to that exact USB device, stop fprintd, run only `verimark-pair-lab inspect`, and save redacted descriptor, firmware, and SHA-256(serial) metadata under ignored `hardware-local/`. Confirm the reader reports the expected factory-fresh state without sending the pair opcode.

- [ ] **Step 5: Establish the pre-integration recovery argument without pairing hardware**

Trace the existing protocol implementation and published protocol evidence to
identify the exact operation that recovers final server material or safely
resubmits identity A. Encode its observed status/response requirements in the
fake transport tests. Do not infer safety from a status number alone: require
certificate equality and an explicit assertion that the sensor pairing slot is
not rewritten.

Expected safe result: the implementation has a bounded recovery transition
using only identity A and test vectors exercise it. If no such transition can
be specified, G1 fails and Task 8 does not begin.

- [ ] **Step 6: Enforce the pre-integration stop/go decision**

If the recovery argument is complete, write its response fields, identity-hash
comparison, and remaining hardware assumption into the redacted report. If it
fails or remains ambiguous, retain explicit experimental opt-in and document
the blocker without advertising factory-fresh support. The remaining hardware
assumption is checked during Task 14's one normal enrollment, not by this lab.

- [ ] **Step 7: Export and commit only the testable harness and redacted evidence**

```bash
git -C .driver-worktrees/libfprint add libfprint/drivers/verimark
git -C .driver-worktrees/libfprint commit -m "test: characterize VeriMark pairing recovery"
tools/export-libfprint-patches 66591aae03856bcefa7d7b4c0f08ea630f64b623 verimark-factory-beta-driver
git add patches/libfprint docs/hardware/pairing-recoverability-protocol.md tests/test_hardware_reports.py
git commit -m "test: record VeriMark pairing recoverability gate"
```

### Task 8: Start Provisioning Only From Enrollment

**Files:**
- Modify in driver: `libfprint/drivers/verimark/verimark.h`
- Modify in driver: `libfprint/drivers/verimark/verimark.c`
- Create in driver: `libfprint/drivers/verimark/tests/test-enroll-provision.c`
- Modify in driver: `libfprint/drivers/verimark/meson.build`
- Regenerate: `patches/libfprint/series`

**Interfaces:**
- Consumes: `verimark_provision_start()` and `verimark_provision_finish()` after the pre-integration half of G1 passes.
- Produces: non-mutating open state `READY`, `FACTORY_FRESH`, `PENDING_RECOVERY`, or `UNSUPPORTED_PAIRED`; enroll vfunc that provisions when eligible and resumes the original enroll exactly once; Meson option `verimark_factory_pairing` with choices `disabled`, `experimental`, and `enabled`, default `disabled` until Task 14.

- [ ] **Step 1: Write lifecycle tests around the public driver vfuncs**

Test discovery, probe, open, close, verify, list, and delete with no local record and assert zero pair submissions. Test first enroll from `FACTORY_FRESH` and `PENDING_RECOVERY`; test ready enrollment; test already-paired refusal; test cancellation before and after USB submission; test daemon close during provisioning.

- [ ] **Step 2: Confirm the inherited open-time bootstrap behavior fails policy**

```bash
meson test -C .driver-worktrees/libfprint/build-verimark-tests test-enroll-provision --print-errorlogs
```

Expected: FAIL because existing `verimark_try_bootstrap()` runs from open and uses environment/marker opt-in.

- [ ] **Step 3: Remove every open-time mutation trigger**

Delete the environment-variable and marker-file bootstrap path from `open()`. Open may read device identity and persistence state only. It must establish TLS immediately only for a valid ready or compatible legacy credential; otherwise it leaves the USB session clear and records the non-secret state.

- [ ] **Step 4: Chain provisioning into the enroll vfunc**

On authorized enrollment, call provisioning only for `FACTORY_FRESH` or recoverable `PENDING_RECOVERY` when the build option is `experimental`. On success, establish TLS using the returned pairing data, then start the existing enrollment SSM with the original finger request. Map unsupported-paired and ambiguous states to a stable fprintd-visible error message that instructs the user to run `verimarkctl doctor` and never suggests reset.

- [ ] **Step 5: Run the full driver suite under normal and sanitizer builds**

```bash
meson test -C .driver-worktrees/libfprint/build --print-errorlogs
meson test -C .driver-worktrees/libfprint/build-verimark-tests --print-errorlogs
meson test -C .driver-worktrees/libfprint/build-verimark-asan --print-errorlogs
```

Expected: all upstream and VeriMark tests PASS; lifecycle traces contain no pair operation before enroll.

- [ ] **Step 6: Export and commit**

```bash
git -C .driver-worktrees/libfprint add libfprint/drivers/verimark
git -C .driver-worktrees/libfprint commit -m "feat: provision VeriMark on first enrollment"
tools/export-libfprint-patches 66591aae03856bcefa7d7b4c0f08ea630f64b623 verimark-factory-beta-driver
git add patches/libfprint
git commit -m "feat: enable enroll-time factory provisioning"
```

### Task 9: Preserve Existing Windows-Compatible Credential Loading

**Files:**
- Modify in driver: `libfprint/drivers/verimark/persist-store.h`
- Modify in driver: `libfprint/drivers/verimark/persist-store.c`
- Modify in driver: `libfprint/drivers/verimark/verimark.c`
- Create in driver: `libfprint/drivers/verimark/tests/test-legacy-credential.c`
- Modify: `tests/test_release_lineage.py`
- Regenerate: `patches/libfprint/series`

**Interfaces:**
- Consumes: validated legacy `sub1` data and versioned store.
- Produces: read-only compatibility lookup for `/var/lib/fprintd/verimark/sub1.bin`; no writer, importer, exporter, or public acquisition instructions.

- [ ] **Step 1: Write legacy-compatibility and release-boundary tests**

Use only synthetic 1284-byte fixtures. Assert a valid legacy credential loads through the storage abstraction, establishes TLS, and causes zero provisioning submissions. Assert invalid size/content, symlink, non-regular file, group/world-readable mode, or wrong device rejects safely. Assert project sources contain no Windows registry, DPAPI, collector, importer, exporter, or install command.

- [ ] **Step 2: Confirm the compatibility tests fail before the adapter exists**

```bash
meson test -C .driver-worktrees/libfprint/build-verimark-tests test-legacy-credential --print-errorlogs
python -m unittest -v tests.test_release_lineage
```

Expected: the C test FAILS because only versioned state is consulted; lineage tests PASS.

- [ ] **Step 3: Add a strict read-only legacy adapter**

Open each path component with `O_NOFOLLOW`, require a root-owned regular file of exact size and mode no broader than `0600`, parse it through the existing credential validator, and return it as ready pairing data. Never copy, rename, delete, rewrite, or log the file. Prefer the per-device versioned record whenever both exist; reject conflicting valid identities rather than guessing.

- [ ] **Step 4: Verify regression behavior**

```bash
meson test -C .driver-worktrees/libfprint/build-verimark-tests test-legacy-credential test-enroll-provision --print-errorlogs
python -m unittest -v tests.test_release_lineage
```

Expected: PASS; fake transport submission count remains zero for every valid legacy-credential test.

- [ ] **Step 5: Export and commit**

```bash
git -C .driver-worktrees/libfprint add libfprint/drivers/verimark
git -C .driver-worktrees/libfprint commit -m "fix: preserve read-only legacy pairing credentials"
tools/export-libfprint-patches 66591aae03856bcefa7d7b4c0f08ea630f64b623 verimark-factory-beta-driver
git add patches/libfprint tests/test_release_lineage.py
git commit -m "fix: retain safe paired-reader compatibility"
```

### Task 10: Replace the Credential CLI With Read-Only `verimarkctl`

**Files:**
- Rename: `tools/verimark-credential` to `tools/verimarkctl`
- Modify: `verimark_support/credential.py`
- Create: `verimark_support/probe.py`
- Create: `verimark_support/report.py`
- Modify: `verimark_support/cli.py`
- Modify: `verimark_support/__init__.py`
- Modify: `tests/test_cli.py`
- Create: `tests/test_probe.py`
- Create: `tests/test_report.py`

**Interfaces:**
- Consumes: read-only sysfs, package database, fprintd D-Bus command output, and persistence metadata; never raw USB.
- Produces:

```python
@dataclass(frozen=True)
class DeviceObservation:
    usb_id: str | None
    serial_hash: str | None
    driver: str | None

@dataclass(frozen=True)
class StatusReport:
    schema_version: int
    device: DeviceObservation
    package_version: str | None
    fprintd_available: bool
    persistence_state: str
    enrolled_print_visible: bool | None
    checks: Sequence[Mapping[str, str]]
```

The module exports the exact callable signatures `collect_status(probe:
SystemProbe) -> StatusReport`, `render_report(report: StatusReport) -> str`,
`redact_serial(serial: str) -> str`, and `main(argv: list[str] | None = None) ->
int`.

- [ ] **Step 1: Replace old CLI tests with the allowed command surface**

Assert `status`, `doctor`, and `report` exist; `pair`, `reset`, `delete`, `import`, `export`, `install`, and `windows` are rejected. Assert every probe is injectable and read-only, the CLI refuses to run as a USB claimant, and `report` uses `O_CREAT|O_EXCL` with mode `0600`.

- [ ] **Step 2: Add adversarial redaction tests**

Feed raw serials, 32-byte private-key markers, 400-byte certificate bodies, 1284-byte credentials, ANSI escapes, newlines, control characters, home paths, registry paths, and multiline journal text. Require schema version 1, SHA-256 serial hashes truncated to 16 lowercase hex characters, bounded field lengths, escaped JSON, and absence of every supplied secret token.

- [ ] **Step 3: Run the CLI tests and confirm the old tool fails the contract**

```bash
python -m unittest -v tests.test_cli tests.test_probe tests.test_report
```

Expected: FAIL because the new commands and report model do not exist.

- [ ] **Step 4: Implement the minimum read-only probes**

Use `pathlib` reads under `/sys/bus/usb/devices`, `pacman -Q`, `busctl --system`, and `fprintd-list` with the account name from `pwd.getpwuid(os.getuid()).pw_name`; use fixed argument arrays, timeouts, output-size caps, and `LC_ALL=C`. An unprivileged process reports persistence as `protected` when fprintd's `0700` state directory denies access. A root invocation may read only filename, mode, size, magic, version, kind, serial match, and digest validity; it never includes body bytes in the model.

- [ ] **Step 5: Implement deterministic CLI output**

`status` prints concise human output or `--json`; `doctor` returns 0 only when supported device, expected driver ABI, fprintd, permissions, and non-corrupt persistence checks pass; `report FILE` writes canonical sorted JSON to a new mode-0600 file and refuses stdout so terminal history cannot capture unreviewed diagnostics.

- [ ] **Step 6: Verify command surface and redaction**

```bash
python -m unittest -v tests.test_cli tests.test_probe tests.test_report tests.test_credential
tools/verimarkctl --help
tools/verimarkctl pair
```

Expected: tests PASS; help lists only three subcommands; forbidden command exits 2 without touching state.

- [ ] **Step 7: Commit the diagnostic CLI**

```bash
git add tools/verimarkctl verimark_support tests/test_cli.py tests/test_probe.py tests/test_report.py
git add -u tools/verimark-credential
git commit -m "feat: add read-only VeriMark diagnostics"
```

### Task 11: Package the Driver and Diagnostic Tool Without Side Effects

**Files:**
- Modify: `packaging/arch/PKGBUILD`
- Modify: `packaging/arch/.SRCINFO`
- Create: `packaging/arch/verimarkctl.1`
- Modify: `tests/test_arch_package.py`
- Create: `tests/test_package_hooks.py`
- Create: `docs/release/install.md`
- Create: `docs/release/rollback.md`

**Interfaces:**
- Consumes: ordered patch series and Python `verimarkctl` package.
- Produces: `libfprint-verimark` package that owns driver files, generated hwdb/udev data, CLI, Python modules, manual page, and documentation; it owns no PAM configuration or runtime pairing state.

- [ ] **Step 1: Write failing package-content and lifecycle tests**

Assert `provides=('libfprint' 'libfprint-2.so')`, `conflicts=('libfprint')`, exact source commit, checksums for every input, installed executable/man page/modules, and absence of `/etc/pam.d`, `/var/lib/fprint/verimark`, credentials, install scripts, post-transaction hooks, Windows files, or network calls in `prepare/build/check/package`.

- [ ] **Step 2: Add install/upgrade/remove simulation tests**

Extract the package into temporary roots and assert no device state is created. Compare package file manifests across clean install and upgrade. Verify rollback instructions use `pacman -S libfprint` and preserve `/var/lib/fprint/verimark` unless the user explicitly archives it.

- [ ] **Step 3: Run package tests and observe missing CLI/docs**

```bash
python -m unittest -v tests.test_arch_package tests.test_package_hooks
```

Expected: FAIL because `verimarkctl`, its man page, and release docs are not packaged.

- [ ] **Step 4: Update PKGBUILD and manual page**

Install `tools/verimarkctl` as `/usr/bin/verimarkctl`, Python modules into the interpreter's `site-packages/verimark_support`, the man page as `/usr/share/man/man1/verimarkctl.1`, and release docs under `/usr/share/doc/libfprint-verimark/`. Keep package functions non-mutating and reproducible.

- [ ] **Step 5: Regenerate metadata and build twice**

```bash
cd packaging/arch
makepkg --force --cleanbuild --clean --noconfirm
b2sum libfprint-verimark-*.pkg.tar.zst
makepkg --force --cleanbuild --clean --noconfirm
b2sum libfprint-verimark-*.pkg.tar.zst
makepkg --printsrcinfo > .SRCINFO
```

Expected: both builds and checks PASS; package payloads are reproducible after normalizing the Arch build timestamp, and `.SRCINFO` matches the tracked file.

- [ ] **Step 6: Inspect the actual package**

```bash
bsdtar -tf libfprint-verimark-*.pkg.tar.zst
namcap PKGBUILD libfprint-verimark-*.pkg.tar.zst
python -m unittest -v tests.test_arch_package tests.test_package_hooks
```

Expected: only intended files; no secret/state/PAM paths; no fatal `namcap` finding; tests PASS.

- [ ] **Step 7: Commit packaging**

```bash
git add packaging/arch tests/test_arch_package.py tests/test_package_hooks.py docs/release
git commit -m "build: package factory-ready VeriMark beta"
```

### Task 12: Add Fuzzing, Sanitizers, Static Checks, and Public CI

**Files:**
- Create in driver: `libfprint/drivers/verimark/tests/fuzz-persist-format.c`
- Create in driver: `libfprint/drivers/verimark/tests/fuzz-pair-response.c`
- Modify in driver: `libfprint/drivers/verimark/meson.build`
- Create: `tools/check-release-tree`
- Create: `tests/test_release_scanner.py`
- Create: `.github/workflows/ci.yml`
- Regenerate: `patches/libfprint/series`

**Interfaces:**
- Consumes: pure parsers, patch application, project tests, and Arch packaging.
- Produces: libFuzzer-compatible entry points, deterministic secret scanner, and CI jobs named `python`, `libfprint`, `sanitizers`, and `package-source`.

- [ ] **Step 1: Add failing scanner and CI-policy tests**

Create synthetic repositories/archives containing each forbidden class and assert detection: `BEGIN PRIVATE KEY`, `sub1` blob signature, 32-byte key fixture marker, `.pcap`, `.reg`, `DPAPI`, raw USB serial, `/home/`, `hardware-local`, and ignored task reports. Assert the scanner has an explicit allowlist for synthetic test tokens and scans reachable Git objects plus a generated archive.

- [ ] **Step 2: Implement the deterministic scanner**

`tools/check-release-tree REF ARCHIVE` validates exactly two existing arguments, enumerates `git rev-list --objects REF`, streams object contents without checkout, inspects every archive member with size caps, rejects symlinks escaping the archive root, and reports only object/path and rule name—not matching secret content.

- [ ] **Step 3: Add fuzz targets for the two untrusted parsers**

Each target calls one parser with arbitrary bytes, clears all outputs, and treats any crash, leak, out-of-bounds access, or unbounded allocation as failure. Seed corpora contain only synthetic valid/invalid records from unit tests.

- [ ] **Step 4: Add CI with immutable container/package inputs**

The workflow must:

```text
python: python -m unittest discover -s tests -v
libfprint: apply series, configure -Dwerror=true, run all Meson tests
sanitizers: configure address+undefined, run all VeriMark tests
package-source: run makepkg --verifysource and project/archive scanner
```

Pin GitHub actions to full commit SHAs and grant `contents: read` only.

- [ ] **Step 5: Run local security gates**

```bash
python -m unittest -v tests.test_release_scanner
meson test -C .driver-worktrees/libfprint/build-verimark-asan --print-errorlogs
meson test -C .driver-worktrees/libfprint/build-verimark-tests --wrapper='valgrind --error-exitcode=99 --leak-check=full' test-persist-format test-provision --print-errorlogs
meson setup --wipe .driver-worktrees/libfprint/build-scan .driver-worktrees/libfprint -Ddrivers=all -Dinstalled-tests=false -Dwerror=true
scan-build --status-bugs meson compile -C .driver-worktrees/libfprint/build-scan
```

Expected: tests PASS; Valgrind exits 0; static analysis reports no release-blocking defect.

- [ ] **Step 6: Export and commit**

```bash
git -C .driver-worktrees/libfprint add libfprint/drivers/verimark
git -C .driver-worktrees/libfprint commit -m "test: fuzz VeriMark persistence and pairing parsers"
tools/export-libfprint-patches 66591aae03856bcefa7d7b4c0f08ea630f64b623 verimark-factory-beta-driver
git add patches/libfprint tools/check-release-tree tests/test_release_scanner.py .github/workflows/ci.yml
git commit -m "ci: enforce VeriMark release security gates"
```

### Task 13: Run the Existing Paired-Reader Regression Gate

**Files:**
- Create: `docs/hardware/existing-paired-reference.md`
- Modify: `tests/test_hardware_reports.py`

**Interfaces:**
- Consumes: built package, protected existing credential, fprintd, and current `047d:00f2` reader.
- Produces: redacted G2 evidence with package version, firmware, serial hash, operation counts, and restart/reconnect/reboot results.

- [ ] **Step 1: Add report-schema tests before hardware work**

Require fields `schema_version: 1`, `device: 047d:00f2`, `pair_submissions: 0`, `list`, `verify`, `fprintd_restart`, `usb_reconnect`, `system_reboot`, `windows_regression`, and SHA-256 hashes of credential before/after. Reject raw serials, credentials, template IDs, usernames, and unrestricted logs.

- [ ] **Step 2: Install the candidate package with explicit user approval**

```bash
sudo pacman -U packaging/arch/libfprint-verimark-*.pkg.tar.zst
sudo systemctl restart fprintd.service
```

Expected: stock fprintd starts and claims the Desktop reader; no pairing operation occurs.

- [ ] **Step 3: Exercise only safe reference-reader operations**

List the user's prints and verify the designated existing enrollment. Restart fprintd, verify again, reconnect USB, verify again, reboot, and verify again. Enroll/delete only a clearly designated Linux test finger if a fresh enrollment regression is needed. Do not remove the credential or unknown templates.

- [ ] **Step 4: Confirm Windows compatibility**

Boot Windows and confirm its original enrollment still authenticates. Record only pass/fail, device firmware, and redacted hashes; do not extract any Windows data.

- [ ] **Step 5: Validate and commit the redacted report**

```bash
python -m unittest -v tests.test_hardware_reports
tools/check-release-tree HEAD /tmp/verimark-project-test.tar
git add docs/hardware/existing-paired-reference.md tests/test_hardware_reports.py
git commit -m "test: record paired-reader regression evidence"
```

Expected: G2 passes, `pair_submissions` is exactly 0, and credential hashes are byte-stable.

### Task 14: Run Factory-Fresh Acceptance Through fprintd

**Files:**
- Modify in driver: `meson_options.txt`
- Regenerate: `patches/libfprint/series`
- Modify: `packaging/arch/PKGBUILD`
- Regenerate: `packaging/arch/.SRCINFO`
- Create: `docs/hardware/factory-fresh-acceptance.md`
- Modify: `tests/test_hardware_reports.py`
- Create: `docs/release/beta-known-limitations.md`

**Interfaces:**
- Consumes: a new factory-fresh `047d:00f2` unit, candidate package, normal fprintd/Omarchy enrollment, the passed pre-integration half of G1, and passed G2.
- Produces: redacted G3 evidence and an exact known-limitations document.

- [ ] **Step 1: Extend the report schema for the acceptance matrix**

Require preflight state `factory-fresh`, `pair_submissions: 1`, enrollment result, 20 numbered positive verifications, wrong-finger and poor-scan results, list, targeted delete, re-enroll, restart, reconnect, reboot, file owner/mode, and before/after SHA-256 of the finalized credential.

- [ ] **Step 2: Capture non-mutating preflight data**

Run `verimarkctl status --json` and the lab `inspect` mode. Confirm exact USB ID, supported firmware state, no local pending/ready record, and factory-fresh sensor status. Store the full local report only under ignored `hardware-local/`; commit only its redacted schema-approved form.

- [ ] **Step 3: Perform the single real first enrollment**

Build this hardware candidate with `-Dverimark_factory_pairing=experimental`, then start enrollment through `fprintd-enroll -f right-index-finger` or the Omarchy fingerprint enrollment UI as the logged-in user. Confirm pairing is triggered once inside libfprint and the same enroll request continues to completion. Do not stop fprintd, unplug USB, kill the process, suspend, or reboot during the first pair.

- [ ] **Step 4: Run the acceptance matrix**

Perform 20 successful verifications, representative wrong-finger and poor-scan attempts, list prints, delete only the designated test print, re-enroll it, restart fprintd, reconnect USB, reboot, and verify after each lifecycle transition.

- [ ] **Step 5: Verify persistence stability and permissions**

Check `/var/lib/fprint/verimark` is root-owned `0700`, canonical files are root-owned regular `0600` files, no symlinks exist, the ready credential hash remains stable, and no second pair request occurs.

Confirm the real response satisfies the recovery fields and identity equality
assumed in Task 7. If it does, change the Meson option default to `enabled`,
run `updpkgsums` and `makepkg --printsrcinfo` in `packaging/arch`, rerun the
complete driver/package suites, and record G1 as passed. If it does not, leave
the default disabled and stop before release-candidate work.

- [ ] **Step 6: Validate and commit redacted evidence**

```bash
git -C .driver-worktrees/libfprint add meson_options.txt
git -C .driver-worktrees/libfprint commit -m "feat: enable verified VeriMark factory pairing"
tools/export-libfprint-patches 66591aae03856bcefa7d7b4c0f08ea630f64b623 verimark-factory-beta-driver
python -m unittest -v tests.test_hardware_reports
git add patches/libfprint packaging/arch docs/hardware/factory-fresh-acceptance.md docs/release/beta-known-limitations.md tests/test_hardware_reports.py
git commit -m "test: record factory-fresh VeriMark acceptance"
```

Expected: G3 passes with exactly one pairing submission and 20/20 positive verifications.

### Task 15: Produce and Independently Review a Reproducible Release Candidate

**Files:**
- Create: `README.md`
- Create: `LICENSES/LGPL-2.1-or-later.txt`
- Create: `LICENSES/MIT.txt`
- Create: `SECURITY.md`
- Create: `CONTRIBUTING.md`
- Create: `.github/ISSUE_TEMPLATE/verimark-report.yml`
- Create: `docs/release/v0.1.0-beta.1.md`
- Create: `docs/release/checklist.md`
- Modify: `packaging/arch/PKGBUILD`
- Modify: `packaging/arch/.SRCINFO`
- Modify: `tests/test_release_lineage.py`

**Interfaces:**
- Consumes: passed G1–G3, exact driver base, patch series, package, reports, and security scanner.
- Produces: reviewed tag candidate commit, source archive, `BLAKE2bSUMS`, package, rollback evidence, and G4 result; no remote changes.

- [ ] **Step 1: Add public-metadata policy tests**

Require README scope and install/rollback links, SPDX license mapping, private security-report instructions, contribution test commands, privacy-safe issue fields, beta limitations, supported USB ID, unsupported already-paired state, no Windows acquisition instructions, and no claim of upstream support.

- [ ] **Step 2: Write the public documents and issue template**

State plainly that this is an experimental Arch beta, hardware pairing is persistent, `047d:8054` is unsupported, already-paired readers need an existing compatible credential, and rollback restores stock libfprint without resetting hardware. The issue form requests only `verimarkctl report` attachment and explicitly forbids raw credentials, registry exports, packet captures, serials, and biometric data.

- [ ] **Step 3: Run all source and driver verification**

```bash
python -m unittest discover -s tests -v
meson test -C .driver-worktrees/libfprint/build --print-errorlogs
meson test -C .driver-worktrees/libfprint/build-verimark-tests --print-errorlogs
meson test -C .driver-worktrees/libfprint/build-verimark-asan --print-errorlogs
git diff --check
```

Expected: every test PASS and no whitespace error.

- [ ] **Step 4: Build in a clean Arch chroot**

```bash
cd packaging/arch
extra-x86_64-build
```

Expected: clean source verification, build, complete upstream/libfprint/VeriMark test suites, packaging, and ABI checks all succeed without access to local ignored files.

- [ ] **Step 5: Exercise install, upgrade, and rollback on a clean test host**

Install the candidate, upgrade from the previous candidate, run `verimarkctl doctor`, replace it with stock `libfprint`, restart fprintd, and confirm package ownership and ABI state after each operation. Verify no PAM file or runtime identity changes as a package side effect.

- [ ] **Step 6: Generate the local release artifacts from the candidate commit**

```bash
git archive --format=tar --prefix=verimark-linux-0.1.0-beta.1/ HEAD | zstd -19 -T0 -o /tmp/verimark-linux-0.1.0-beta.1.tar.zst
b2sum /tmp/verimark-linux-0.1.0-beta.1.tar.zst > /tmp/BLAKE2bSUMS
tools/check-release-tree HEAD /tmp/verimark-linux-0.1.0-beta.1.tar.zst
```

Expected: scanner exits 0; archive contains no ignored or machine-local material.

- [ ] **Step 7: Request independent code, security, and package review**

Use `superpowers:requesting-code-review` three times with separate scopes:

```text
1. protocol/state machine/persistence and G1 proof;
2. secret handling/redaction/history/archive scanning;
3. PKGBUILD/ABI/clean-chroot/install/upgrade/rollback.
```

Address every accepted finding with `superpowers:receiving-code-review`, rerun the affected task tests, then rerun Steps 3–6 in full.

- [ ] **Step 8: Commit the release candidate and verify G4**

```bash
git add README.md LICENSES SECURITY.md CONTRIBUTING.md .github/ISSUE_TEMPLATE docs/release packaging/arch tests/test_release_lineage.py
git commit -m "docs: prepare VeriMark beta release candidate"
git status --short
```

Expected: clean worktree, all review findings resolved, and G4 passed from immutable inputs.

### Task 16: Publish GitHub and AUR Only After Explicit Authorization

**Files:**
- Modify after repository URL is known: `packaging/arch/PKGBUILD`
- Regenerate after repository URL is known: `packaging/arch/.SRCINFO`
- Create in separate AUR checkout: `PKGBUILD`
- Create in separate AUR checkout: `.SRCINFO`
- Create in separate AUR checkout: `verimarkctl.1`
- Copy into separate AUR checkout: `patches/libfprint/series`
- Copy into separate AUR checkout: `patches/libfprint/*.patch`

**Interfaces:**
- Consumes: passed G1–G4 and explicit authorization immediately before each remote mutation.
- Produces: public GitHub repository, annotated `v0.1.0-beta.1` tag, release archive/checksums, and AUR `libfprint-verimark` package; then G5 is complete.

- [ ] **Step 1: Pause and request authorization for GitHub publication**

Present the final repository tree, test totals, hardware gate results, independent-review dispositions, release archive checksum, and exact planned repository name `verimark-linux`. Do not invoke `gh repo create`, push, create a release, file an issue, or contact anyone until the user explicitly approves.

- [ ] **Step 2: Create the repository and set the canonical URL after approval**

Resolve the authenticated account rather than guessing it:

```bash
release_account=$(gh api user --jq .login)
gh repo create "${release_account}/verimark-linux" --public --source=. --remote=origin --description "Experimental Linux support for the Kensington VeriMark Desktop fingerprint reader"
```

Update PKGBUILD `url` and release-source URL to `https://github.com/${release_account}/verimark-linux`, regenerate `.SRCINFO`, update checksums from the tagged archive, rerun package/source tests, and commit that exact metadata.

- [ ] **Step 3: Create and verify the annotated beta tag**

```bash
git tag -a v0.1.0-beta.1 -m "VeriMark Desktop factory-fresh beta 1"
git show --no-patch --format=fuller v0.1.0-beta.1
git push origin feature/verimark-factory-beta
git push origin v0.1.0-beta.1
```

Expected: the tag object names the beta release and the remote tag resolves to the fully tested candidate commit.

- [ ] **Step 4: Publish immutable release artifacts**

Regenerate the archive from the tag, rerun `tools/check-release-tree`, verify `b2sum -c`, and use `gh release create v0.1.0-beta.1` with the release notes, archive, and `BLAKE2bSUMS`. Download the published assets into a new temporary directory and verify their checksums and archive scan again.

- [ ] **Step 5: Pause and request separate authorization for AUR publication**

Show the final `PKGBUILD`, `.SRCINFO`, source URLs, hashes, clean-chroot transcript, file manifest, and rollback result. Do not create or push the AUR repository until the user explicitly approves.

- [ ] **Step 6: Build the isolated AUR submission after approval**

Clone the empty `aur@aur.archlinux.org:libfprint-verimark.git` repository into a new sibling worktree, copy only the packaging inputs enumerated in this task, run `makepkg --verifysource`, `makepkg --cleanbuild`, `namcap`, and `extra-x86_64-build`, then compare the artifact manifest and ABI with the reviewed candidate.

- [ ] **Step 7: Commit and push the AUR package**

```bash
git add PKGBUILD .SRCINFO verimarkctl.1 series *.patch
git commit -m "Initial import: libfprint-verimark 0.1.0_beta1-1"
git push origin master
```

Expected: AUR contains only immutable release inputs; the package page builds the same artifact; G5 completes.

- [ ] **Step 8: Verify the public installation path without changing user authentication**

On a clean Arch test environment, install from the AUR, connect a supported test unit, enroll through ordinary fprintd, verify, run `verimarkctl doctor`, and roll back to stock libfprint. Do not alter PAM, sudo, login, lock-screen, or FIDO configuration as part of release verification.

### Task 17: Turn Beta Evidence Into an Upstreamable Desktop Driver

**Files:**
- Create: `docs/upstream/persistent-data-proposal.md`
- Create: `docs/upstream/verimark-desktop-protocol.md`
- Create: `docs/upstream/beta-evidence.md`
- Create: `tools/summarize-verimark-reports`
- Create: `tests/test_report_summary.py`
- Create after maintainer feedback: `patches/upstream/series`
- Create after maintainer feedback: `patches/upstream/*.patch`

**Interfaces:**
- Consumes: published beta, privacy-safe issue attachments, existing libfprint persistent-data branch `benzea/persistent-data`, and separate authorization before maintainer contact or GitLab publication.
- Produces: aggregate hardware evidence, a concrete libfprint persistence API proposal, and a minimal Desktop-only upstream patch series based on the maintainer-selected architecture.

- [ ] **Step 1: Write aggregation tests before collecting public reports**

Use synthetic schema-version-1 `verimarkctl` reports. Assert the summarizer
groups only by USB ID, package version, driver version, firmware, persistence
state, and pass/fail check; counts serial hashes without printing them; rejects
unknown schemas and unredacted fields; and never reads arbitrary journal or
binary attachments.

- [ ] **Step 2: Implement privacy-preserving evidence aggregation**

`tools/summarize-verimark-reports INPUT_DIRECTORY OUTPUT_JSON` must accept two
paths, refuse symlinks and files broader than `0600`, parse bounded JSON only,
validate the exact report schema, aggregate counts, and atomically create a new
output file. It emits no individual serial hash or free-form diagnostic value.

- [ ] **Step 3: Verify the aggregator**

```bash
python -m unittest -v tests.test_report_summary tests.test_report
```

Expected: all tests PASS, including adversarial reports containing secrets and
control characters.

- [ ] **Step 4: Collect a minimum independent beta evidence set**

After users voluntarily attach `verimarkctl report` output, aggregate at least
three independently owned `047d:00f2` readers. Record firmware diversity as
observed rather than inferring it. Document pairing count, enrollment success,
verification totals, restart/reconnect/reboot results, and every distinct safe
failure mode in `docs/upstream/beta-evidence.md`.

- [ ] **Step 5: Draft the persistence architecture proposal locally**

Compare driver-managed `/var/lib/fprint/verimark` storage with the historical
`fp_device_get_persistent_data()` and `fp_device_set_persistent_data()` shape.
Specify ownership, versioning, maximum size, async behavior, atomicity,
no-replace semantics, device identity binding, error mapping, migration, and
secret lifetime. Include the exact API surface proposed for libfprint and show
how the beta backend migrates without changing pairing protocol data.

- [ ] **Step 6: Pause and request authorization before maintainer contact**

Present the local proposal, beta evidence, protocol document, and the exact
existing libfprint issue or discussion target. Do not comment, email, open an
issue, create a freedesktop fork, or submit a merge request until the user
explicitly authorizes that external contact.

- [ ] **Step 7: Ask maintainers one narrow architecture question after approval**

Request a decision among reviving the historical persistent-data API, adding
an equivalent internal API, or temporarily accepting driver-managed state.
Link the redacted beta evidence and protocol document; do not attach pairing
credentials, raw captures, serials, or Windows artifacts.

- [ ] **Step 8: Recut the upstream series to the selected architecture**

Create a fresh libfprint worktree from the maintainer-requested base. Rebase
only Desktop `047d:00f2` support, protocol parsers, async provisioning,
persistence integration, and tests. Exclude AUR packaging, `verimarkctl`, the
lab harness, VeriMark IT registration, Windows tooling, and project-specific
release machinery. Export reviewable mail patches with preserved authorship
into `patches/upstream/` and verify clean application plus the full upstream
test suite.

- [ ] **Step 9: Pause and request separate authorization before an upstream merge request**

Show the final patch series, maintainer discussion outcome, CI transcript,
hardware evidence, license audit, and proposed merge-request text. Create the
freedesktop fork or merge request only after explicit approval.

- [ ] **Step 10: Commit the local upstream-preparation artifacts**

```bash
git add docs/upstream tools/summarize-verimark-reports tests/test_report_summary.py patches/upstream
git commit -m "docs: prepare VeriMark Desktop upstream submission"
```

Expected: the local repository contains a reproducible, Desktop-only upstream
series and privacy-safe evidence; external state changes are separately
authorized and recorded.

## Final Completion Criteria

The beta implementation is complete when G1–G5 pass, every automated suite is green, the two hardware reports satisfy their schemas, the package is reproducible from the public tag, and a clean Arch user can enroll a factory-fresh `047d:00f2` through normal fprintd without Windows files or special pairing tooling. Mainstream upstream work is ready when Task 17 also produces independently sourced evidence and a maintainer-aligned Desktop-only series. Any failure of same-identity recovery, already-paired refusal, secret containment, reference-reader compatibility, or rollback reopens the corresponding task and blocks the beta.
