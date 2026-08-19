# VeriMark Linux

Experimental Linux support for the Kensington VeriMark Desktop fingerprint
reader through libfprint and fprintd.

## Status

This project is beta software. The supported device is the Kensington VeriMark
Desktop with USB ID `047d:00f2`.

The VeriMark IT (`047d:8054`) and other Tudor-family readers are not supported
by this release.

## What It Provides

- A Desktop-only VeriMark driver integrated with libfprint.
- Factory-fresh pairing and enrollment through ordinary fprintd interfaces.
- An Arch Linux package in `packaging/arch/`.
- A deterministic, reviewable libfprint patch series under
  `patches/libfprint/`.
- Synthetic protocol and driver tests without requiring a reader.

## Safety Boundaries

- Opening or discovering a reader does not pair, reset, or mutate it.
- Factory pairing starts only from an explicit enrollment operation.
- Already-paired or ambiguous pairing responses are treated as terminal.
- Pairing credentials and private keys are never included in the repository,
  package sources, logs, or test reports.
- This project does not provide Windows credential extraction, DPAPI or
  registry tooling, credential import/export, or factory-reset tooling.

## Install From Source

Build the Arch package locally:

```bash
cd packaging/arch
makepkg -si
```

The package replaces the stock `libfprint` package while preserving the
`libfprint-2.so` ABI used by fprintd. Installation does not pair hardware or
enroll a finger.

After installation, use the normal fprintd commands, for example:

```bash
fprintd-enroll
fprintd-verify
```

Hardware pairing is destructive on a factory-fresh reader. Review the beta
release documentation and make sure the target reader is the intended device
before starting enrollment.

## Development

Run the repository tests:

```bash
python -m unittest discover -v
```

Materialize and build the pinned libfprint source with the checked patch
series:

```bash
tools/materialize-libfprint /tmp/verimark-libfprint
```

The materializer builds both the normal libfprint tree and the standalone
VeriMark test suite. Hardware acceptance testing is separate from these
synthetic tests.

## Repository Layout

- `packaging/arch/`: Arch package definition and generated package metadata.
- `patches/libfprint/`: ordered, checksum-pinned libfprint patches.
- `tools/`: patch export, source materialization, and credential inspection
  helpers.
- `verimark_support/`: redaction-safe Python support code.
- `tests/`: packaging, lineage, parser, CLI, and patch-series tests.
- `docs/`: design, implementation, and release notes.

## Contributing

Keep changes reproducible and privacy-safe. Do not add credentials, packet
captures, raw serials, Windows registry data, unrestricted logs, or hardware
reports containing sensitive material.
