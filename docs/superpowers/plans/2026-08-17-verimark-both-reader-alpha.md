# VeriMark Both-Reader Alpha Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, publish, and package a reproducible `v0.0.1-alpha.1` with cleaned s-celles-derived support for both VeriMark Desktop and VeriMark IT on current pinned libfprint.

**Architecture:** The project stores a reviewed mail-patch series rather than a whole libfprint checkout. A materializer obtains upstream `c4654fdc85c25afdd9115bec2f95a44145ae3b94`, applies the series, and builds the same source locally and in the AUR. Shared Tudor code is separated from Desktop control-transfer and IT bulk/interrupt behavior; each reader reports its own capability tier.

**Tech Stack:** C11, GLib/GObject/GIO, libfprint, Meson, OpenSSL, Python 3 standard library, unittest, Bash, Arch makepkg/devtools, GitHub releases.

## Global Constraints

- Register and maintain both USB IDs: Desktop `047d:00f2` and IT `047d:8054`.
- Desktop is `desktop-alpha`; IT is `it-experimental` until its own hardware transport, enrollment, verification, list, delete, restart, reconnect, and reboot matrix passes.
- A USB match never implies an unsupported capability works; `verimarkctl` reports a per-device tier and concrete unavailable reason.
- The upstream base is exactly `c4654fdc85c25afdd9115bec2f95a44145ae3b94`; no build follows a moving VCS branch.
- Preserve s-celles authorship and license notices in ordered mail patches; resolve rebase conflicts in new cleanup commits.
- No Windows extractor, credential import/export, registry code, raw serial, credential, private key, certificate, template, packet capture, or ignored build data is public.
- Normal and AUR builds pass `-Dverimark_dev_reset=false` and contain no reset command, helper, opcode, or confirmation string.
- Pairing, reset, persistence, and recovery are device-specific. No Desktop protocol is used on IT without verified IT evidence.
- Package lifecycle never pairs, resets, enables PAM, enrolls a finger, or changes FIDO, sudo, login, or lock-screen configuration.
- Publish GitHub and AUR only after the local release gates in this plan pass; the user has authorized those later external actions.

---

### Task 1: Rebase Provenance and Atomic Source Materialization

**Files:**
- Create: `docs/rebase/s-celles-inventory.md`
- Create: `tools/materialize-libfprint`
- Modify: `tools/export-libfprint-patches`
- Modify: `patches/libfprint/series`
- Modify: `tests/test_patch_series.py`
- Modify: `tests/test_arch_package.py`

**Interfaces:**
- Produces `tools/materialize-libfprint OUTPUT_DIRECTORY`, which clones/fetches only upstream commit `c4654fdc85c25afdd9115bec2f95a44145ae3b94`, rejects a nonmatching `HEAD`, validates the series, applies each mail patch, and creates `build` plus `build-verimark-tests`.

- [ ] Write failing tests for: exact base, both IDs in active patches, mail-patch authorship, duplicate/blank/path-traversal series rejection, symlink patch rejection, and materializer refusal of dirty/mismatched sources.
- [ ] Run `python -m unittest -v tests.test_patch_series tests.test_arch_package` and capture the failure against old base `66591aa`.
- [ ] Generate `docs/rebase/s-celles-inventory.md` from the 61 inherited driver commits, classifying each as shared, Desktop, IT, test, or obsolete; record original commit and retained/dropped decision.
- [ ] Rebase retained patches onto `c4654fd`, preserving mail headers. Do not publish a partial driver: a patch either applies and compiles or is explicitly excluded in the inventory.
- [ ] Implement validation before application. Publish the generated series atomically through a `current` symlink replacement (`ln -s` sibling then `mv -T`) so a reader observes either the old valid tree or the new valid tree; retain a previous tree only after successful replacement.
- [ ] Run `tools/materialize-libfprint /tmp/verimark-materialized`, `meson test -C /tmp/verimark-materialized/build --print-errorlogs`, `meson test -C /tmp/verimark-materialized/build-verimark-tests --print-errorlogs`, and the Python suite.
- [ ] Commit: `build: rebase VeriMark series onto current libfprint`.

### Task 2: Separate Shared, Desktop, and IT Driver Layers

**Files:**
- Modify in materialized driver: `libfprint/drivers/verimark/verimark.[ch]`
- Create in materialized driver: `libfprint/drivers/verimark/device-profile.[ch]`
- Modify in materialized driver: `libfprint/drivers/verimark/transport.[ch]`
- Create in materialized driver: `libfprint/drivers/verimark/tests/test-device-profile.c`

**Interfaces:**

```c
typedef enum {
  VERIMARK_PROFILE_DESKTOP,
  VERIMARK_PROFILE_IT,
} VerimarkDeviceProfile;

typedef enum {
  VERIMARK_TIER_DESKTOP_ALPHA,
  VERIMARK_TIER_IT_EXPERIMENTAL,
} VerimarkSupportTier;

const VerimarkDeviceProfile *verimark_device_profile_for_pid (guint16 pid);
```

- [ ] Write tests mapping `0x00f2` only to Desktop/control transport and `0x8054` only to IT/bulk+interrupt transport; unknown PIDs return `NULL`.
- [ ] Run the focused C test and capture the old PID branches as the failure.
- [ ] Move PID branching from shared session, crypto, and persistence code into profile callbacks; maintain distinct endpoint/interface, handshake variant, and capability fields.
- [ ] Register both IDs and ensure generated hwdb/udev data contains both exactly once.
- [ ] Run full upstream and standalone test suites with warnings-as-errors.
- [ ] Commit: `refactor: separate VeriMark device profiles`.

### Task 3: Desktop Alpha Pairing and Existing-Reader Compatibility

**Files:**
- Create in materialized driver: `persist-format.[ch]`, `persist-store.[ch]`, `provision.[ch]`
- Modify in materialized driver: `bootstrap.[ch]`, `verimark.c`
- Create in materialized driver tests: `test-persist-format.c`, `test-persist-store.c`, `test-provision.c`, `test-enroll-provision.c`, `test-legacy-credential.c`

**Interfaces:**
- Produces a Desktop-only asynchronous enroll-time provisioning state machine, per-device state under `/var/lib/fprint/verimark/`, and read-only legacy credential loading. IT returns a tiered unsupported pairing error until it has dedicated evidence.

- [ ] Add RED tests for pending/ready record parsing, symlink/no-replace/fsync faults, cancellation/disconnect, same-identity retry, no open-time pairing, and legacy Windows-compatible credential loading with zero pair submissions.
- [ ] Implement versioned records, dirfd-pinned storage, and FpiSsm provisioning using exact pending identity reuse.
- [ ] Require protocol recovery evidence before enabling Desktop factory pairing by default; retain experimental build option otherwise.
- [ ] Run normal, ASan/UBSan, and full upstream/standalone suites.
- [ ] Commit: `feat: add Desktop alpha native pairing`.

### Task 4: Complete IT Experimental Transport and Capability Tests

**Files:**
- Modify in materialized driver: `transport.[ch]`, `handshake.[ch]`, `capture.[ch]`, `enroll.[ch]`, `storage.[ch]`
- Create in materialized driver tests: `test-it-transport.c`, `test-it-lifecycle.c`
- Create: `docs/hardware/it-capability-matrix.md`

**Interfaces:**
- Produces IT transport operations `open`, `handshake`, `verify`, `enroll`, `list`, and `delete`, each returning explicit `available`, `experimental`, or `unavailable` status.

- [ ] Write fake bulk/interrupt transport tests for endpoint selection, framing, timeout, cancellation, disconnect, late callback, and no control-transfer fallback.
- [ ] Run focused IT tests and capture current partial-path failures.
- [ ] Port IT bulk/interrupt lifecycle code in isolated commits; do not copy Desktop request formats into IT paths.
- [ ] Update matrix entries only from synthetic vectors or redacted real hardware observations; untested operations remain `unavailable`.
- [ ] Run complete C suites and commit: `feat: harden VeriMark IT experimental transport`.

### Task 5: Capability-Aware Read-Only `verimarkctl`

**Files:**
- Modify: `tools/verimarkctl`, `verimark_support/cli.py`, `verimark_support/probe.py`, `verimark_support/report.py`
- Create: `verimark_support/capability.py`
- Modify: `tests/test_cli.py`
- Create: `tests/test_capability.py`, `tests/test_report.py`

**Interfaces:**

```python
class CapabilityTier(Enum):
    DESKTOP_ALPHA = "desktop-alpha"
    IT_EXPERIMENTAL = "it-experimental"
    UNSUPPORTED = "unsupported"

```

The module exports `capability_for_usb_id(usb_id: str) -> CapabilityTier`.

- [ ] Test exact tiers for both IDs, unknown-device refusal, and redacted report output.
- [ ] Implement status/doctor/report with no raw USB access, no state mutation, and a reason per unavailable operation.
- [ ] Test normal help lists exactly `status`, `doctor`, and `report`; developer reset remains absent.
- [ ] Commit: `feat: report VeriMark per-device capabilities`.

### Task 6: Keep Developer Reset Device-Specific and Publicly Absent

**Files:**
- Modify: `docs/superpowers/specs/2026-08-17-verimark-developer-factory-reset-design.md`
- Modify: `tests/test_reset_build_policy.py`, `tests/test_arch_package.py`
- Create in materialized driver: reset code only after device-specific protocol record passes

- [ ] Test normal/AUR builds contain neither reset markers nor helper for both profiles.
- [ ] Require separate verified protocol records for Desktop and IT before compiling either reset implementation.
- [ ] Keep Task 18–22 of the prior plan as the implementation detail for a verified Desktop reset; duplicate their gates for IT rather than sharing reset frames.
- [ ] Commit only build-policy and documentation changes until a protocol record is verified.

### Task 7: Reproducible GitHub-Source AUR Alpha Package

**Files:**
- Modify: `packaging/arch/PKGBUILD`, `packaging/arch/.SRCINFO`
- Modify: `tests/test_arch_package.py`, `tests/test_package_hooks.py`
- Create: `docs/release/v0.0.1-alpha.1.md`, `docs/release/install.md`, `docs/release/rollback.md`

- [ ] Write tests requiring GitHub release source plus pinned upstream source, fixed checksums, both USB IDs in materialized generated data, explicit reset-disabled Meson option, and no package side effects.
- [ ] Implement package build using the same materializer logic; package `verimarkctl`, manual page, driver, and docs only.
- [ ] Build twice with `makepkg --force --cleanbuild --clean --noconfirm`, regenerate `.SRCINFO`, inspect archive/ABI, and run `namcap`.
- [ ] Commit: `build: package both-reader VeriMark alpha`.

### Task 8: CI, Security, and Hardware Evidence

**Files:**
- Create: `.github/workflows/ci.yml`, `tools/check-release-tree`, `tests/test_release_scanner.py`
- Create: `docs/hardware/desktop-alpha-acceptance.md`, `docs/hardware/it-experimental-acceptance.md`

- [ ] Add CI jobs for patch materialization, full tests, sanitizers, package source, and secret/archive scan.
- [ ] Test and run source-history/archive scan, Valgrind, static analysis, and clean chroot package build.
- [ ] Run Desktop acceptance only on the factory-fresh unit after simulated recovery passes; retain the Windows-paired regression fixture untouched.
- [ ] Run IT acceptance only on an IT unit; otherwise publish matrix entries as unavailable, not successful.
- [ ] Commit: `ci: verify both-reader alpha evidence`.

### Task 9: Publish GitHub `v0.0.1-alpha.1` and the AUR Package

**Files:**
- Modify: `packaging/arch/PKGBUILD`, `packaging/arch/.SRCINFO`
- Create: `BLAKE2bSUMS`

- [ ] Re-run all Task 1–8 gates and obtain independent code, security, and packaging review.
- [ ] Create public GitHub repository `verimark-linux`, push the reviewed branch, create annotated tag `v0.0.1-alpha.1`, attach source artifact and `BLAKE2bSUMS`, then download and verify them.
- [ ] Update PKGBUILD to the exact GitHub release artifact URL/checksum, regenerate `.SRCINFO`, and clean-chroot build it again.
- [ ] Create/push `aur@aur.archlinux.org:libfprint-verimark.git` containing only PKGBUILD, .SRCINFO, patches, series, manual page, and required package files.
- [ ] Verify clean Arch installation, Desktop alpha behavior, `verimarkctl doctor`, and rollback without PAM/FIDO changes.
- [ ] Commit local release metadata: `docs: publish VeriMark both-reader alpha`.

## Completion Criteria

`v0.0.1-alpha.1` is complete when the GitHub release and AUR package reproduce the materialized both-reader source from the pinned upstream commit; Desktop is proven alpha-capable; IT is labeled experimental with only hardware-proven capabilities; public artifacts exclude secrets, Windows tooling, and reset capability; and rollback is verified.
