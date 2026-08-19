# VeriMark Both-Reader GitHub and AUR Alpha

Date: 2026-08-17

## Objective

Create a clean public `verimark-linux` project that carries forward and cleans
up Sébastien Celles' VeriMark work for both Kensington readers:

- VeriMark Desktop, USB ID `047d:00f2`; and
- VeriMark IT, USB ID `047d:8054`.

The project rebases that work onto current upstream libfprint commit
`c4654fdc85c25afdd9115bec2f95a44145ae3b94`, builds from a reproducible local
source materialization, publishes a source-only GitHub alpha, and provides an
AUR alpha package whose inputs are immutable GitHub and upstream artifacts.

## Repository and source model

`verimark-linux` is a clean project repository, not a wholesale mirror of the
historical s-celles fork. It contains:

```text
patches/libfprint/       ordered, reviewable mail patches
packaging/arch/          AUR PKGBUILD and metadata
tools/materialize-libfprint
tools/export-libfprint-patches
tests/                   project, patch, package, and policy tests
docs/                    protocol, hardware, support-tier, and release docs
```

The driver checkout is generated locally under ignored `.driver-worktrees/`.
`tools/materialize-libfprint` obtains exact upstream commit
`c4654fdc85c25afdd9115bec2f95a44145ae3b94`, validates it, applies every patch
listed in `patches/libfprint/series` in order, and creates full/standalone
build trees. The generated checkout is never committed.

Every retained s-celles change is imported as an ordered mail patch with its
original authorship and license notices. The rebase separates shared Tudor
protocol/crypto/session code from Desktop control-transfer behavior and IT
bulk/interrupt behavior. Rebase conflicts are resolved in new cleanup commits,
not by rewriting original attribution.

## Device capability policy

Both IDs are registered in the driver and package hardware data. They have
separate, explicit capability states:

| Reader | USB ID | Alpha state | Required evidence before stronger claim |
| --- | --- | --- | --- |
| VeriMark Desktop | `047d:00f2` | `desktop-alpha` | factory-fresh pairing/enrollment, verification, restart, reconnect, reboot, and Windows-paired regression |
| VeriMark IT | `047d:8054` | `it-experimental` | hardware proof for bulk/interrupt transport, enrollment, verification, list, deletion, restart, reconnect, and reboot |

The current IT code is treated as experimental because the inherited source
labels its IT path partial. A matched USB ID alone is never evidence of usable
authentication. `verimarkctl status` and `doctor` report the device tier and
precise unavailable capability instead of a generic supported claim.

Desktop factory-fresh pairing remains a separate safety-gated path. IT does
not inherit Desktop pairing, persistence, recovery, or reset semantics without
device-specific protocol evidence.

## Build and packaging

The first public version is `v0.0.1-alpha.1`. The AUR package is
`libfprint-verimark` with a clearly alpha package version. It provides and
conflicts with Arch `libfprint`, preserves the `libfprint-2.so` ABI required by
stock fprintd, and explicitly records both supported USB IDs in generated
hardware data.

The AUR package downloads:

1. the immutable GitHub source artifact for `v0.0.1-alpha.1`; and
2. the immutable upstream libfprint source at
   `c4654fdc85c25afdd9115bec2f95a44145ae3b94`.

It verifies fixed checksums for both artifacts, applies the project patch
series in order, runs the complete build/test set, and builds from the same
materialized source as local development. It never follows a moving branch.

Package installation, upgrade, and removal do not pair hardware, enable PAM,
enroll fingerprints, reset a reader, create state, or alter FIDO, sudo, login,
or lock-screen configuration.

## Public publication

After local clean-build, test, package, ABI, source-history, and release-archive
gates pass, publish the clean repository and an annotated GitHub tag
`v0.0.1-alpha.1`. The release attaches a source artifact and `BLAKE2bSUMS`.
The AUR package is then generated from that published artifact and exact
upstream source, tested in a clean Arch chroot, and pushed as the alpha package.

The release notes state:

- Desktop is alpha and has the stated hardware evidence;
- IT is experimental and capability-gated;
- no Windows extraction, credential import, export, or collector is shipped;
- Windows-paired readers require an already compatible local credential; and
- rollback restores stock `libfprint` without modifying reader pairing state.

No credential, private key, certificate body, raw serial, fingerprint template,
packet capture, Windows registry data, local path, ignored build tree, or local
hardware report is committed, released, or packaged.

## Developer reset boundary

The developer-only reset design remains separate. Public local builds, GitHub
release artifacts, and AUR packages explicitly pass
`-Dverimark_dev_reset=false` and must contain no reset helper, command, reset
protocol code, reset opcode, or reset confirmation string. Any developer reset
for Desktop or IT requires its own verified protocol evidence and disposable
hardware acceptance; neither device inherits reset behavior from the other.

## Validation gates

Every source candidate passes:

- exact-base patch application and series-order validation;
- upstream libfprint and standalone VeriMark tests;
- warnings-as-errors, AddressSanitizer, UndefinedBehaviorSanitizer, Valgrind,
  and available static analysis;
- tests that each USB ID is registered and that per-device tier output is
  accurate;
- redaction, secret/history/archive, package-content, and package-hook scans;
- clean Arch chroot package build and ABI inspection; and
- install, upgrade, and rollback exercises without authentication-side effects.

Desktop hardware acceptance is required for the alpha release. IT remains
experimental until it receives its own full hardware acceptance matrix. A
failure or ambiguity in either device path downgrades only that device's tier;
it never causes cross-device pairing, reset, or credential mutation.

## Success criteria

The alpha is complete when a public GitHub source tag and reproducible AUR
package build both-device code from the pinned upstream commit, register both
USB IDs, accurately report Desktop alpha and IT experimental tiers, and pass
all automated/package security gates. Desktop may perform normal fprintd
enrollment only after its pairing-recovery gate passes. IT is never advertised
as functionally complete until its device-specific hardware matrix passes.
