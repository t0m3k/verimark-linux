from pathlib import Path
from email import policy
from email.parser import Parser
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import unittest


BASE_COMMIT = "c4654fdc85c25afdd9115bec2f95a44145ae3b94"
DRIVER_REF = "verimark-both-rebased"
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

        self.assertIn(SCELLES_AUTHOR, authors)

    def test_active_patch_series_registers_both_verimark_ids(self):
        patch_text = "\n".join((CURRENT / name).read_text() for name in read_series())

        for marker in (
            "0x00f2",
            "0x8054",
            "+usb:v047Dp00F2*",
            "+usb:v047Dp8054*",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, patch_text)

    def test_series_applies_as_mail_on_the_exact_base(self):
        self.assertTrue(DRIVER_WORKTREE.is_dir(), "driver checkout is required")
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory) / "libfprint"
            clone_at(self, checkout, BASE_COMMIT)
            for name in read_series():
                applied = run(
                    "git", "-C", str(checkout), "am", "--keep-cr",
                    str((CURRENT / name).resolve()),
                )
                self.assertEqual(applied.returncode, 0, f"{name}: {applied.stderr}")

            count = len(read_series())
            resolved_base = run_checked(
                self, "git", "-C", str(checkout), "rev-parse", f"HEAD~{count}"
            ).strip()
            self.assertEqual(resolved_base, BASE_COMMIT)
            authors = run_checked(
                self,
                "git", "-C", str(checkout), "log", "--format=%an <%ae>",
                f"{BASE_COMMIT}..HEAD",
            ).splitlines()
            self.assertIn(SCELLES_AUTHOR, authors)

    def test_pkgbuild_applies_the_checked_series_in_order(self):
        package_build = (REPOSITORY / "packaging" / "arch" / "PKGBUILD").read_text()

        self.assertIn('done < "${srcdir}/series"', package_build)
        self.assertIn('git am --keep-cr "${srcdir}/${patch_name}"', package_build)
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
            for patch_name in read_series(published):
                self.assertTrue((published / patch_name).is_file())
            previous = current.parent / "previous"
            self.assertTrue(previous.is_symlink())
            self.assertEqual(os.readlink(previous), "generations/old")
            self.assertTrue(old_generation.is_dir())


if __name__ == "__main__":
    unittest.main()
