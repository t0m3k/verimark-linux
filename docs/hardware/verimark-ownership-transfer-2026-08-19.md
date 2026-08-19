# VeriMark Ownership Transfer — Hardware Evidence and Decision

Date: 2026-08-19
Device class: Kensington VeriMark Desktop, USB ID `047d:00f2`
Status: **the ownership model in the design spec is contradicted by hardware**

## Decision

`verimarkctl take-ownership`, as specified in
`docs/superpowers/specs/2026-08-19-verimark-linux-ownership-transfer-design.md`,
targets a failure mode this device does not have. The spec assumes the reader
has one active host owner and that Linux must erase another operating system's
pairing identity before it can pair. Neither assumption holds.

Recommended disposition:

- Rewrite the ownership model around **pairing slots**, not single ownership.
- Keep plan Tasks 1–3 (confirmation, target preflight, fail-closed helper
  boundary). They are implemented, tested, and remain correct as guard rails.
- Drop plan Task 4 (native factory reset from a captured opcode) as written.
  The evidence below shows the opcode is not obtainable by bus capture, and
  that the operation it was meant to enable is not the blocking problem.
- Treat "all pairing slots occupied" as the only genuinely stuck state, and
  note that a Linux host holding a valid credential can open an authenticated
  session — so a slot-release issued from inside a Linux-owned session is a
  coherent design, unlike a reset issued by an unpaired host.

## Method

All device traffic was produced with the driver's own documented transport:
init via `bRequest 0x19` / `0x1A`, then transceive via `0x16` write with
`wValue = length & 7` and 8-byte alignment, `0x17` read. A standalone probe
reproduced the vendor host's cleartext bring-up byte-for-byte, which is what
establishes that the transport reimplementation is faithful.

Read-only opcodes used: `0x01` GET_DEVICE_INFO, `0x19` GET_START_INFO,
`0x3E` GET_STORAGE_INFO, `0x8E` IOTA_READ. The single destructive request
issued was `0x93` DoPairBasic, built exactly as `bootstrap.c` builds it
(400-byte wire cert, magic `0x5f3f`, ECDSA-P256/SHA-256 over `cert[0..142]`),
submitted once per attempt with no retry.

## Evidence

### 1. The sensor holds more than one host pairing at a time

A Linux credential created on 2026-08-17 authenticated successfully on
2026-08-19 at 17:55 (`fprintd-verify` → `verify-match`). The other operating
system signed in with its own credential earlier the same day and enrolled a
finger, using a client certificate that is byte-identical across the day and
never re-paired — no `0x93` exchange appears anywhere in the captures taken
during those sessions.

Both credentials are therefore simultaneously valid on the same sensor.

### 2. Template storage is partitioned per host

The other operating system erased all of its enrolled fingerprints through its
own vendor-supported removal path. The Linux-enrolled templates continued to
match on-chip afterwards. `0x3E` reports a three-entry partition table.

A removal performed by one host does not touch another host's templates, and
it does not clear that host's own pairing either.

### 3. `0x93` is refused once the sensor is populated

Two attempts, the second after a `USBDEVFS_RESET` power cycle with the
one-shot first `GET_START_INFO` block of that power cycle present:

```
--> 0x93 DoPairBasic, 401 bytes
<-- 4f 04      (2-byte response; status 0x4f04 big-endian, 0x044f little-endian)
```

The response is a bare status word, not the 802-byte pair response. The status
is not `0x0104` "unknown op", so the opcode and request framing were accepted
and the operation itself was refused. The refusal is stable and is not stale
session state.

### 4. The refusal cannot mean "already paired"

At some point a `0x93` succeeded against a sensor that already had an owner —
this is forced regardless of which host paired first, because both credentials
are valid now (§1) and only two hosts have ever paired this reader. Whichever
one paired second did so on an already-owned sensor.

A rule of "refuse whenever a pairing exists" would have rejected that second
pairing. It did not. Therefore `0x044f` reports a capacity or state condition,
not ownership — the most economical reading being that the available slots are
now full.

### 5. The reset opcode is not obtainable from bus captures

Every command and response body after the handshake is a TLS application-data
record. The session requires a client certificate of type `ecdsa_fixed_ecdh`
that the sensor bound to its host. Capturing the correct vendor operation would
still yield ciphertext. `wValue` is a transport-derived field
(`length & 7`), not a command selector, so no opcode can be inferred from it
positionally — the same logical message appears under different `wValue`s in
two captures.

## Defects found and fixed

Three defects surfaced during this work. All three are fixed in the patch
series and covered by tests.

1. **Double free on driver error paths** (`0038`). `verimark_list()` and
   `verimark_delete()` held their `GError` in a `g_autoptr` and passed it to
   completion functions documented `(transfer full)`. libfprint stores the
   error for a deferred idle return while the autoptr frees it at scope exit.
   Observed as a `SIGSEGV` in `fprintd` whenever a device with no usable
   pairing took one of those paths. Fixed with `g_steal_pointer()` at all
   eight call sites; regression test asserts no autoptr-owned error reaches a
   completion call.

2. **Refusals misreported as size errors** (`0036`). `verimark_bootstrap_pair`
   judged the response length before reading the status, so a real refusal
   returned `ERR_RESPONSE_SIZE` with `out_status` left at `0xffff`. The code
   the driver was written against (`0x0406`) exists only in a synthetic test
   fixture and is not what hardware returns. Fixed to read the status first
   and treat a short response with a non-zero status as an explicit refusal.

3. **Malformed P-256 domain parameters** (`0037`). `P256_A_LE` and `P256_P_LE`
   each carried a wrong 32-bit word, so reversing them produced integers that
   are not the NIST P-256 parameters. The bytes only reach the persisted
   params blob (sub1 tag 4) and never go on the wire, so no pairing was
   affected, but the stored credential documented unusable parameters.

## Open, and worth answering before any further ownership work

- **How many pairing slots exist, and can one be released?** This is now the
  only question standing between the current state and a working ownership
  story. `0x40` HOST_PARTITION_READ is the candidate probe; whether it answers
  before a session is open is untested.
- **Factory-fresh pairing is unreachable through `fprintd-enroll` in the
  current build.** `open()` completes successfully without a session, so
  `fprintd`'s pre-enroll duplicate check (`identify`) and its delete-before-
  re-enroll both fail first and the enroll vfunc is never called. This blocks
  the capability the README advertises. It is a design question rather than a
  clear defect — failing closed in `open()` would make pairing permanently
  unreachable, since the device must be opened before it can be enrolled — so
  it is recorded here rather than patched.

## Reproduction

The read-only probe and the single-shot `0x93` tool used here are not part of
the package. The probe is safe to re-run; the pairing tool is destructive,
requires an explicit `--yes-destructive` flag, and submits exactly one request.
Neither is required to reproduce §1 and §2, which need only `fprintd-verify`
and the partition table from `0x3E`.

No credentials, certificate bytes, packet captures, serials, or host registry
data are recorded in this document.
