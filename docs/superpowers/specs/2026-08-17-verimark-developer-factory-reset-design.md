# VeriMark Developer Factory Reset

Date: 2026-08-17

## Objective

Provide an explicitly enabled developer build of `verimarkctl` that can return
a Kensington VeriMark Desktop (`047d:00f2`) to its factory state by erasing the
reader's pairing identity and all fingerprint templates, then removing only
that reader's Linux pairing state.

The feature exists for driver development, recovery experiments, and
repeatable hardware testing. It is absent from normal builds and from the
public Arch/AUR beta package.

## Scope and consequences

A factory reset is intentionally destructive and irreversible. It removes:

- the reader's host-pairing identity;
- every fingerprint template stored by the reader; and
- the matching Linux pending, finalized, legacy-compatible, and reset-journal
  state after the reader confirms success.

Resetting a reader previously paired by Windows permanently breaks that
pairing and requires new pairing and enrollment on every operating system.
The tool presents this consequence before accepting confirmation.

Only USB ID `047d:00f2` is eligible. VeriMark IT `047d:8054`, other
Tudor-family devices, multiple-device ambiguity, and bulk reset are excluded.

## Build boundary

The libfprint driver adds a Meson feature option:

```text
-Dverimark_dev_reset=false
```

The default is `false`. With the default:

- reset protocol code is not compiled;
- the native reset helper is not built;
- `verimarkctl factory-reset` is not registered or shown in help;
- reset opcodes and confirmation strings are absent from binaries; and
- package policy tests reject any reset helper or reset-enabled configuration.

With `-Dverimark_dev_reset=true`, the build produces an uninstalled native
helper and enables the developer `verimarkctl factory-reset` command in the
matching source-tree invocation. The Arch/AUR PKGBUILD always passes
`-Dverimark_dev_reset=false` explicitly.

The feature cannot be enabled through an environment variable, marker file,
runtime configuration file, or command-line switch on a normal binary.

## Components

### `verimarkctl factory-reset`

The Python CLI owns presentation, read-only preflight, confirmation, journal
inspection, and invocation of the exact developer helper built from the same
source revision. It does not implement USB framing or open the USB interface.

The command requires:

- effective uid 0;
- an interactive controlling terminal for stdin and stderr;
- exactly one supported `047d:00f2` target, selected by its sysfs device path;
- fprintd to be stopped and the USB interface to be unclaimed;
- an existing valid local credential for the selected biometric serial;
- entry of the displayed device-specific serial-hash suffix; and
- a second exact confirmation: `ERASE WINDOWS PAIRING`.

There is no `--yes`, `--force`, stdin pipe, response file, multiple-device, or
remote mode. A failed confirmation exits before journal creation or USB I/O.

### Native reset helper

The helper is a small C executable linked to the same protocol and persistence
modules as the driver. It accepts a pinned sysfs device path, an already
created reset-journal identifier, and an inherited directory descriptor for
the state directory. It independently rechecks uid, USB ID, device identity,
journal binding, credential validity, and exclusive interface ownership.

The helper establishes an authenticated session with the existing credential
and sends at most one verified factory-reset request. It has no pairing,
enrollment, template export, arbitrary opcode, arbitrary USB path, or raw
credential-output mode.

### Reset journal

Before mutation, `verimarkctl` creates a versioned, non-secret journal under
`/var/lib/fprint/verimark/` using the same dirfd-pinned, symlink-safe,
no-replace, file-then-directory `fsync` rules as pairing persistence.

The journal contains only:

- format version;
- SHA-256 of the biometric serial;
- canonical credential filenames, never their contents;
- helper/build version;
- state `prepared`, `submitted`, `confirmed`, or `ambiguous`; and
- timestamps and the bounded sensor status code when available.

The journal never contains a raw serial, credential body, private key,
certificate, fingerprint template, biometric data, or USB payload.

## Transaction flow

The operation is:

```text
read-only preflight
  -> authenticated-session check
  -> two interactive confirmations
  -> durable prepared journal
  -> helper revalidation
  -> durable submitted journal
  -> one factory-reset exchange
  -> complete-response validation
  -> durable confirmed journal
  -> remove selected device's Linux pairing files
  -> fsync state directory
  -> remove confirmed journal
  -> fsync state directory
```

No reset request is sent until the prepared journal is durable. A local
credential remains available until the reader has returned a complete,
validated success response.

On confirmed success, cleanup removes only filenames derived from the exact
biometric serial bound into the journal. It never scans and deletes every
credential in the directory. Secure physical erasure cannot be guaranteed on
flash-backed filesystems; the tool removes directory entries and documents
that limitation rather than claiming cryptographic erasure.

The command never pairs the reader after reset. A subsequent normal fprintd
enrollment follows the factory-fresh pairing path.

## Failure and recovery behavior

Failures before request submission retain the credential and remove a journal
only when doing so cannot discard evidence needed to diagnose ambiguity.

A complete sensor refusal or validated non-success status retains the
credential and records the terminal status. The command does not retry.

Timeout, cancellation, USB disconnect, helper termination, daemon crash, or
short/malformed response after submission creates or retains `ambiguous`
state. While ambiguous state exists:

- the helper refuses another reset request;
- pairing and enrollment refuse to mutate the reader;
- `verimarkctl` performs only read-only state detection; and
- cleanup occurs only after the reader is proven factory-fresh.

If the reader is still authenticated with the old identity, the tool reports
that reset did not complete and retains the credential. If the reader is
provably factory-fresh, it completes local credential cleanup without sending
another reset. If neither state is provable, it leaves the journal and
credential intact and requires developer investigation.

A crash after confirmed sensor success but before local cleanup is therefore
recoverable: the confirmed journal directs the next invocation to verify
factory-fresh state and finish only the local removal.

## Logging and privacy

Console output and developer reports may contain only the serial hash,
transition name, helper/build version, bounded status code, and timestamp.
They never include raw serials, credentials, private keys, certificates,
fingerprint templates, biometric data, packet contents, or unrestricted
journal output.

The exact confirmation text warns that Windows pairing and every fingerprint
template will be destroyed. It does not imply that local file deletion can
securely erase prior flash blocks.

## Testing

### Unit and state-machine tests

Fake transports cover:

- confirmed success;
- already factory-fresh refusal;
- unsupported and multiple-device refusal;
- invalid or missing local credential;
- malformed, truncated, oversized, and unexpected responses;
- every pre-submission and post-submission cancellation boundary;
- timeouts and USB disconnects;
- duplicate and late callbacks;
- helper termination and CLI termination;
- stale, corrupt, wrong-device, and unsupported-version journals;
- cleanup permission and full-filesystem failures; and
- restart from every durable journal state.

Every test asserts at most one reset submission, at most one completion, exact
device binding, and no pairing or enrollment operation.

### Filesystem and adversarial tests

Tests cover symlink components, directory replacement, no-replace races,
invalid filenames, ownership and mode failures, interrupted writes, each
`fsync` boundary, and an attacker replacing sysfs or state paths between CLI
preflight and helper execution.

### Build and package tests

Default-build tests prove that reset source is excluded, the subcommand is
absent from help, the helper does not exist, and reset opcode/confirmation
markers are absent from binaries. Developer-build tests prove that all three
are present only with `-Dverimark_dev_reset=true`.

Arch package tests fail if the PKGBUILD omits the explicit false setting,
installs the helper, exposes the subcommand, or contains reset-enabled binary
markers.

### Hardware acceptance

Hardware reset testing uses a disposable reader that is neither the protected
Windows-paired reference reader nor the sole factory-fresh beta acceptance
reader. The sequence is:

1. Pair and enroll test-only fingerprints.
2. Verify across fprintd restart, reconnect, and reboot.
3. Run one confirmed developer reset without interruption.
4. Prove all templates and the pairing identity are absent.
5. Prove the old local credential cannot authenticate.
6. Confirm local state cleanup is limited to that reader.
7. Pair and enroll again through normal fprintd.
8. Verify across restart, reconnect, and reboot again.

Destructive interruption testing requires an additional disposable reader.
It is not simulated by deliberately orphaning the only reset-test unit.

## Release boundary

The public beta and AUR package do not contain reset capability. Public
documentation may state that a developer-only reset experiment exists, but it
does not provide a prebuilt reset binary or suggest reset as recovery for an
already-paired reader.

Promoting reset into public builds requires a separate design, hardware
evidence across multiple disposable units, security review, and explicit user
approval. Upstream submission of reset support is independent from upstreaming
ordinary Desktop pairing and authentication.

## Success criteria

The developer reset feature is complete when:

1. normal and AUR builds provably contain no reset capability;
2. the opt-in developer build exposes only the narrowly bounded command;
3. all confirmation, protocol, journal, crash-recovery, and filesystem tests
   pass under normal and sanitizer builds;
4. one disposable reader returns to factory-fresh state and can be paired and
   enrolled again through normal fprintd;
5. no operation touches the protected Windows-paired reference reader or the
   factory-fresh beta acceptance reader; and
6. ambiguous outcomes never trigger an automatic retry or deletion of the
   only recoverable credential.
