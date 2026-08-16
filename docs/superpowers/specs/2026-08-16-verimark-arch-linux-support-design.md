# Kensington VeriMark Desktop support on Arch Linux

Date: 2026-08-16

## Objective

Enable a Kensington VeriMark Desktop fingerprint reader (`047d:00f2`, model
K62330WW) on Arch Linux while preserving its existing Windows functionality.
Deliver command-line enrollment and verification first. Login, lock-screen,
and `sudo` integration are explicitly deferred until the driver is reliable.

The implementation will begin from the existing `verimark-vfuncs` libfprint
fork rather than repeating the completed protocol reverse engineering. The
fork must be treated as a proof of concept until its code, tests, packaging,
and failure behavior have been independently checked.

## Current state

The reader enumerates correctly over USB as `047d:00f2 Kensington VeriMark
Desktop`. Arch currently has `libfprint 1.94.100` and `fprintd 1.94.5`, but
`fprintd-list` returns `No devices available`. The USB ID is absent from the
upstream libfprint supported-device list.

The reader is a Synaptics Tudor-family Match-on-Chip device. Its biometric
interface is USB interface `MI_01`, while `MI_00` provides FIDO/U2F behavior.
Biometric commands use a device-specific encrypted session. Fingerprint
templates and matching stay inside the sensor.

The sensor has already been paired with Windows. Its Trust On First Use
pairing slot cannot currently be reset through a known Linux operation.
Therefore Linux must authenticate with the same host pairing identity used by
Windows. Creating a new Linux pairing is out of scope and could make the
reader unavailable to Windows.

## Chosen approach

Adopt and harden the existing native libfprint driver from the
`s-celles/libfprint` `verimark-vfuncs` branch. Pin builds to a reviewed commit;
the initial reference commit is `66591aae03856bcefa7d7b4c0f08ea630f64b623`.
Do not track an unpinned moving branch in an installed package.

The project will contain:

1. An Arch package for the patched libfprint.
2. An auditable Windows pairing-credential export workflow.
3. A Linux credential validator and installer that never displays secrets.
4. Reproducible build, runtime-test, and rollback instructions.
5. Notes and patches needed to move the driver toward upstream quality.

Loading proprietary Windows binaries on Linux and independently rewriting the
entire native driver are rejected for the first milestone. They remain fallback
options only if the existing native driver proves unusable.

## Architecture

The runtime path is:

```text
fprintd
  -> patched libfprint
    -> VeriMark driver
      -> USB interface MI_01
        -> encrypted Tudor session
          -> sensor-side enrollment and matching
```

The Windows exporter produces the existing host pairing blob, conventionally
called `sub1.bin`. The blob contains a client certificate, a P-256 private key,
and sensor certificate data. It is a credential, not ordinary configuration.
Linux installs it at a driver-supported system path under
`/var/lib/fprintd/verimark/`. The precise filename is selected from the
reader's serial number when reliable, with `sub1.bin` permitted only for the
single-device bring-up.

The file owner must be the effective identity of the installed `fprintd`
service and its mode must be `0600`. The containing directory must not be
accessible to unprivileged users. The implementation must inspect the actual
Arch service unit rather than assuming a service account.

## Credential acquisition and handling

The credential must be exported from the Windows installation that originally
paired the reader. The public driver fork consumes the blob but does not ship a
public DT extraction utility, so extraction is a distinct implementation task.

Before writing or running an exporter, locate the exact Synaptics pairing
record and establish how Windows protects it. Any existing researcher-provided
script must be obtained from its original source and reviewed before use. If
an exporter is written locally, it must do only the following:

- Run with the minimum Windows system identity required to unprotect the
  machine-scoped pairing record.
- Read the pairing value without changing the registry or sensor.
- DPAPI-unprotect the record and write the exact blob to a user-selected local
  destination.
- Print only structural metadata, sizes, and hashes; never print key bytes.
- Refuse to overwrite an existing output unless explicitly requested.

The blob must never be pasted into chat, attached to an issue, committed to
Git, or uploaded to cloud storage. Transfer should be direct and local, with
temporary copies minimized. The repository must ignore `sub1*.bin`, registry
exports, packet captures, crash dumps, and extracted Windows files from its
first commit.

The Linux validator will accept a path and check:

- File type, owner, and permissions.
- A conservative maximum size.
- The expected TLV structure and required tag lengths.
- That a client certificate, 32-byte private scalar, and sensor certificate
  are present.

It must report only pass/fail information and non-secret metadata. Secret
buffers must be cleared where practical, and logs must not include blob
contents.

## Arch packaging

Create a `libfprint-verimark-git` package pinned to the reviewed commit. It will
provide and conflict with Arch's `libfprint` package while retaining the same
shared-library ABI expected by the installed `fprintd`. Build dependencies
include the fork's Meson dependencies, notably GnuTLS, Nettle/Hogweed, GMP,
GLib, and libgusb.

The package build must:

- Verify the source commit and use a reproducible source declaration.
- Apply only repository-tracked patches.
- Run the upstream libfprint tests and VeriMark protocol tests before
  packaging.
- Avoid embedding the pairing credential or any machine-specific data.
- Install the relevant udev/hwdb data through the normal libfprint build.

Before installation, record the installed stock package version and confirm a
stock package is available locally or from the Arch repositories. Rollback is
reinstallation of stock `libfprint`, removal or quarantine of the pairing blob,
and restart of `fprintd`. No PAM file is changed during bring-up.

## Runtime validation

Validation proceeds in increasing-risk order and stops on the first unexpected
result:

1. Build and unit tests in an uninstalled build tree.
2. Inspect the built package contents and dependencies.
3. Install the credential with restrictive permissions.
4. Install the patched package and restart `fprintd`.
5. Confirm the device appears through libfprint/fprintd.
6. List templates without modifying sensor storage and record their opaque
   identifiers locally so later storage changes can be checked.
7. Enroll one clearly identified Linux test finger that is not already
   enrolled under Windows, then confirm exactly one new identifier appeared.
8. Verify the new Linux enrollment repeatedly: at least 20 positive attempts
   plus representative negative attempts, recording outcomes but no biometric
   payloads.
9. Delete only the new identifier and confirm the original identifier set is
   unchanged. Do not use a delete-all operation.
10. Re-enroll the Linux test finger, then repeat discovery and verification
    after an `fprintd` restart, USB unplug/replug, and system reboot.
11. Boot Windows and confirm its enrollment and verification still work.

No automated test may delete unknown templates, bootstrap pairing, reset the
device, or invoke an undocumented destructive opcode.

## Error handling and recovery

Malformed credentials, failed TLS authentication, USB timeouts, driver
crashes, inconsistent template identifiers, or unexpected sensor status codes
are hard stops. Collect redacted journal output and a backtrace when relevant;
never collect or publish the pairing blob or raw biometric traffic.

Package installation and rollback are explicit user-invoked operations. If
`fprintd` becomes unstable, stop it, reinstall stock libfprint, restart the
daemon, and verify that the original unsupported-device behavior is restored.
The credential should be quarantined rather than destroyed until both Linux
testing and the subsequent Windows verification have succeeded.

PAM, display-manager, lock-screen, and `sudo` configuration are outside the
first milestone. This prevents an experimental driver from causing an
authentication lockout.

## Success criteria

The Arch bring-up is complete when:

- `fprintd` consistently discovers `047d:00f2`.
- Listing, enrollment, verification, and deletion work without daemon crashes.
- Repeated positive and negative checks produce sensible results.
- Operation survives daemon restart, USB reconnect, and reboot.
- The reader continues to work on the paired Windows installation.
- Stock libfprint can be restored cleanly.
- No sensitive artifact appears in source control, build packages, or logs.

## Upstream and maintenance milestone

Local support does not imply upstream readiness. After bring-up, compare the
fork with current libfprint, run sanitizers, and audit credential lifetime,
file permissions, USB cancellation, state-machine behavior, timeouts, and all
error paths. Synchronous or blocking operations should be converted to normal
libfprint asynchronous state machines where maintainers require it.

Prepare small, reviewable commits and a hardware test report. Discuss the
expected architecture and maintenance burden with libfprint maintainers before
opening another merge request. No issue, merge request, email, or other
external communication will be sent without explicit user authorization. An
Arch package can remain the supported delivery mechanism while upstream work
continues.

## References

- libfprint supported devices: <https://fprint.freedesktop.org/supported-devices.html>
- Existing device issue: <https://gitlab.freedesktop.org/libfprint/libfprint/-/issues/575>
- Published DT protocol research: <https://gist.github.com/s-celles/94cd114a580fb63524ce63432fd6fc92>
- Earlier reverse-engineering notes: <https://blog.inexplicity.de/reverse-engineering-the-kensington-verimark-fingerprint-scanner.html>
- Existing driver fork: <https://gitlab.freedesktop.org/s-celles/libfprint/-/tree/verimark-vfuncs>
