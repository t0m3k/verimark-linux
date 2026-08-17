# s-celles VeriMark commit inventory

This inventory covers the exact 61-commit linear range
`d79f157282085738ea8ffbe8c2ae96fb8b3ad831..66591aae03856bcefa7d7b4c0f08ea630f64b623`
from the s-celles libfprint fork. Every inherited commit is authored by
Sébastien Celles <s.celles@gmail.com> and modifies files within libfprint's
LGPL-2.1-or-later source tree. The retained commits were replayed in order onto
upstream `c4654fdc85c25afdd9115bec2f95a44145ae3b94`; their mail-patch `From:`,
`Date:`, and `Subject:` headers are preserved.

Before publication, the series was replayed through a mechanical sanitation
pass that replaces nonessential local machine, Windows-tooling, capture-file,
test-harness, and capture-derived fixture identifiers in commit messages and
content. Replaced protocol fixtures use obvious deterministic byte sequences
and are documented as synthetic. This does not change the 61-commit order,
authors, author dates, or licensing. The example device serial
`0011223344556677` used by the tests is explicitly synthetic and is not an
observed hardware identifier.

All 61 inherited commits are retained. Entries categorized as obsolete are
kept only to preserve the authored development sequence; later patches in the
same ordered series supersede their temporary logging or protocol experiments.
The materialized final tree therefore contains the later behavior, not the
intermediate experiment.

Three inherited commits carried Meson integration hunks written against the old
base: entries 1, 2, and 14. Their driver source changes retain Sébastien's
authorship, while the incompatible old Meson hunks are excluded from those
rebased commits. New current-upstream wiring, both generated USB-ID updates, the
offline AppStream check, and the `_GNU_SOURCE` compatibility guard live in
Tomasz Tracz's separate cleanup commit
`ebe889da9e5c3fb347be2e4e47caf505835fd075`.

The cleanup exposes only libfprint capabilities with implemented driver class
paths: identify, verify, storage, storage-list, and storage-delete. Capture and
duplicate-reporting feature bits are deliberately absent because this driver
does not implement those API paths.

The IT enroll-record commit at entry 51 was audited separately because its
original message described capture-derived protocol analysis. Its public mail
message now refers only to the documented protocol structure, and its source
uses a documented synthetic TUID and counter, a synthetic SID, and an optional
326-byte buffer that defaults to zeroes. It contains no captured credential
blob, private key, certificate, fingerprint template, or proprietary binary
bytes.

| # | Original commit | Rebased commit | Category | Decision | Subject | Reason |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | `d591cff340673695f16c0fb853d8d342cf15e08f` | `b9fc0f283882abec9ab7d4be38d0ba0df8eafedb` | Desktop | Retained | feat(verimark): add Kensington VeriMark DT driver (047d:00f2) | Retained; driver source preserved, while conflicting legacy Meson wiring is restored by the separate cleanup commit. |
| 2 | `8a1bac267f06bb6402fb82f75a4c38c95d7b2570` | `89d1b1f05c183c7fc12efa96340324a3b913995b` | Desktop | Retained | feat(verimark): wire all 8 vfuncs (list/delete/verify/identify/enroll) | Retained; driver source preserved, while conflicting legacy Meson wiring is restored by the separate cleanup commit. |
| 3 | `5f62a2374ecf8854236d8e11ae557c1abd8ab41d` | `f3ae107ff43e9f0a18820def342104e6036fcc8d` | test | Retained | test(verimark): ship the standalone TDD test suite and meson.build | Retained; the standalone TDD suite is part of the reviewable driver source. |
| 4 | `94b766b494d91818d9ea2edfa179c62dfe45843e` | `02c512d2725b754ccccd8b175e14ad861b764159` | Desktop | Retained | fix(verimark): close_notify on close + GError ownership cleanup | Retained; Desktop-specific integration or lifecycle behavior. |
| 5 | `b0950c1fc709f523cb70b7445a877768e236448a` | `76a7357c287d1c79812ad1e1dd050d82030f1aca` | Desktop | Retained | fix(verimark): set non-NULL username/description on list() prints | Retained; Desktop-specific integration or lifecycle behavior. |
| 6 | `3e511e87eab81d922bb0e37541c00aec61fd853f` | `4cd0a5bd8ff97074cff6ac17308a5e9dc84b80b2` | Desktop | Retained | fix(verimark): backfill description + username on enroll-time FpPrint | Retained; Desktop-specific integration or lifecycle behavior. |
| 7 | `a987418f1647e755e1c1050ad434b3655effff93` | `b7dd7560878d146ae511166fe7456819dfb80da0` | Desktop | Retained | fix(verimark): set enroll_date on list() prints | Retained; Desktop-specific integration or lifecycle behavior. |
| 8 | `8fda1981b42488dc7b3058d9d75b2f3b9288f2b0` | `a3305d3e3377f678f7810e50bbe9ce06795346ed` | Desktop | Retained | fix(verimark): enroll uses the device-assigned storage_handle as tuid | Retained; Desktop-specific integration or lifecycle behavior. |
| 9 | `026e1d69288436bb0016e7fa48505ac5c303d9c5` | `2d5ee14c202902f7f479bd7fa186d38afe80460d` | obsolete | Retained | chore(verimark): bump verify exit logs to fp_info for journal visibility | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 10 | `4f649592a9def70c0889a403711df6b018e56817` | `47d308b117eece3b32778318203ca601a000d200` | obsolete | Retained | chore(verimark): use fp_warn for verify diagnostic exits | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 11 | `1b639097f15b40c3580ebc0bab3b54e6dc0b9b15` | `73603dd90b0f0ebbe0c9c8067b0eb267a46881d1` | Desktop | Retained | fix(verimark): drop close-side TLS close_notify, recover stale state at open() | Retained; Desktop-specific integration or lifecycle behavior. |
| 12 | `e86690953221720e5e66e6bb363655b6d4a46782` | `4103978c00e14cf21739320b86fb4d1d3d7e1053` | Desktop | Retained | fix(verimark): USB-level reset at open() to recover from stuck state | Retained; Desktop-specific integration or lifecycle behavior. |
| 13 | `d696c2ced3d170e75bd23d02b6ffd7ca37135999` | `3f6aaea409f8970e545a4e76ded68ba0bfdbdfb5` | Desktop | Retained | feat(verimark): 3-attempt verify retry loop with WARM-mode-on-retry | Retained; Desktop-specific integration or lifecycle behavior. |
| 14 | `45ad43f09a289fb01f15fccade2325521b69a1ca` | `3b322048d4664611571c6de5e9d00ebf4cb2264e` | Desktop | Retained | feat(verimark): factory-fresh pairing bootstrap — step 1 (pure builders) | Retained; driver source preserved, while conflicting legacy Meson wiring is restored by the separate cleanup commit. |
| 15 | `bd1293ae1570be9a20b0e9f2eddcc198674d5170` | `3f685398baa69931f990b24abb4273eab607aa97` | Desktop | Retained | feat(verimark): factory-fresh pairing bootstrap — step 2 (crypto+orchestrator+hook) | Retained; Desktop-specific integration or lifecycle behavior. |
| 16 | `b6bdd46e1e1fdb8afc0aa3b0e686594fc569d7a3` | `02708373cc4984d5fc6e90fa916dae0a0ed72dee` | Desktop | Retained | fix(verimark): include glib/gstdio.h for g_chmod / g_rename | Retained; Desktop-specific integration or lifecycle behavior. |
| 17 | `27ca8629dbb449efa43d0ad5d6d155bb827965d3` | `1779ed065df9a6aac2f455e1e660972cb4764087` | obsolete | Retained | chore(verimark): clean up logging for upstream review (Phase 10.4) | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 18 | `8bcfbf12d2691d0e63990504aff5cb59d7317adf` | `afeab12cc35b720617804234367773b1ce3e8c4d` | shared | Retained | feat(verimark): Phase 10.3.a — async transport foundation | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 19 | `13d8a682e0f21a14b7018dfef609fda0ff9caa3d` | `9b0c039b0a5bf5533cf2c96a5ab60b27e3afe736` | shared | Retained | feat(verimark): Phase 10.3.b — session.call_opcode async | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 20 | `2d7b46c69ed1b4d8c5fcb6c38c1076de6b7c5cc6` | `905b47fa6eecf98b11388ca1e203a18bc10a01ca` | shared | Retained | fix(verimark): Phase 10.3.a async block was inside the wrong #ifdef branch | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 21 | `84a80c72489ac1e9fef9e34a4a7d04b5bda334f3` | `a23d22a30469a3c98cfc150b3011f02382a6e0cd` | shared | Retained | feat(verimark): Phase 10.3.c — async handshake | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 22 | `336e3024f44edcddbae69ae6010f26e27460c05e` | `2a7c5edf963962ffcc00205a099fe64aab0ad84f` | Desktop | Retained | feat(verimark): Phase 10.3.d — verify/identify async SSM | Retained; Desktop-specific integration or lifecycle behavior. |
| 23 | `c20053bea3cf7af63e364957290eb0af87482ce9` | `451a22372024263f65c2cfdbf312fe6bfab007d4` | Desktop | Retained | feat(verimark): Phase 10.3.e — async enroll SSM | Retained; Desktop-specific integration or lifecycle behavior. |
| 24 | `031fe66e2872e1093972bd5318d112cf0e5838fa` | `f130c1eac27b8f8bbe496f87aaa8f773e039842d` | shared | Retained | feat(verimark): Phase 10.3.f — cancellation polish (dev_class->cancel hook) | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 25 | `7cfe5a9668854873f8241aaa2ec84a399083b4cb` | `c8617291049fc5b8afc0c062b5c9800e7e36e078` | Desktop | Retained | feat(verimark): Phase 10.3.g — async open() handshake wiring | Retained; Desktop-specific integration or lifecycle behavior. |
| 26 | `865b0c066e08a31ed7065df82cf354f7d4691cad` | `c97f42832f3d2fa15fd1ffef351208181c894bd5` | shared | Retained | verimark: sanitize source comments for upstream submission | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 27 | `91ae5c5e0987b50b9fdb4fbf68a4153d76904f5d` | `e1451a09f2745120427d64c5f2d05e21e080d430` | shared | Retained | verimark: defer verify/identify complete to avoid pam_fprintd race | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 28 | `a048ce5fe5eedcfc2186fdb52d0acd31ee00d66b` | `031f50983b2d3bee3392dafc17bc1109c50d0aa3` | shared | Retained | verimark: make probe() return a stable device_id | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 29 | `411ea8c59f212df655efbbbdc8448e606c8f1ca9` | `4b7d926f6742c85e967201d77fcb08e41827fe4f` | IT | Retained | verimark: recognize the IT (047d:8054) at probe time (POC step 1) | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 30 | `c0954feee3922eeca9829b8ebf1de11eefcc9a95` | `914eca9c205b0fc08f8da4d5750236cf9886d27e` | IT | Retained | verimark: bootstrap the IT port (047d:8054) — BULK transport + constants | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 31 | `1398f5da19d0a55c0578d161604ba22c45583b05` | `d8b826d1a299a7577258384f6c50e6f2f804f3d8` | IT | Retained | verimark: high-level IT session reset helper (close_notify recovery) | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 32 | `10ae1bb7301480e13f34ebcc426c956644a5edc3` | `bef7961ccd20d7dc93be9c695fc92e0b91ff6c9e` | IT | Retained | verimark: IT-specific ClientHello builder (5 ciphers, no 0x00a9) | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 33 | `eca92e5bbfeb44386d295616318b5974240a7204` | `0c4e5b3468fcfd068328f047538831a824d5d45b` | IT | Retained | verimark: handshake orchestrator becomes IT-aware (is_it_variant flag) | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 34 | `47b5faa4b0477a4cd499840d461a2588ad7e2060` | `f2c750045ce64be3cde9c67679072cb8346acffc` | IT | Retained | verimark: wire the IT path inside open() — full Tudor TLS session | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 35 | `e47961add0225ee37579d94445a56e4722c1665d` | `69138d03abe2397eb286333f791d7b878cf79653` | IT | Retained | verimark: BULK async transceive for the IT handshake | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 36 | `320720c2de5106f18049ea6505bcf3c76494fa8f` | `e5190cbf490324ad92115622cf18a2f6812aa980` | IT | Retained | verimark: auto-route transceive_async to BULK on the IT (047d:8054) | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 37 | `0c19192da70c2b70c70e1c6170295733389a7e0b` | `7d249fd7ec87a3d660bfae520669dbf692d51c49` | IT | Retained | verimark: fix GTask leak when auto-routing IT calls to BULK | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 38 | `25d4ce235900b42a298eaf60719b70e354e05a60` | `3a393c606bcc68f21ac7b77f958f427f970afc23` | IT | Retained | verimark: accept 0x96 02 add_image status 0x8006 as IT-side complete signal | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 39 | `cbd0a12bc0e994ec025ef41ebbf8b771a57576fc` | `c032257c5368f6e8823f79d4eaeee54bcd751f8a` | IT | Retained | verimark: skip 0x96 03 commit on the IT (firmware auto-commits via 0x8006) | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 40 | `bf1001c60a52ffddd59f192e224c03e1f51ca749` | `999b975694791b3dc2ee517200f4d7bf9086f1aa` | obsolete | Retained | verimark: log the 0x99 match no-match response shape at info level | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 41 | `1bd9b94de7350e7e3f5581d58122c5873c8880bd` | `2fd1b17e5598a225c16609ef46802a5577ba4e21` | obsolete | Retained | verimark: temporarily log 0x99 no-match at WARN level for IT diagnose | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 42 | `b09440c7e3ed6748653ca2eb09cf1ecd267eb10b` | `37ab39ad42064a2cdf11a830ba5e0c49084683c6` | obsolete | Retained | verimark: log all vfy_cb_match branches at WARN level for IT diagnose | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 43 | `9e5f1636ca00cc1f0fa24e1f370e0bad497e99d7` | `1627d3a1c06277b4cb633bbb944be1559a5480e8` | IT | Retained | verimark: set enroll-date + IT-aware description on enroll success | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 44 | `87cd7ad675b4d406321678c46336a2aa513f282f` | `78b6679985cd7cae103289e499811d4081f8ea45` | obsolete | Retained | verimark: log VFY_S_AFTER_POLL and VFY_S_MATCH transitions for IT diagnose | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 45 | `3550a8ccca0e0f8c006f5b5b99955eb3d53001f6` | `93a613a4e5b655a275217fce41ff8edb715998f0` | obsolete | Retained | verimark: log pre/post getlist counts at ENR_S_RESOLVE_TUID for IT diagnose | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 46 | `3e9e8348ef45d42e8b5151abd0d95cb11771a893` | `6395a9cea4b645f7613d9ceef3e97d114ea19b10` | obsolete | Retained | verimark: send 0x96 03 commit on the IT with minimal 1-byte payload | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 47 | `b94e23e1a07683486e7c3d6b9721f35d58b1abf1` | `ef10ea4fe8381300ad3a6791ded4885b5f83ec93` | obsolete | Retained | verimark: try 17-byte 0x96 03 commit on IT (sub-cmd + TUID, no SID) | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 48 | `023197623029432559dd6b606661ded0c18cba4d` | `53246ce835bb66417e3f578023a5ce37d3bacc26` | obsolete | Retained | verimark: try 35-byte 0x96 03 commit on IT (DT prefix shape, no SID) | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 49 | `aec2dc28542c76f41a6cae4293d35e142edea5c5` | `296ab113aa110fd91428faae25e18d791461dbd6` | obsolete | Retained | verimark: send IT 0x96 03 commit with sub-cmd as u32 LE per DLL RE | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 50 | `3f304bbe33378eb86f77d2b482ad76dc2e065e22` | `f7d740b833291ae0ec7ad1b7d8b51bdb6441784b` | obsolete | Retained | verimark: try 28-byte IT 0x96 03 commit (sub-cmd + length + TUID) | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 51 | `5dce9e64710ddc174a911a87e3219007975ea96f` | `fa587e436fa0a693df3ad6abcfe97fc40c42fa0f` | IT | Retained | verimark: IT 0x96 03 commit builds the full 443-byte record (trace-decoded) | Retained; documented layout uses synthetic TUID, counter, and SID fixtures plus a zero-filled optional blob, with no captured credential bytes. |
| 52 | `f50712f2cfb0a3b7d2dd6aa1058728ecd712e279` | `9645b02aeaed119dea1049bb45936f8829a63180` | IT | Retained | verimark: cleanup IT diagnostic logs + decline delete-IT cleanly | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 53 | `c1e52018f3f98a63d811c166f02f34aff0d868f3` | `a785522d0a3c6f010984d3a9e85a9a3e0768628b` | obsolete | Retained | verimark: implement IT delete via 0xA4 with ANSI-381 sub-factor selector | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 54 | `ecbd94f7c60f02558d337a6e9571663004211c5d` | `78839342585beecd895802aab3f2c2e0663390c6` | shared | Retained | verimark: fix double-free in delete/list vfuncs (use g_steal_pointer) | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 55 | `b1dc557697d1228631d9b0db3a7bb3b143bfdd5d` | `4bb52f12ae53a47aed4b73632b79952c38e44494` | obsolete | Retained | verimark: pad IT 0xA4 delete payload to standard 12-byte Synaptics framing | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 56 | `6508ad9bbd9b43842fc071aa2330af2cfd5f89b9` | `d6c4df04d8f23f7c21600f72fb5ac0b219217b71` | obsolete | Retained | verimark: revert IT 0xA4 to 1-byte payload + add granular failure logging | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 57 | `c08ad24b8ecceaa4016cae1eec42ad9c7724073a` | `ae4ac45f4580d8971dedbae69cd581e148e8748c` | obsolete | Retained | verimark: drive IT delete 0xA4 over BULK directly (sync vtable was CONTROL-only) | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 58 | `a90b1d5ac21ecc4f0c633c9be7b14f0182b2373c` | `d0588c39737f3d6df3ee65070af31dcd4679d842` | IT | Retained | verimark: fix IT list (0x9f) + delete (0xA3) via async-over-sync wrapper | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 59 | `e4c7b7ce158cc981c37110012f2a2ae0ccd070ef` | `6c8e17366cb37b61646d07eb01a9e1d5da7d784c` | IT | Retained | verimark: trigger 0xA4 GC after IT 0xA3 delete to wipe ghost templates | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 60 | `b888e9f3e741335eae8c66ef2910333ecb9b99b5` | `314b6243b9a74be1e5e56fe505313dea6cb2a197` | IT | Retained | verimark: use 0xA4 01 cleanup (not 80/81 config) for IT post-delete GC | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 61 | `66591aae03856bcefa7d7b4c0f08ea630f64b623` | `7cea5581579ab59319c72a7a957437f13b3e9b5a` | Desktop | Retained | verimark: trigger 0xA4 01 cleanup GC after DT 0xA3 delete (symmetry with IT) | Retained; Desktop-specific integration or lifecycle behavior. |

## Totals

- Shared: 9 retained, 0 dropped.
- Desktop: 17 retained, 0 dropped.
- IT: 17 retained, 0 dropped.
- Test: 1 retained, 0 dropped.
- Obsolete: 17 retained for provenance, 0 dropped.
- Cleanup: one new Tomasz Tracz commit, not counted among the 61 inherited commits.
