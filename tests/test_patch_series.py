from pathlib import Path
from email import policy
from email.parser import Parser
import hashlib
import os
import re
import shutil
import stat
import subprocess
import tempfile
import unittest


BASE_COMMIT = "c4654fdc85c25afdd9115bec2f95a44145ae3b94"
DRIVER_REF = "verimark-both-source-clean"
REPOSITORY = Path(__file__).resolve().parents[1]
DRIVER_WORKTREE = REPOSITORY / ".driver-worktrees" / "libfprint"
PATCH_ROOT = REPOSITORY / "patches" / "libfprint"
CURRENT = PATCH_ROOT / "current"
SERIES = CURRENT / "series"
EXPORTER = REPOSITORY / "tools" / "export-libfprint-patches"
MATERIALIZER = REPOSITORY / "tools" / "materialize-libfprint"
PATCH_NAME = re.compile(r"^[0-9]{4}-[a-z0-9][a-z0-9-]*\.patch$")
LICENSE_COMPATIBLE_PREFIXES = ("data/", "libfprint/", "tests/")
LICENSE_COMPATIBLE_FILES = {"meson.build"}
SCELLES_AUTHOR = "Sébastien Celles <s.celles@gmail.com>"
CLEANUP_AUTHOR = "Tomasz Tracz <t@t90.dev>"
PROHIBITED_RESIDUE = {
    "unreviewed bio-serial": re.compile(r"D84CD3B6708B0000", re.IGNORECASE),
    "credential extractor": re.compile(
        r"powershell|pwsh|\.ps1|extract_pairingdata", re.IGNORECASE
    ),
    "named Windows capture": re.compile(
        r"windows[^\n]{0,100}(?:pcap|sub1)|"
        r"(?:pcap|sub1)[^\n]{0,100}windows|"
        r"\b20\d{2}-\d{2}-\d{2}[^\n]{0,30}pcap|"
        r"fresh-pairing-bootstrap\.pcapng",
        re.IGNORECASE,
    ),
    "generic capture provenance": re.compile(
        r"\bmatik\s+captures?\b|"
        r"\bcdb\s+capture\b|"
        r"\bcaptures/|"
        r"\bprobe-run-\d{8}(?:\.[a-z0-9]+)?\b|"
        r"\breal\s+(?:runtime\s+)?captur(?:e|ed)\b|"
        r"\bcaptured\s+runtime\b",
        re.IGNORECASE,
    ),
    "capture-derived TUID": re.compile(
        r"\b(?:sample|test)\s+tuid\b[^\n]{0,100}\b(?:from|taken\s+from)\b"
        r"[^\n]{0,100}\bcaptur(?:e|ed)\b|"
        r"\bcaptur(?:e|ed)\b[^\n]{0,100}\b(?:sample|test)\s+tuid\b",
        re.IGNORECASE,
    ),
    "capture-derived opaque identifier": re.compile(
        r"0xd9\s*,\s*0x92\s*,\s*0xaa\s*,\s*0x60|"
        r"0x1f\s*,\s*0x80\s*,\s*0x8b\s*,\s*0x28|"
        r"0xb5\s*,\s*0x08\s*,\s*0x52\s*,\s*0x0a|"
        r"0xad\s*,\s*0x05\s*,\s*0x86\s*,\s*0x70|"
        r"0x77\s*,\s*0xd2\s*,\s*0x04\s*,\s*0x99|"
        r"0x64\s*,\s*0xe5\s*,\s*0x73\s*,\s*0x41|"
        r"0x89\s*,\s*0x03\s*,\s*0xce\s*,\s*0x97|"
        r"0xe7\s*,\s*0x92\s*,\s*0xe7\s*,\s*0xc5|"
        r"0x01\s*,\s*0xbf\s*,\s*0x69\s*,\s*0x2c|"
        r"0xad\s*,\s*0xea\s*,\s*0x42\s*,\s*0x74|"
        r"0x87\s*,\s*0x81\s*,\s*0xeb\s*,\s*0xa2",
        re.IGNORECASE,
    ),
    "absolute temporary harness path": re.compile(r"/tmp/"),
}
SYNTHETIC_FIXTURE_MARKERS = (
    "Synthetic TUID used only to exercise record layout and byte preservation.",
    "Synthetic 0x9f 01 response fixture for the documented layout",
    "Synthetic matched_tuid used to exercise request framing.",
)


def run(*arguments, cwd=REPOSITORY, env=None):
    return subprocess.run(
        arguments,
        cwd=cwd,
        capture_output=True,
        check=False,
        text=True,
        env=env,
    )


def run_checked(test_case, *arguments, cwd=REPOSITORY):
    result = run(*arguments, cwd=cwd)
    test_case.assertEqual(
        result.returncode,
        0,
        f"{' '.join(map(str, arguments))} failed:\n{result.stderr}",
    )
    return result.stdout


def read_series(directory=CURRENT):
    return (directory / "series").read_text().splitlines()


def generation_snapshot():
    target = os.readlink(CURRENT)
    directory = (PATCH_ROOT / target).resolve()
    files = {
        path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in directory.iterdir()
        if path.is_file() and not path.is_symlink()
    }
    return target, files


def clone_at(test_case, destination, revision):
    cloned = run(
        "git", "clone", "--shared", "--no-checkout",
        str(DRIVER_WORKTREE), str(destination),
    )
    test_case.assertEqual(cloned.returncode, 0, cloned.stderr)
    checked_out = run("git", "-C", str(destination), "checkout", "--detach", revision)
    test_case.assertEqual(checked_out.returncode, 0, checked_out.stderr)


def apply_series(test_case, checkout):
    clone_at(test_case, checkout, BASE_COMMIT)
    for name in read_series():
        applied = run(
            "git", "-C", str(checkout), "am", "--keep-cr",
            str((CURRENT / name).resolve()),
        )
        test_case.assertEqual(applied.returncode, 0, f"{name}: {applied.stderr}")


def read_text_tree(root):
    return "\n".join(
        path.read_text(errors="replace")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    )


class PatchSeriesTests(unittest.TestCase):
    def test_series_is_nonempty_ordered_and_unique(self):
        names = read_series()

        self.assertTrue(names)
        self.assertEqual(names, sorted(names))
        self.assertEqual(len(names), len(set(names)))

    def test_series_entries_are_plain_valid_regular_patch_files(self):
        for name in read_series():
            with self.subTest(name=name):
                self.assertRegex(name, PATCH_NAME)
                self.assertNotIn("/", name)
                self.assertNotIn("..", name)
                path = CURRENT / name
                self.assertTrue(path.is_file())
                self.assertFalse(path.is_symlink())

    def test_patch_generation_has_no_unlisted_patches(self):
        listed = set(read_series())
        exported = {path.name for path in CURRENT.glob("*.patch")}

        self.assertEqual(exported, listed)

    def test_current_generation_has_project_source_permissions(self):
        generation = CURRENT.resolve()

        self.assertEqual(stat.S_IMODE(generation.stat().st_mode), 0o755)
        for path in (generation / "series", *generation.glob("*.patch")):
            with self.subTest(path=path.name):
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o644)

    def test_patches_preserve_mail_authorship_and_license_compatible_targets(self):
        authors = []
        for name in read_series():
            with self.subTest(name=name):
                patch = (CURRENT / name).read_text()
                self.assertRegex(
                    patch,
                    r"(?m)^From [0-9a-f]{40} Mon Sep 17 00:00:00 2001$",
                )
                message = Parser(policy=policy.default).parsestr(patch)
                self.assertIsNotNone(message["From"])
                authors.append(str(message["From"]))
                self.assertRegex(patch, r"(?m)^Date: ")
                self.assertRegex(patch, r"(?m)^Subject: ")
                targets = re.findall(r"(?m)^diff --git a/(.+) b/(.+)$", patch)
                self.assertTrue(targets)
                for before, after in targets:
                    self.assertEqual(before, after)
                    self.assertTrue(
                        before in LICENSE_COMPATIBLE_FILES
                        or before.startswith(LICENSE_COMPATIBLE_PREFIXES),
                        before,
                    )

        self.assertEqual(
            authors,
            [SCELLES_AUTHOR] * 24
            + [CLEANUP_AUTHOR, SCELLES_AUTHOR]
            + [CLEANUP_AUTHOR] * 8,
        )

    def test_active_patches_exclude_prohibited_provenance_residue(self):
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory) / "libfprint"
            apply_series(self, checkout)
            patch_text = read_text_tree(
                checkout / "libfprint" / "drivers" / "verimark"
            )

        for description, pattern in PROHIBITED_RESIDUE.items():
            with self.subTest(description=description):
                self.assertIsNone(pattern.search(patch_text))

    def test_active_patch_series_registers_only_desktop_verimark_id(self):
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory) / "libfprint"
            apply_series(self, checkout)
            patch_text = read_text_tree(checkout / "libfprint")

        for marker in ("0x00f2",):
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), patch_text.lower())
        for marker in ("0x8054", "+usb:v047Dp8054*"):
            with self.subTest(marker=marker):
                self.assertNotIn(marker.lower(), patch_text.lower())

    def test_verimark_disables_generic_temperature_cutoff(self):
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory) / "libfprint"
            apply_series(self, checkout)
            source = read_text_tree(
                checkout / "libfprint" / "drivers" / "verimark"
            )

        self.assertIn("dev_class->temp_hot_seconds = -1;", source)

    def test_factory_beta_never_bootstraps_during_open(self):
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory) / "libfprint"
            apply_series(self, checkout)
            patch_text = read_text_tree(checkout / "libfprint" / "drivers" / "verimark")

        self.assertNotIn("VERIMARK_ALLOW_BOOTSTRAP", patch_text)
        self.assertNotIn(".allow_bootstrap", patch_text)
        self.assertNotIn("verimark_try_bootstrap", patch_text)

    def test_pairing_loader_enforces_secure_regular_files_and_strict_tlvs(self):
        patch_text = "\n".join((CURRENT / name).read_text() for name in read_series())

        self.assertIn("O_NOFOLLOW", patch_text)
        self.assertIn("st_mode & 07777", patch_text)
        self.assertIn("reserved != 0", patch_text)
        self.assertIn("got_tag1", patch_text)
        self.assertIn("off == blob_len", patch_text)

    def test_series_applies_as_mail_on_the_exact_base(self):
        self.assertTrue(DRIVER_WORKTREE.is_dir(), "driver checkout is required")
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory) / "libfprint"
            apply_series(self, checkout)

            count = len(read_series())
            resolved_base = run_checked(
                self, "git", "-C", str(checkout), "rev-parse", f"HEAD~{count}"
            ).strip()
            self.assertEqual(resolved_base, BASE_COMMIT)
            authors = run_checked(
                self,
                "git", "-C", str(checkout), "log", "--reverse",
                "--format=%an <%ae>",
                f"{BASE_COMMIT}..HEAD",
            ).splitlines()
            self.assertEqual(
                authors,
                [SCELLES_AUTHOR] * 24
                + [CLEANUP_AUTHOR, SCELLES_AUTHOR]
                + [CLEANUP_AUTHOR] * 8,
            )

    def test_materialized_driver_has_only_implemented_features_for_desktop_id(self):
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory) / "libfprint"
            apply_series(self, checkout)
            driver = checkout / "libfprint" / "drivers" / "verimark"
            source = (driver / "verimark.c").read_text()
            header = (driver / "proto.h").read_text()

            id_table = re.search(
                r"static const FpIdEntry id_table\[\] = \{(.*?)\n\};",
                source,
                re.DOTALL,
            )
            self.assertIsNotNone(id_table)
            self.assertEqual(
                re.findall(r"\.pid = (VERIMARK_PID(?:_[A-Z]+)?)", id_table.group(1)),
                ["VERIMARK_PID"],
            )
            self.assertRegex(header, r"(?m)^#define VERIMARK_PID\s+0x00F2\b")
            self.assertNotRegex(header, r"(?m)^#define VERIMARK_PID_IT\s+0x8054\b")

            features = re.search(
                r"dev_class->features\s*=\s*(.*?);", source, re.DOTALL
            )
            self.assertIsNotNone(features)
            self.assertEqual(
                set(re.findall(r"FP_DEVICE_FEATURE_[A-Z_]+", features.group(1))),
                {
                    "FP_DEVICE_FEATURE_IDENTIFY",
                    "FP_DEVICE_FEATURE_VERIFY",
                    "FP_DEVICE_FEATURE_STORAGE",
                    "FP_DEVICE_FEATURE_STORAGE_LIST",
                    "FP_DEVICE_FEATURE_STORAGE_DELETE",
                    "FP_DEVICE_FEATURE_CAPTURE",
                    "FP_DEVICE_FEATURE_DUPLICATES_CHECK",
                },
            )
            for callback in ("enroll", "identify", "verify", "list", "delete"):
                with self.subTest(callback=callback):
                    self.assertRegex(
                        source,
                        rf"dev_class->{callback}\s*=\s*verimark_{callback};",
                    )
            self.assertNotRegex(source, r"dev_class->capture\s*=")

    def test_materialized_source_excludes_prohibited_provenance_residue(self):
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory) / "libfprint"
            apply_series(self, checkout)
            driver_text = read_text_tree(
                checkout / "libfprint" / "drivers" / "verimark"
            )

        for description, pattern in PROHIBITED_RESIDUE.items():
            with self.subTest(description=description):
                self.assertIsNone(pattern.search(driver_text))

    def test_pkgbuild_applies_the_checked_series_in_order(self):
        package_build = (REPOSITORY / "packaging" / "arch" / "PKGBUILD").read_text()

        self.assertIn('done < "${patch_directory}/series"', package_build)
        self.assertIn('git am --keep-cr "${patch_directory}/${patch_name}"', package_build)
        for name in read_series():
            self.assertIn(name, package_build)

    def test_materializer_rejects_blank_duplicate_traversal_and_symlink_entries(self):
        cases = {
            "blank": (
                "0001-valid.patch\n\n0002-valid.patch\n",
                "blank patch-series entry",
                False,
            ),
            "duplicate": (
                "0001-valid.patch\n0001-valid.patch\n",
                "duplicate patch-series entry",
                False,
            ),
            "traversal": ("../outside.patch\n", "invalid patch-series entry", False),
            "symlink": ("0001-valid.patch\n", "regular non-symlink", True),
        }

        self.assertTrue(MATERIALIZER.is_file(), "materializer is required")
        for name, (series, message, symlink_patch) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                tools = root / "tools"
                generation = root / "patches" / "libfprint" / "generations" / "test"
                tools.mkdir()
                generation.mkdir(parents=True)
                shutil.copy2(MATERIALIZER, tools / MATERIALIZER.name)
                (generation / "series").write_text(series)
                for patch_name in ("0001-valid.patch", "0002-valid.patch"):
                    (generation / patch_name).write_text("fixture\n")
                if symlink_patch:
                    (generation / "0001-valid.patch").unlink()
                    (generation / "target.patch").write_text("fixture\n")
                    (generation / "0001-valid.patch").symlink_to("target.patch")
                current = generation.parents[1] / "current"
                current.symlink_to("generations/test")

                result = run(str(tools / MATERIALIZER.name), str(root / "output"), cwd=root)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assertFalse((root / "output").exists())

    def test_materializer_refuses_dirty_source(self):
        self.assertTrue(MATERIALIZER.is_file(), "materializer is required")
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory) / "libfprint"
            clone_at(self, checkout, BASE_COMMIT)
            (checkout / ".dirty").write_text("dirty\n")

            result = run(str(MATERIALIZER), str(checkout))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("source checkout is dirty", result.stderr)

    def test_materializer_refuses_mismatched_source_head(self):
        self.assertTrue(MATERIALIZER.is_file(), "materializer is required")
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory) / "libfprint"
            clone_at(self, checkout, BASE_COMMIT + "^")

            result = run(str(MATERIALIZER), str(checkout))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("source HEAD must be exactly", result.stderr)

    def test_exporter_refuses_a_dirty_checkout_without_replacing_series(self):
        self.assertTrue(DRIVER_WORKTREE.is_dir(), "driver checkout is required")
        self.assertEqual(
            run("git", "-C", str(DRIVER_WORKTREE), "status", "--porcelain").stdout,
            "",
        )
        previous = generation_snapshot()
        sentinel = DRIVER_WORKTREE / ".patch-series-test-dirty"
        sentinel.write_text("dirty\n")
        self.addCleanup(sentinel.unlink)

        result = run(str(EXPORTER), BASE_COMMIT, DRIVER_REF)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(generation_snapshot(), previous)

    def test_exporter_refuses_a_wrong_base_reference_without_replacing_series(self):
        previous = generation_snapshot()

        result = run(str(EXPORTER), "HEAD", DRIVER_REF)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(generation_snapshot(), previous)

    def test_exporter_atomically_switches_current_and_retains_previous_generation(self):
        self.assertTrue(EXPORTER.is_file(), "exporter is required")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tools = root / "tools"
            driver = root / ".driver-worktrees" / "libfprint"
            generations = root / "patches" / "libfprint" / "generations"
            old_generation = generations / "old"
            tools.mkdir(parents=True)
            old_generation.mkdir(parents=True)
            shutil.copy2(EXPORTER, tools / EXPORTER.name)
            clone_at(self, driver, BASE_COMMIT)
            run_checked(
                self, "git", "-C", str(driver), "switch", "-c", "export-test"
            )
            source = driver / "data" / "autosuspend.hwdb"
            source.write_text(source.read_text() + "\n# exporter fixture\n")
            run_checked(self, "git", "-C", str(driver), "add", str(source))
            run_checked(
                self,
                "git", "-C", str(driver),
                "-c", "user.name=Exporter Test",
                "-c", "user.email=exporter@example.invalid",
                "commit", "-m", "test: export fixture",
            )
            (old_generation / "series").write_text("0001-old.patch\n")
            (old_generation / "0001-old.patch").write_text("old generation\n")
            current = generations.parent / "current"
            current.symlink_to("generations/old")

            result = run(
                str(tools / EXPORTER.name), BASE_COMMIT, "export-test", cwd=root
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(current.is_symlink())
            self.assertNotEqual(os.readlink(current), "generations/old")
            published = (current.parent / os.readlink(current)).resolve()
            self.assertTrue((published / "series").is_file())
            self.assertEqual(stat.S_IMODE(published.stat().st_mode), 0o755)
            for patch_name in read_series(published):
                self.assertTrue((published / patch_name).is_file())
                self.assertEqual(
                    stat.S_IMODE((published / patch_name).stat().st_mode), 0o644
                )
            self.assertEqual(
                stat.S_IMODE((published / "series").stat().st_mode), 0o644
            )
            previous = current.parent / "previous"
            self.assertTrue(previous.is_symlink())
            self.assertEqual(os.readlink(previous), "generations/old")
            self.assertTrue(old_generation.is_dir())


if __name__ == "__main__":
    unittest.main()
