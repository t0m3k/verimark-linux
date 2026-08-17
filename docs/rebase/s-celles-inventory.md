# s-celles VeriMark commit inventory

This inventory covers the exact 61-commit linear range
`d79f157282085738ea8ffbe8c2ae96fb8b3ad831..66591aae03856bcefa7d7b4c0f08ea630f64b623`
from the s-celles libfprint fork. Every inherited commit is authored by
Sébastien Celles <s.celles@gmail.com> and modifies files within libfprint's
LGPL-2.1-or-later source tree. The retained commits were replayed in order onto
upstream `c4654fdc85c25afdd9115bec2f95a44145ae3b94`; their mail-patch `From:`,
`Date:`, and `Subject:` headers are preserved.

Before publication, the series was replayed through a mechanical sanitation
pass that replaces nonessential local machine, Windows-tooling, trace-file, and
test-harness identifiers in commit messages and content. This does not change
the 61-commit order, authors, author dates, or licensing. The example device
serial `0011223344556677` used by the tests is explicitly synthetic and is not
an observed hardware identifier.

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
`dde31ac31cebdd6f33392a4206ac72c2311a55d0`.

The cleanup exposes only libfprint capabilities with implemented driver class
paths: identify, verify, storage, storage-list, and storage-delete. Capture and
duplicate-reporting feature bits are deliberately absent because this driver
does not implement those API paths.

The IT enroll-record commit at entry 51 was audited separately because its
message describes trace-derived protocol analysis. Its public source contains
a synthetic SID and an optional 326-byte buffer that defaults to zeroes. It
contains no captured credential blob, private key, certificate, fingerprint
template, or proprietary binary bytes.

| # | Original commit | Rebased commit | Category | Decision | Subject | Reason |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | `d591cff340673695f16c0fb853d8d342cf15e08f` | `feb02b74f421db99bf107044a7ed97c08272b458` | Desktop | Retained | feat(verimark): add Kensington VeriMark DT driver (047d:00f2) | Retained; driver source preserved, while conflicting legacy Meson wiring is restored by the separate cleanup commit. |
| 2 | `8a1bac267f06bb6402fb82f75a4c38c95d7b2570` | `42d4376ebc43668d8991a75f7c9e6e1a9c8b89ea` | Desktop | Retained | feat(verimark): wire all 8 vfuncs (list/delete/verify/identify/enroll) | Retained; driver source preserved, while conflicting legacy Meson wiring is restored by the separate cleanup commit. |
| 3 | `5f62a2374ecf8854236d8e11ae557c1abd8ab41d` | `67cf9fffbae6efd92c371a1fd478d23ae8b48a22` | test | Retained | test(verimark): ship the standalone TDD test suite and meson.build | Retained; the standalone TDD suite is part of the reviewable driver source. |
| 4 | `94b766b494d91818d9ea2edfa179c62dfe45843e` | `ba07d9297e9cb659ce051dee80fd9c16a850ef63` | Desktop | Retained | fix(verimark): close_notify on close + GError ownership cleanup | Retained; Desktop-specific integration or lifecycle behavior. |
| 5 | `b0950c1fc709f523cb70b7445a877768e236448a` | `dbe4e077da03c3bf563a3fb7df4be1440411ba76` | Desktop | Retained | fix(verimark): set non-NULL username/description on list() prints | Retained; Desktop-specific integration or lifecycle behavior. |
| 6 | `3e511e87eab81d922bb0e37541c00aec61fd853f` | `1127513539ea78e6dce0e8c8929f4c2b30515c52` | Desktop | Retained | fix(verimark): backfill description + username on enroll-time FpPrint | Retained; Desktop-specific integration or lifecycle behavior. |
| 7 | `a987418f1647e755e1c1050ad434b3655effff93` | `1a2c210eca149a46c773f243e04a4405ea7b0e4c` | Desktop | Retained | fix(verimark): set enroll_date on list() prints | Retained; Desktop-specific integration or lifecycle behavior. |
| 8 | `8fda1981b42488dc7b3058d9d75b2f3b9288f2b0` | `01257feee05dd60ec7b02f2bc521a8987a2d4b24` | Desktop | Retained | fix(verimark): enroll uses the device-assigned storage_handle as tuid | Retained; Desktop-specific integration or lifecycle behavior. |
| 9 | `026e1d69288436bb0016e7fa48505ac5c303d9c5` | `c7e45c33aafcbae21717dc7f7b32522bf9d62aee` | obsolete | Retained | chore(verimark): bump verify exit logs to fp_info for journal visibility | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 10 | `4f649592a9def70c0889a403711df6b018e56817` | `44e099f691b05c5c057856dd39627b5788451a1a` | obsolete | Retained | chore(verimark): use fp_warn for verify diagnostic exits | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 11 | `1b639097f15b40c3580ebc0bab3b54e6dc0b9b15` | `11edcb0d7a747ddcb1ca3f1f0b9ae35424030fbf` | Desktop | Retained | fix(verimark): drop close-side TLS close_notify, recover stale state at open() | Retained; Desktop-specific integration or lifecycle behavior. |
| 12 | `e86690953221720e5e66e6bb363655b6d4a46782` | `74ec88704d27e5613691ed1015ade9e361839156` | Desktop | Retained | fix(verimark): USB-level reset at open() to recover from stuck state | Retained; Desktop-specific integration or lifecycle behavior. |
| 13 | `d696c2ced3d170e75bd23d02b6ffd7ca37135999` | `5ab20e79284767838a7fc1dcee2e3211c139c14c` | Desktop | Retained | feat(verimark): 3-attempt verify retry loop with WARM-mode-on-retry | Retained; Desktop-specific integration or lifecycle behavior. |
| 14 | `45ad43f09a289fb01f15fccade2325521b69a1ca` | `673dcbff925e21583671ec2611708cfe7da047a7` | Desktop | Retained | feat(verimark): factory-fresh pairing bootstrap — step 1 (pure builders) | Retained; driver source preserved, while conflicting legacy Meson wiring is restored by the separate cleanup commit. |
| 15 | `bd1293ae1570be9a20b0e9f2eddcc198674d5170` | `65f2f29bc87289a1895969d7505f6353b4819e5d` | Desktop | Retained | feat(verimark): factory-fresh pairing bootstrap — step 2 (crypto+orchestrator+hook) | Retained; Desktop-specific integration or lifecycle behavior. |
| 16 | `b6bdd46e1e1fdb8afc0aa3b0e686594fc569d7a3` | `374f07804185d3936096c2b144d30959fa65d3cb` | Desktop | Retained | fix(verimark): include glib/gstdio.h for g_chmod / g_rename | Retained; Desktop-specific integration or lifecycle behavior. |
| 17 | `27ca8629dbb449efa43d0ad5d6d155bb827965d3` | `d5b330e5690f1f5e6e17cbf4089cde64e1cfbd47` | obsolete | Retained | chore(verimark): clean up logging for upstream review (Phase 10.4) | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 18 | `8bcfbf12d2691d0e63990504aff5cb59d7317adf` | `c01b8422bb11a57474ddab6f3c04b86751efea55` | shared | Retained | feat(verimark): Phase 10.3.a — async transport foundation | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 19 | `13d8a682e0f21a14b7018dfef609fda0ff9caa3d` | `50cf065a658b602c8748ef9c64afce5702c57d47` | shared | Retained | feat(verimark): Phase 10.3.b — session.call_opcode async | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 20 | `2d7b46c69ed1b4d8c5fcb6c38c1076de6b7c5cc6` | `b605fb30f62ae00dd3f209b962bad17b703fec2f` | shared | Retained | fix(verimark): Phase 10.3.a async block was inside the wrong #ifdef branch | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 21 | `84a80c72489ac1e9fef9e34a4a7d04b5bda334f3` | `6f9a65c6ee75fd4a93a586969b220d8ca3eb1b95` | shared | Retained | feat(verimark): Phase 10.3.c — async handshake | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 22 | `336e3024f44edcddbae69ae6010f26e27460c05e` | `35df900114a5962b0f9d3002a5c7956ee036b60c` | Desktop | Retained | feat(verimark): Phase 10.3.d — verify/identify async SSM | Retained; Desktop-specific integration or lifecycle behavior. |
| 23 | `c20053bea3cf7af63e364957290eb0af87482ce9` | `9a1179032af602b10e54011a0f30891dd013169e` | Desktop | Retained | feat(verimark): Phase 10.3.e — async enroll SSM | Retained; Desktop-specific integration or lifecycle behavior. |
| 24 | `031fe66e2872e1093972bd5318d112cf0e5838fa` | `fc4f4530e73bbd317d06f32047c8978d3580b9f4` | shared | Retained | feat(verimark): Phase 10.3.f — cancellation polish (dev_class->cancel hook) | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 25 | `7cfe5a9668854873f8241aaa2ec84a399083b4cb` | `1654fcdea176b424d39b31a23cd9c95f43dccb21` | Desktop | Retained | feat(verimark): Phase 10.3.g — async open() handshake wiring | Retained; Desktop-specific integration or lifecycle behavior. |
| 26 | `865b0c066e08a31ed7065df82cf354f7d4691cad` | `96279a2453928a76df67172c07d220dccbb2c4ce` | shared | Retained | verimark: sanitize source comments for upstream submission | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 27 | `91ae5c5e0987b50b9fdb4fbf68a4153d76904f5d` | `61f3530f8dee6f77b5f8318394bbf567bf181371` | shared | Retained | verimark: defer verify/identify complete to avoid pam_fprintd race | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 28 | `a048ce5fe5eedcfc2186fdb52d0acd31ee00d66b` | `a1593ac4affbeb73d4f74af21cee032f4e3ca6a7` | shared | Retained | verimark: make probe() return a stable device_id | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 29 | `411ea8c59f212df655efbbbdc8448e606c8f1ca9` | `7546500494d5c2ece91a9a46a60ccd8044ec2369` | IT | Retained | verimark: recognize the IT (047d:8054) at probe time (POC step 1) | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 30 | `c0954feee3922eeca9829b8ebf1de11eefcc9a95` | `732e369e58a28044e062ac6561c84a9284f9ebaa` | IT | Retained | verimark: bootstrap the IT port (047d:8054) — BULK transport + constants | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 31 | `1398f5da19d0a55c0578d161604ba22c45583b05` | `392fafd35265541e84180ab72af5a0fdb87b14fe` | IT | Retained | verimark: high-level IT session reset helper (close_notify recovery) | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 32 | `10ae1bb7301480e13f34ebcc426c956644a5edc3` | `518a13c3054e0574264b1e458445201d9bc61840` | IT | Retained | verimark: IT-specific ClientHello builder (5 ciphers, no 0x00a9) | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 33 | `eca92e5bbfeb44386d295616318b5974240a7204` | `5803a562f87398eda44091f7e97ef7292120676a` | IT | Retained | verimark: handshake orchestrator becomes IT-aware (is_it_variant flag) | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 34 | `47b5faa4b0477a4cd499840d461a2588ad7e2060` | `355fb69b4a8f6e429536c79da2088008a855b2f7` | IT | Retained | verimark: wire the IT path inside open() — full Tudor TLS session | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 35 | `e47961add0225ee37579d94445a56e4722c1665d` | `9f00dac7ba13e56016a2e5b599d16e46db192744` | IT | Retained | verimark: BULK async transceive for the IT handshake | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 36 | `320720c2de5106f18049ea6505bcf3c76494fa8f` | `6899f0fc95c617f10b6856a71dfc8e31f9f3b16a` | IT | Retained | verimark: auto-route transceive_async to BULK on the IT (047d:8054) | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 37 | `0c19192da70c2b70c70e1c6170295733389a7e0b` | `6a460c9eacfce3d204346a8e029fd71f4ae6fa2a` | IT | Retained | verimark: fix GTask leak when auto-routing IT calls to BULK | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 38 | `25d4ce235900b42a298eaf60719b70e354e05a60` | `f3ca08f4d11d5ead8040c8cd70e0cc008d7449a9` | IT | Retained | verimark: accept 0x96 02 add_image status 0x8006 as IT-side complete signal | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 39 | `cbd0a12bc0e994ec025ef41ebbf8b771a57576fc` | `e66a3b2cb564daf88a6626e7b2b86ef6a6c789c0` | IT | Retained | verimark: skip 0x96 03 commit on the IT (firmware auto-commits via 0x8006) | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 40 | `bf1001c60a52ffddd59f192e224c03e1f51ca749` | `53a02f4b2494c2eca82552027290d5b52202abde` | obsolete | Retained | verimark: log the 0x99 match no-match response shape at info level | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 41 | `1bd9b94de7350e7e3f5581d58122c5873c8880bd` | `38824fadcaf8a654ff8ab3cf1c3bcf1a4c884da1` | obsolete | Retained | verimark: temporarily log 0x99 no-match at WARN level for IT diagnose | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 42 | `b09440c7e3ed6748653ca2eb09cf1ecd267eb10b` | `79e28c1b178fe1a7f4582ad4a5dba67a193cae5a` | obsolete | Retained | verimark: log all vfy_cb_match branches at WARN level for IT diagnose | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 43 | `9e5f1636ca00cc1f0fa24e1f370e0bad497e99d7` | `a411073e2ac593213e73ac53f5b7708b65480497` | IT | Retained | verimark: set enroll-date + IT-aware description on enroll success | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 44 | `87cd7ad675b4d406321678c46336a2aa513f282f` | `ce49e71d7d9fdcc4a25f0bb7fc0579e4719063e0` | obsolete | Retained | verimark: log VFY_S_AFTER_POLL and VFY_S_MATCH transitions for IT diagnose | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 45 | `3550a8ccca0e0f8c006f5b5b99955eb3d53001f6` | `917c95ecf782704e03ef1c3c0ebc9dbe9228b4e9` | obsolete | Retained | verimark: log pre/post getlist counts at ENR_S_RESOLVE_TUID for IT diagnose | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 46 | `3e9e8348ef45d42e8b5151abd0d95cb11771a893` | `e55559a79ffa4837a910b993c7d229c3ad8e4013` | obsolete | Retained | verimark: send 0x96 03 commit on the IT with minimal 1-byte payload | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 47 | `b94e23e1a07683486e7c3d6b9721f35d58b1abf1` | `97484d8521c4062bf9eb2cdb62485b48d6b58115` | obsolete | Retained | verimark: try 17-byte 0x96 03 commit on IT (sub-cmd + TUID, no SID) | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 48 | `023197623029432559dd6b606661ded0c18cba4d` | `415dc765891ed24f537c43f0ba4b71506a8c8aac` | obsolete | Retained | verimark: try 35-byte 0x96 03 commit on IT (DT prefix shape, no SID) | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 49 | `aec2dc28542c76f41a6cae4293d35e142edea5c5` | `2e2c50e8838a71d339091709428e00410a6f9294` | obsolete | Retained | verimark: send IT 0x96 03 commit with sub-cmd as u32 LE per DLL RE | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 50 | `3f304bbe33378eb86f77d2b482ad76dc2e065e22` | `301db27a63ddcef5988f051cba104462180d7057` | obsolete | Retained | verimark: try 28-byte IT 0x96 03 commit (sub-cmd + length + TUID) | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 51 | `5dce9e64710ddc174a911a87e3219007975ea96f` | `2cfb8306e610ec9b02034c694467746e81a999ca` | IT | Retained | verimark: IT 0x96 03 commit builds the full 443-byte record (trace-decoded) | Retained; documented layout uses a synthetic SID and a zero-filled optional blob, with no captured credential bytes. |
| 52 | `f50712f2cfb0a3b7d2dd6aa1058728ecd712e279` | `29ec83354738c4e313ca17e0871410c4c9dbbc47` | IT | Retained | verimark: cleanup IT diagnostic logs + decline delete-IT cleanly | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 53 | `c1e52018f3f98a63d811c166f02f34aff0d868f3` | `9e11c6e101371cd1bf6990cb2fb5c66813e72335` | obsolete | Retained | verimark: implement IT delete via 0xA4 with ANSI-381 sub-factor selector | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 54 | `ecbd94f7c60f02558d337a6e9571663004211c5d` | `23041190743ab1629d0bfd0f58b44a27105deaea` | shared | Retained | verimark: fix double-free in delete/list vfuncs (use g_steal_pointer) | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 55 | `b1dc557697d1228631d9b0db3a7bb3b143bfdd5d` | `00ec321bbedfa883a4687bc8c9325cf4be07ee30` | obsolete | Retained | verimark: pad IT 0xA4 delete payload to standard 12-byte Synaptics framing | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 56 | `6508ad9bbd9b43842fc071aa2330af2cfd5f89b9` | `56986fdbd98515a6ae7c324221c3de9f5e9fd7b8` | obsolete | Retained | verimark: revert IT 0xA4 to 1-byte payload + add granular failure logging | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 57 | `c08ad24b8ecceaa4016cae1eec42ad9c7724073a` | `d980fe627625eca6b553602d6d88cf427cdb3c59` | obsolete | Retained | verimark: drive IT delete 0xA4 over BULK directly (sync vtable was CONTROL-only) | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 58 | `a90b1d5ac21ecc4f0c633c9be7b14f0182b2373c` | `0caebfeac5af89ecd950fc43f9dee66679475129` | IT | Retained | verimark: fix IT list (0x9f) + delete (0xA3) via async-over-sync wrapper | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 59 | `e4c7b7ce158cc981c37110012f2a2ae0ccd070ef` | `70676335aa0c3d5d5e3eed457a1e9f3b9fd8ff86` | IT | Retained | verimark: trigger 0xA4 GC after IT 0xA3 delete to wipe ghost templates | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 60 | `b888e9f3e741335eae8c66ef2910333ecb9b99b5` | `fe89c5c21c4b3d33b5bdf74b762e1557e046cf3b` | IT | Retained | verimark: use 0xA4 01 cleanup (not 80/81 config) for IT post-delete GC | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 61 | `66591aae03856bcefa7d7b4c0f08ea630f64b623` | `ba079f263f1bd4a94a6dc2c33c532601e0f64df4` | Desktop | Retained | verimark: trigger 0xA4 01 cleanup GC after DT 0xA3 delete (symmetry with IT) | Retained; Desktop-specific integration or lifecycle behavior. |

## Totals

- Shared: 9 retained, 0 dropped.
- Desktop: 17 retained, 0 dropped.
- IT: 17 retained, 0 dropped.
- Test: 1 retained, 0 dropped.
- Obsolete: 17 retained for provenance, 0 dropped.
- Cleanup: one new Tomasz Tracz commit, not counted among the 61 inherited commits.
