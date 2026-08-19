# VeriMark Linux Ownership Transfer

Date: 2026-08-19

> **Status: the ownership model below is contradicted by hardware evidence.**
> The reader holds more than one host pairing at a time and partitions
> templates per host, so "one active host owner" does not describe this
> device, and `0x93` refusals report capacity rather than ownership. See
> `docs/hardware/verimark-ownership-transfer-2026-08-19.md` before acting on
> this spec.

## Objective

Make Linux use the Kensington VeriMark Desktop as a single-owner device after
it has been paired or enrolled by another operating system. Ownership transfer
is explicit and destructive: it erases the reader's pairing identity and
device-side fingerprint templates, then prepares Linux for a fresh pairing and
enrollment.

## Ownership Model

The reader is treated as having one active host owner and one active secure
session. Windows and Linux enrollment databases are not synchronized. A user
must explicitly transfer ownership before moving the reader between operating
systems.

Normal Linux operations never transfer ownership. In particular, daemon start,
USB discovery, `fprintd-list`, `fprintd-verify`, and ordinary
`fprintd-enroll` do not reset the reader or replace pairing credentials.

## Explicit Command

The ownership transfer command is:

```text
sudo verimarkctl take-ownership
```

It is the supported Linux-facing entry point to the existing destructive
factory-reset workflow. The Linux package exposes this command, but not a
generic or unscoped reset API. It must require interactive, device-specific
confirmation stating that Windows pairing and all device-side fingerprints
will be erased. There is no automatic, `--yes`, piped, or lock-screen
invocation.

The command performs the following transaction:

1. Stop or unclaim fprintd and identify exactly one supported Desktop reader.
2. Validate the target identity and existing Linux state without mutation.
3. Require the destructive confirmation.
4. Durably record a reset journal before USB mutation.
5. Authenticate with the existing Linux credential when available.
6. Submit at most one validated factory-reset request.
7. Confirm the reader is factory-fresh before deleting local Linux pairing state.
8. Remove only state bound to the selected reader.
9. Leave the reader factory-fresh; do not automatically pair or enroll it.

After successful transfer, the user runs ordinary `fprintd-enroll`. Pairing is
allowed during enrollment only when the reader is demonstrably factory-fresh.

## Safety Boundaries

- Only USB ID `047d:00f2` is supported.
- The command never operates on `047d:8054` or ambiguous devices.
- Factory reset is never performed by package installation or service startup.
- Existing pairing files are not removed before reset success is confirmed.
- Timeout, disconnect, malformed response, or ambiguous reset state prevents a
  second reset attempt and retains recovery evidence.
- Local deletion is filename-scoped and does not claim secure flash erasure.

## Linux Runtime Recovery

Ownership transfer is separate from normal session recovery. Once Linux owns
the reader, the driver must maintain that ownership across fprintd restart,
USB reconnect, suspend/resume, and lock-screen operation. A failed TLS reopen
must be reported as a protocol/session error, never as an empty enrollment
list. The driver must not attempt ownership transfer as an implicit recovery.

## Testing

Tests must cover:

- refusal to reset unsupported, missing, or ambiguous targets;
- exact interactive confirmation and refusal of non-interactive bypasses;
- durable reset journal states and restart recovery;
- at-most-one reset submission;
- cleanup only after confirmed factory-fresh state;
- no pairing or enrollment during reset;
- factory-fresh reader pairing through ordinary `fprintd-enroll`;
- list and verify across Linux daemon restart after ownership transfer;
- stale TLS recovery without false `NoEnrolledPrints` results; and
- preservation of existing pairing files when reset is unsuccessful.

## Success Criteria

Linux ownership transfer is complete when a user can explicitly erase a
Windows-owned reader, pair and enroll it on Linux, and then list and verify
fingerprints after fprintd restart without any automatic reset or cross-OS
state mutation.
