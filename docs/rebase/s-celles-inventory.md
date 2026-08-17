# s-celles VeriMark commit inventory

This inventory covers the exact 61-commit linear range
`d79f157282085738ea8ffbe8c2ae96fb8b3ad831..66591aae03856bcefa7d7b4c0f08ea630f64b623`
from the s-celles libfprint fork. Every inherited commit is authored by
Sébastien Celles <s.celles@gmail.com> and modifies files within libfprint's
LGPL-2.1-or-later source tree. The retained commits were replayed in order onto
upstream `c4654fdc85c25afdd9115bec2f95a44145ae3b94`; their mail-patch `From:`,
`Date:`, and `Subject:` headers are preserved.

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
`6bf40743474440760ae80d20ec310c09f11a7caf`.

The IT enroll-record commit at entry 51 was audited separately because its
message describes Windows-derived protocol analysis. Its public source contains
a synthetic SID and an optional 326-byte buffer that defaults to zeroes. It
contains no captured DPAPI blob, credential, private key, certificate,
fingerprint template, or proprietary Windows binary bytes.

| # | Original commit | Rebased commit | Category | Decision | Subject | Reason |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | `d591cff340673695f16c0fb853d8d342cf15e08f` | `85a70d500576772847d8ef94b24603dd22d887ae` | Desktop | Retained | feat(verimark): add Kensington VeriMark DT driver (047d:00f2) | Retained; driver source preserved, while conflicting legacy Meson wiring is restored by the separate cleanup commit. |
| 2 | `8a1bac267f06bb6402fb82f75a4c38c95d7b2570` | `da7b2c02052fa6025641f64c447b1b9b63fc3887` | Desktop | Retained | feat(verimark): wire all 8 vfuncs (list/delete/verify/identify/enroll) | Retained; driver source preserved, while conflicting legacy Meson wiring is restored by the separate cleanup commit. |
| 3 | `5f62a2374ecf8854236d8e11ae557c1abd8ab41d` | `04cb13ea5c05393c1dab9a4e8aa87577b8842960` | test | Retained | test(verimark): ship the standalone TDD test suite and meson.build | Retained; the standalone TDD suite is part of the reviewable driver source. |
| 4 | `94b766b494d91818d9ea2edfa179c62dfe45843e` | `3f04807025bd2b14ab267ef92189a8dbdd5af9f0` | Desktop | Retained | fix(verimark): close_notify on close + GError ownership cleanup | Retained; Desktop-specific integration or lifecycle behavior. |
| 5 | `b0950c1fc709f523cb70b7445a877768e236448a` | `e1270b22cf06559a8b80d2df341df1460fcaad97` | Desktop | Retained | fix(verimark): set non-NULL username/description on list() prints | Retained; Desktop-specific integration or lifecycle behavior. |
| 6 | `3e511e87eab81d922bb0e37541c00aec61fd853f` | `a2534064bbbc7da337c6aa26c51bc77ee65b8964` | Desktop | Retained | fix(verimark): backfill description + username on enroll-time FpPrint | Retained; Desktop-specific integration or lifecycle behavior. |
| 7 | `a987418f1647e755e1c1050ad434b3655effff93` | `ab52d2902fc3b2e351386ed2fcc95fb57e12645c` | Desktop | Retained | fix(verimark): set enroll_date on list() prints | Retained; Desktop-specific integration or lifecycle behavior. |
| 8 | `8fda1981b42488dc7b3058d9d75b2f3b9288f2b0` | `18a05ea2dbd84e1e2f07c524c27cdba93ea68384` | Desktop | Retained | fix(verimark): enroll uses the device-assigned storage_handle as tuid | Retained; Desktop-specific integration or lifecycle behavior. |
| 9 | `026e1d69288436bb0016e7fa48505ac5c303d9c5` | `5df0a10a22142960e72ac80354fbf69591fcbfe4` | obsolete | Retained | chore(verimark): bump verify exit logs to fp_info for journal visibility | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 10 | `4f649592a9def70c0889a403711df6b018e56817` | `fcea5d2458a85702ddf200a06b7e5c911b6436ae` | obsolete | Retained | chore(verimark): use fp_warn for verify diagnostic exits | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 11 | `1b639097f15b40c3580ebc0bab3b54e6dc0b9b15` | `5256aa8131f7aa63b9537c78fc2e197a0def237b` | Desktop | Retained | fix(verimark): drop close-side TLS close_notify, recover stale state at open() | Retained; Desktop-specific integration or lifecycle behavior. |
| 12 | `e86690953221720e5e66e6bb363655b6d4a46782` | `1faef0d531992e2fd9059da3d085677d4e43e174` | Desktop | Retained | fix(verimark): USB-level reset at open() to recover from stuck state | Retained; Desktop-specific integration or lifecycle behavior. |
| 13 | `d696c2ced3d170e75bd23d02b6ffd7ca37135999` | `b0e0fd1758dccff0a718c2a657dfd6f68c5da3d6` | Desktop | Retained | feat(verimark): 3-attempt verify retry loop with WARM-mode-on-retry | Retained; Desktop-specific integration or lifecycle behavior. |
| 14 | `45ad43f09a289fb01f15fccade2325521b69a1ca` | `f2ad579dfdd874460ef41f0e2384cf5a2786fba6` | Desktop | Retained | feat(verimark): factory-fresh pairing bootstrap — step 1 (pure builders) | Retained; driver source preserved, while conflicting legacy Meson wiring is restored by the separate cleanup commit. |
| 15 | `bd1293ae1570be9a20b0e9f2eddcc198674d5170` | `9b882386d527dafbf400c5998fe59d544e199bfe` | Desktop | Retained | feat(verimark): factory-fresh pairing bootstrap — step 2 (crypto+orchestrator+hook) | Retained; Desktop-specific integration or lifecycle behavior. |
| 16 | `b6bdd46e1e1fdb8afc0aa3b0e686594fc569d7a3` | `37dfe4efd26de5b1ac11ce66afef3cd25031edb7` | Desktop | Retained | fix(verimark): include glib/gstdio.h for g_chmod / g_rename | Retained; Desktop-specific integration or lifecycle behavior. |
| 17 | `27ca8629dbb449efa43d0ad5d6d155bb827965d3` | `5b413fd5f92673609f15c1ffe348dfd77a1a736b` | obsolete | Retained | chore(verimark): clean up logging for upstream review (Phase 10.4) | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 18 | `8bcfbf12d2691d0e63990504aff5cb59d7317adf` | `2381347a13f45044af176554a82d29e25da2ea7b` | shared | Retained | feat(verimark): Phase 10.3.a — async transport foundation | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 19 | `13d8a682e0f21a14b7018dfef609fda0ff9caa3d` | `75bd7d99cac8814769840d76d0009b43a6f17d30` | shared | Retained | feat(verimark): Phase 10.3.b — session.call_opcode async | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 20 | `2d7b46c69ed1b4d8c5fcb6c38c1076de6b7c5cc6` | `ca37314b682ef2abfa43b02d926be40b640b5cea` | shared | Retained | fix(verimark): Phase 10.3.a async block was inside the wrong #ifdef branch | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 21 | `84a80c72489ac1e9fef9e34a4a7d04b5bda334f3` | `4ce0822a6adc8be6a8eaa3c4bda4e3d05f417468` | shared | Retained | feat(verimark): Phase 10.3.c — async handshake | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 22 | `336e3024f44edcddbae69ae6010f26e27460c05e` | `ceeb62efb91cb5cd4b081034043c9596ecd642a4` | Desktop | Retained | feat(verimark): Phase 10.3.d — verify/identify async SSM | Retained; Desktop-specific integration or lifecycle behavior. |
| 23 | `c20053bea3cf7af63e364957290eb0af87482ce9` | `06a9c6f9dcae8cd0b2c1cf6af6e4febbc889fe5d` | Desktop | Retained | feat(verimark): Phase 10.3.e — async enroll SSM | Retained; Desktop-specific integration or lifecycle behavior. |
| 24 | `031fe66e2872e1093972bd5318d112cf0e5838fa` | `b68d6099a8328fe77669957389cda7ee8249e79f` | shared | Retained | feat(verimark): Phase 10.3.f — cancellation polish (dev_class->cancel hook) | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 25 | `7cfe5a9668854873f8241aaa2ec84a399083b4cb` | `568b4c61d5ffab20d488aceed024b5644646318d` | Desktop | Retained | feat(verimark): Phase 10.3.g — async open() handshake wiring | Retained; Desktop-specific integration or lifecycle behavior. |
| 26 | `865b0c066e08a31ed7065df82cf354f7d4691cad` | `0f8a8484a22a561d888f3d7770476b11f3355efa` | shared | Retained | verimark: sanitize source comments for upstream submission | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 27 | `91ae5c5e0987b50b9fdb4fbf68a4153d76904f5d` | `6792a166f39039abc76400e5299ca4183da5ae61` | shared | Retained | verimark: defer verify/identify complete to avoid pam_fprintd race | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 28 | `a048ce5fe5eedcfc2186fdb52d0acd31ee00d66b` | `715f61b2adc31b2575736bd5ee6f9c0c800defd0` | shared | Retained | verimark: make probe() return a stable device_id | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 29 | `411ea8c59f212df655efbbbdc8448e606c8f1ca9` | `42f30c943a72d67ca7a36e0b2a0955db8b93e2ab` | IT | Retained | verimark: recognize the IT (047d:8054) at probe time (POC step 1) | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 30 | `c0954feee3922eeca9829b8ebf1de11eefcc9a95` | `b8fae63d2afe16528f697b91ce0c7cba518648a4` | IT | Retained | verimark: bootstrap the IT port (047d:8054) — BULK transport + constants | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 31 | `1398f5da19d0a55c0578d161604ba22c45583b05` | `75dbb198ee653225f70157eed1aea5af3ad1773d` | IT | Retained | verimark: high-level IT session reset helper (close_notify recovery) | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 32 | `10ae1bb7301480e13f34ebcc426c956644a5edc3` | `436d3bf7f5bfb4db1ef9cdbf21c0ddfc445317e9` | IT | Retained | verimark: IT-specific ClientHello builder (5 ciphers, no 0x00a9) | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 33 | `eca92e5bbfeb44386d295616318b5974240a7204` | `a00cecb39e59efeb899d25af02f1c5b2157834ca` | IT | Retained | verimark: handshake orchestrator becomes IT-aware (is_it_variant flag) | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 34 | `47b5faa4b0477a4cd499840d461a2588ad7e2060` | `033b489639a76f4f9ceed3980cdc8e7f36a9f1e3` | IT | Retained | verimark: wire the IT path inside open() — full Tudor TLS session | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 35 | `e47961add0225ee37579d94445a56e4722c1665d` | `21e11652532b8c242875900243b3f0e5d4a46268` | IT | Retained | verimark: BULK async transceive for the IT handshake | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 36 | `320720c2de5106f18049ea6505bcf3c76494fa8f` | `d3778afa59e05b44ff4a66178383fde1fc22f79c` | IT | Retained | verimark: auto-route transceive_async to BULK on the IT (047d:8054) | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 37 | `0c19192da70c2b70c70e1c6170295733389a7e0b` | `29c111fca688bf409cef05d54c3f1785c272e0d0` | IT | Retained | verimark: fix GTask leak when auto-routing IT calls to BULK | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 38 | `25d4ce235900b42a298eaf60719b70e354e05a60` | `4c9829a521cc0ff74f9bc78bf3529b6da8b248ac` | IT | Retained | verimark: accept 0x96 02 add_image status 0x8006 as IT-side complete signal | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 39 | `cbd0a12bc0e994ec025ef41ebbf8b771a57576fc` | `b98bf58c4eb6b82fb92f63605838d9238da823b1` | IT | Retained | verimark: skip 0x96 03 commit on the IT (firmware auto-commits via 0x8006) | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 40 | `bf1001c60a52ffddd59f192e224c03e1f51ca749` | `bfb16b2638e5b99af0fb191859a729542cfdaf4f` | obsolete | Retained | verimark: log the 0x99 match no-match response shape at info level | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 41 | `1bd9b94de7350e7e3f5581d58122c5873c8880bd` | `deed6c5bba0ff4c45178fa8d9f9e26a38dd8cb7d` | obsolete | Retained | verimark: temporarily log 0x99 no-match at WARN level for IT diagnose | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 42 | `b09440c7e3ed6748653ca2eb09cf1ecd267eb10b` | `79c3214871e6e538e1f4ed9e472c25e0cf861aa1` | obsolete | Retained | verimark: log all vfy_cb_match branches at WARN level for IT diagnose | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 43 | `9e5f1636ca00cc1f0fa24e1f370e0bad497e99d7` | `3f103d6a14a52a0cdf6c84331d5c9ef86135a506` | IT | Retained | verimark: set enroll-date + IT-aware description on enroll success | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 44 | `87cd7ad675b4d406321678c46336a2aa513f282f` | `47adc57f7baacd5d7d3ac3182d19ce024bda65f2` | obsolete | Retained | verimark: log VFY_S_AFTER_POLL and VFY_S_MATCH transitions for IT diagnose | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 45 | `3550a8ccca0e0f8c006f5b5b99955eb3d53001f6` | `0374638f070c493eda9ee4f24332b8b11f995359` | obsolete | Retained | verimark: log pre/post getlist counts at ENR_S_RESOLVE_TUID for IT diagnose | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 46 | `3e9e8348ef45d42e8b5151abd0d95cb11771a893` | `e3ca87500388123f1fc99969d38d52721c7072bb` | obsolete | Retained | verimark: send 0x96 03 commit on the IT with minimal 1-byte payload | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 47 | `b94e23e1a07683486e7c3d6b9721f35d58b1abf1` | `e9585895a34bebb773a7a5b01eb5b8860547103e` | obsolete | Retained | verimark: try 17-byte 0x96 03 commit on IT (sub-cmd + TUID, no SID) | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 48 | `023197623029432559dd6b606661ded0c18cba4d` | `b9c57820c93f814ea802653bf035fa9fbe10aa2c` | obsolete | Retained | verimark: try 35-byte 0x96 03 commit on IT (DT prefix shape, no SID) | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 49 | `aec2dc28542c76f41a6cae4293d35e142edea5c5` | `6c991a46b12330a92460f42050d2b9519d48da3c` | obsolete | Retained | verimark: send IT 0x96 03 commit with sub-cmd as u32 LE per DLL RE | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 50 | `3f304bbe33378eb86f77d2b482ad76dc2e065e22` | `ff1d15ed3b51fac38d77b63ee68a0e07f7cb16f7` | obsolete | Retained | verimark: try 28-byte IT 0x96 03 commit (sub-cmd + length + TUID) | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 51 | `5dce9e64710ddc174a911a87e3219007975ea96f` | `6bd8f98ff61261d6a059aae7785ccb0c4a0cd94f` | IT | Retained | verimark: IT 0x96 03 commit builds the full 443-byte record (Windows-decoded) | Retained; documented layout uses a synthetic SID and a zero-filled optional blob, with no captured DPAPI or credential bytes. |
| 52 | `f50712f2cfb0a3b7d2dd6aa1058728ecd712e279` | `cfc5476c3ab86fe062f0c0514e743f366b78419c` | IT | Retained | verimark: cleanup IT diagnostic logs + decline delete-IT cleanly | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 53 | `c1e52018f3f98a63d811c166f02f34aff0d868f3` | `05a02b5a7da19714b31e58a0b20c8e5b27adf596` | obsolete | Retained | verimark: implement IT delete via 0xA4 with ANSI-381 sub-factor selector | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 54 | `ecbd94f7c60f02558d337a6e9571663004211c5d` | `02d2e5db0b2a89f737a2ce249166b73404338dd0` | shared | Retained | verimark: fix double-free in delete/list vfuncs (use g_steal_pointer) | Retained; shared Tudor protocol, session, transport, or runtime behavior. |
| 55 | `b1dc557697d1228631d9b0db3a7bb3b143bfdd5d` | `359bff01c65aaf672771240bb49ee87ef9535ded` | obsolete | Retained | verimark: pad IT 0xA4 delete payload to standard 12-byte Synaptics framing | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 56 | `6508ad9bbd9b43842fc071aa2330af2cfd5f89b9` | `18410030a2d27f7b641b5925bf72a2b13e01f31b` | obsolete | Retained | verimark: revert IT 0xA4 to 1-byte payload + add granular failure logging | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 57 | `c08ad24b8ecceaa4016cae1eec42ad9c7724073a` | `2c37a35dfddd4b488451be8f20a873f0b427d1ea` | obsolete | Retained | verimark: drive IT delete 0xA4 over BULK directly (sync vtable was CONTROL-only) | Retained for authored provenance; a later patch in the ordered series supersedes this diagnostic or protocol experiment. |
| 58 | `a90b1d5ac21ecc4f0c633c9be7b14f0182b2373c` | `860c025d3fe074cc8ccfd9dd26852cfc36f57f8e` | IT | Retained | verimark: fix IT list (0x9f) + delete (0xA3) via async-over-sync wrapper | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 59 | `e4c7b7ce158cc981c37110012f2a2ae0ccd070ef` | `bdb8643e89489e874dbd8e6c00963e622639f274` | IT | Retained | verimark: trigger 0xA4 GC after IT 0xA3 delete to wipe ghost templates | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 60 | `b888e9f3e741335eae8c66ef2910333ecb9b99b5` | `cb3167c15306b143a315ba349abadf848a50103d` | IT | Retained | verimark: use 0xA4 01 cleanup (not 80/81 config) for IT post-delete GC | Retained; IT-specific probe, bulk transport, protocol, or lifecycle behavior. |
| 61 | `66591aae03856bcefa7d7b4c0f08ea630f64b623` | `759c767920d61a3567c3a8386bf4f11b2e96e09b` | Desktop | Retained | verimark: trigger 0xA4 01 cleanup GC after DT 0xA3 delete (symmetry with IT) | Retained; Desktop-specific integration or lifecycle behavior. |

## Totals

- Shared: 9 retained, 0 dropped.
- Desktop: 17 retained, 0 dropped.
- IT: 17 retained, 0 dropped.
- Test: 1 retained, 0 dropped.
- Obsolete: 17 retained for provenance, 0 dropped.
- Cleanup: one new Tomasz Tracz commit, not counted among the 61 inherited commits.
