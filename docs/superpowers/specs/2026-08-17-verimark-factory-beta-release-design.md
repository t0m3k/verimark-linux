# Kensington VeriMark Desktop factory-fresh beta release

Date: 2026-08-17

## Objective

Release a public Arch Linux beta that lets a user install one package, connect
a factory-fresh Kensington VeriMark Desktop (`047d:00f2`, K62330WW), and enroll
through the normal fprintd or desktop interface without Windows pairing data or
a separate provisioning command.

The first public milestone is a tagged GitHub source release and an AUR
package. Upstream libfprint inclusion is a later milestone informed by beta
hardware evidence and an early architecture discussion with its maintainers.

## Release scope

The beta supports only the VeriMark Desktop USB ID `047d:00f2`. Support for the
VeriMark IT (`047d:8054`), other Tudor-family devices, and distribution-native
packages outside Arch are excluded.

Factory-fresh readers are the supported pairing state. A reader already paired
by Windows must never be reset, re-paired, or have its pairing slot replaced.
The existing credential-loading path remains in the driver so future Windows
interoperability is not blocked, but the beta publishes no Windows extraction,
import, or credential-export tooling. When no compatible local credential is
available for an already-paired reader, the driver reports that pairing state
as unsupported without attempting recovery through reset or replacement.

## User experience

The expected first-use flow is:

1. Install `libfprint-verimark` from the AUR.
2. Connect a factory-fresh `047d:00f2` reader.
3. Open the distribution's normal fingerprint settings or run
   `fprintd-enroll`.
4. Start enrollment. This explicit mutation request initiates native pairing
   if the reader has no local pairing identity.
5. Pairing completes inside the driver, the generated identity is persisted,
   and the same enrollment operation continues.
6. Later enrollment and verification operations reuse the persisted identity
   automatically.

Device discovery, daemon startup, read-only diagnostics, and ordinary device
open must not initiate pairing. The beta requires no special pairing CLI.

## Runtime architecture

The runtime path remains:

```text
desktop settings or fprintd client
  -> fprintd D-Bus EnrollStart
    -> libfprint VeriMark enroll vfunc
      -> asynchronous pairing sub-state machine, when required
        -> versioned per-device persistent identity
      -> encrypted Tudor session
      -> normal sensor-side enrollment
```

Pairing belongs in the libfprint driver because fprintd exposes claim,
enrollment, verification, listing, and deletion but no separate provisioning
operation. Triggering from `EnrollStart` makes the sensor mutation correspond
to an explicit authorized user action while preserving the normal desktop
workflow.

All USB exchanges in pairing use libfprint's asynchronous state-machine and
cancellation patterns. No nested main loop, synchronous wrapper around an
asynchronous operation, or unbounded wait is permitted in the release path.

## Pairing state machine

The state machine has explicit states for:

1. Determining the device serial and local persistence state.
2. Loading and validating an existing finalized identity.
3. Refusing ambiguous, inconsistent, or already-paired states.
4. Generating a P-256 host keypair for an eligible factory-fresh operation.
5. Publishing a crash-recovery record before the sensor mutation.
6. Sending the single documented pairing exchange.
7. Validating the complete response and its sensor status.
8. Finalizing and atomically publishing the per-device credential.
9. Establishing the encrypted session with that identity.
10. Continuing the original enrollment request.

An already-paired response is terminal. It must not trigger a reset, a second
identity, or a retry that could replace sensor state. Transport ambiguity after
a pairing request is also terminal unless tests establish a recovery operation
that reuses the exact pending identity without rewriting the pairing slot.

The public beta remains blocked if interruption between sensor mutation and
credential publication can leave the reader orphaned without a demonstrated
same-identity recovery path. If this cannot be solved safely, factory pairing
retains an explicit experimental opt-in rather than being advertised as
out-of-the-box.

## Persistent identity storage

The driver uses a small storage-backend interface so the beta implementation
can later migrate to a libfprint-owned persistent-data API without changing the
pairing protocol.

For the Arch beta, the backend stores versioned per-device state under:

```text
/var/lib/fprint/verimark/
```

This is inside fprintd's systemd-managed `StateDirectory=fprint`. The directory
is mode `0700`. Final credentials and pending recovery records are regular
root-owned files with mode `0600`. Names derive from the biometric serial, not
from a global `sub1.bin`, and must reject unsafe or ambiguous serial forms.

Persistence must:

- traverse directories without following symlinks;
- create pending and finalized files with no-replace semantics;
- write through pinned directory descriptors;
- validate the complete credential before publication;
- flush file data and the containing directory at required durability
  boundaries;
- never overwrite or silently discard a pending or finalized identity;
- version both the filename namespace and serialized format;
- zero private-key material and derived session secrets when their lifetime
  ends; and
- never print credential content, keys, certificates, or derived secrets.

The beta storage format must include enough non-secret metadata to distinguish
pending, finalized, corrupt, wrong-device, and unsupported-version states.

Current libfprint master has no merged API for driver-specific persistent
secrets. An older `benzea/persistent-data` branch demonstrates an API intended
for data generated the first time a device is used. Before upstream submission,
maintainers must choose whether to revive that approach, add an equivalent
internal API, or accept driver-managed state. The beta format remains
migratable until that decision is made.

## Windows-path preservation

The working Windows-paired reference reader remains a regression fixture. Its
existing credential continues to load through the same abstract storage layer,
and refactoring must not change its sensor pairing slot or templates.

The public release contains no Windows collector, DPAPI workflow, registry
script, extracted Windows artifact, or import instructions. The release notes
state that already-paired readers without a compatible local identity are not
supported by this beta. This is a scope boundary, not removal of the underlying
interoperability path.

## Diagnostic CLI

The beta includes `verimarkctl` as a read-only support tool. It is not required
for pairing or ordinary authentication.

Installed commands are:

- `verimarkctl status`: report device presence, supported USB identity,
  installed driver/package version, fprintd availability, local persistence
  state, and whether an enrolled print is visible.
- `verimarkctl doctor`: run non-mutating checks for permissions, service
  availability, driver selection, expected ABI, credential structure, and
  common configuration failures.
- `verimarkctl report`: create a redacted diagnostic report suitable for a
  GitHub issue.

The CLI prefers fprintd D-Bus and read-only filesystem or sysfs inspection. It
must not access the USB interface directly while fprintd owns the reader.
Reports redact device serials by default and contain no pairing blob, private
key, certificate body, fingerprint template, biometric payload, registry data,
or unrestricted journal content.

The first beta excludes CLI commands for pairing, reset, deletion, credential
backup/export/import, or Windows integration. Raw pairing experiments remain
uninstalled developer-only test harnesses.

## Testing strategy

### Protocol and state-machine tests

Tests model factory-fresh success, already-paired refusal, malformed and short
responses, unexpected status values, timeouts, cancellation at every state,
USB disconnect, duplicate completion, and late callbacks. Pairing builders and
parsers use synthetic vectors only. The pairing path is exercised as a normal
libfprint asynchronous sub-state machine.

### Persistence fault injection

Tests inject failure before key generation, during pending-state publication,
before and after each durability boundary, during the USB exchange, and during
final publication. They verify that an identity is never silently replaced,
that temporary files are cleaned where safe, and that pending recovery evidence
is retained when cleanup would destroy the only recoverable identity.

Credential and pairing-response parsers receive fuzz coverage. Storage tests
cover symlinks, directory replacement, no-replace races, invalid serials,
truncation, oversized values, wrong-device records, unsupported versions,
permission errors, and full filesystems.

### Existing-reader regression

On the Windows-paired reference reader:

- list and verify existing Linux enrollment;
- enroll and delete only a designated Linux test print when required;
- confirm the existing credential is loaded without any bootstrap call;
- restart fprintd, reconnect USB, and reboot; and
- confirm Windows continues to recognize its original enrollment.

No test removes the reference credential, sends pairing without it, resets the
reader, or deletes unknown templates.

### Factory-fresh acceptance

Before the new reader is mutated, record redacted model, descriptor, firmware,
and serial-hash metadata. Run all simulated interruption tests before the
single real first-pair operation.

The real acceptance flow starts through normal fprintd or Omarchy enrollment
and confirms pairing occurs exactly once. It then covers successful enrollment,
at least 20 positive verifications, representative wrong-finger and poor-scan
attempts, listing, targeted deletion and re-enrollment, fprintd restart, USB
reconnect, and system reboot. The finalized credential must remain byte-stable
and securely permissioned throughout.

Destructive real-hardware interruption testing waits for another disposable
factory-fresh unit; the only fresh acceptance reader is not deliberately
orphaned to test crash boundaries.

### Build and security gates

Every candidate passes:

- the complete upstream libfprint test suite;
- the integrated VeriMark unit and protocol suite;
- warnings-as-errors and formatting checks;
- AddressSanitizer and UndefinedBehaviorSanitizer;
- Valgrind and available static analysis;
- a clean Arch chroot package build;
- package ABI, dependency, file-type, and content inspection;
- source-history and release-archive secret scanning;
- `verimarkctl` redaction and adversarial-output tests; and
- clean-environment install, upgrade, and rollback exercises.

## Packaging

The AUR package is named `libfprint-verimark`. It provides and conflicts with
Arch's `libfprint` while preserving the `libfprint-2.so` ABI required by stock
fprintd. It includes the driver, generated udev/hwdb data, `verimarkctl`, manual
pages, security notice, and rollback documentation.

The package builds from immutable inputs: an exact reviewed Sébastien Celles
libfprint commit and the checksummed patch series from a tagged project source
archive. It does not follow a moving VCS branch and does not contain a pairing
credential or machine-specific file.

Installation must not automatically pair a reader, enable PAM, enroll a
finger, reset hardware, or create a fake credential. Pairing remains a result
of the user's first normal enrollment request.

## Public repository

The public beta lives in a GitHub project repository. A later freedesktop
GitLab fork is used for upstream libfprint merge requests.

The publishable lineage begins cleanly from `main`. It brings across the
reviewed credential, packaging, and test work but excludes experimental
Windows-discovery commits, local PAM configuration work, ignored credentials,
build products, and internal task reports. Driver changes are an ordered patch
series against the exact external commit, with original authorship and LGPL
licensing preserved.

Before publication, the complete reachable Git history and generated release
archive are scanned for credentials, private-key markers, packet captures,
registry artifacts, machine identifiers, and local paths. The repository adds
an explicit license, README, security policy, contribution guide, release
notes, hardware-test reports, and privacy-safe issue templates.

No GitHub repository, release, issue, author contact, AUR package, or upstream
merge request is created without explicit user authorization at that stage.

## Release sequence

1. Create the clean factory-beta development lineage.
2. Rebase the Desktop driver work onto the selected current libfprint base.
3. Implement and fault-test the pairing state machine and persistence backend.
4. Implement and test the diagnostic-only `verimarkctl`.
5. Preserve the existing Windows-paired reader behavior.
6. Run factory-fresh acceptance on the new reader.
7. Build and test a release candidate in a clean Arch environment.
8. Obtain independent code, security, and package review.
9. With explicit authorization, publish GitHub `v0.1.0-beta.1` and checksums.
10. With explicit authorization, submit the immutable-tag AUR package.
11. Collect redacted reports from additional devices and firmware versions.
12. Discuss persistent-data architecture with libfprint maintainers.
13. Prepare a smaller Desktop-only upstream patch series backed by the beta
    evidence and protocol specification.

## Release blockers

The beta must not ship when any of the following is true:

- pairing can orphan a reader without a demonstrated recovery path;
- already-paired status is ambiguous or can trigger mutation;
- a retry can generate or publish a different identity;
- a secret appears in logs, diagnostics, source history, or package contents;
- storage durability, permissions, or no-replace behavior is unverified;
- cancellation, disconnect, or daemon termination can double-complete an
  operation or silently corrupt state;
- the existing paired reference reader regresses;
- clean installation or rollback fails; or
- the release cannot be reproduced from immutable public inputs.

## Success criteria

`v0.1.0-beta.1` is complete when a user on a clean Arch installation can:

1. Install `libfprint-verimark` from the AUR.
2. Connect a factory-fresh `047d:00f2` reader.
3. Enroll through ordinary desktop or fprintd tooling without Windows material
   or a special pairing command.
4. Verify reliably after fprintd restart, USB reconnect, and reboot.
5. Run `verimarkctl doctor` and produce a privacy-safe support report.
6. Reinstall stock libfprint using the documented rollback procedure.

The release must also preserve operation of the existing Windows-paired
reference reader when its compatible credential is already present, while
never advertising Windows credential acquisition as part of the beta.

## References

- fprintd device API: <https://fprint.freedesktop.org/fprintd-dev/Device.html>
- libfprint driver documentation: <https://fprint.freedesktop.org/libfprint-dev/>
- libfprint asynchronous state machines:
  <https://fprint.freedesktop.org/libfprint-dev/libfprint-2-Sequential-state-machine.html>
- Existing VeriMark issue:
  <https://gitlab.freedesktop.org/libfprint/libfprint/-/issues/575>
- Existing driver fork:
  <https://gitlab.freedesktop.org/s-celles/libfprint/-/tree/verimark-vfuncs>
- Published protocol research:
  <https://gist.github.com/s-celles/94cd114a580fb63524ce63432fd6fc92>
