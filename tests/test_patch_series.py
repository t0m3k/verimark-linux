from pathlib import Path
import re
import subprocess
import tempfile
import unittest


BASE_COMMIT = "66591aae03856bcefa7d7b4c0f08ea630f64b623"
REPOSITORY = Path(__file__).resolve().parents[1]
DRIVER_WORKTREE = REPOSITORY / ".driver-worktrees" / "libfprint"
PATCH_DIRECTORY = REPOSITORY / "patches" / "libfprint"
SERIES = PATCH_DIRECTORY / "series"
EXPORTER = REPOSITORY / "tools" / "export-libfprint-patches"
PATCH_NAME = re.compile(r"^[0-9]{4}-[a-z0-9][a-z0-9-]*\.patch$")
LICENSE_COMPATIBLE_PREFIXES = ("data/", "libfprint/", "tests/")


def run(*arguments, cwd=REPOSITORY):
    return subprocess.run(
        arguments,
        cwd=cwd,
        capture_output=True,
        check=False,
        text=True,
    )


def read_series():
    return SERIES.read_text().splitlines()


class PatchSeriesTests(unittest.TestCase):
    def test_series_is_nonempty_ordered_and_unique(self):
        names = read_series()

        self.assertTrue(names)
        self.assertEqual(names, sorted(names))
        self.assertEqual(len(names), len(set(names)))

    def test_series_entries_are_plain_valid_patch_filenames(self):
        for name in read_series():
            with self.subTest(name=name):
                self.assertRegex(name, PATCH_NAME)
                self.assertNotIn("/", name)
                self.assertNotIn("..", name)
                self.assertFalse((PATCH_DIRECTORY / name).is_symlink())

    def test_patch_directory_has_no_unlisted_patches(self):
        listed = set(read_series())
        exported = {path.name for path in PATCH_DIRECTORY.glob("*.patch")}

        self.assertEqual(exported, listed)

    def test_patches_have_mail_headers_and_license_compatible_targets(self):
        for name in read_series():
            with self.subTest(name=name):
                patch = (PATCH_DIRECTORY / name).read_text()
                self.assertRegex(patch, r"(?m)^From [0-9a-f]{40} Mon Sep 17 00:00:00 2001$")
                self.assertRegex(patch, r"(?m)^Subject: ")
                targets = re.findall(r"(?m)^diff --git a/(.+) b/(.+)$", patch)
                self.assertTrue(targets)
                for before, after in targets:
                    self.assertEqual(before, after)
                    self.assertTrue(
                        before.startswith(LICENSE_COMPATIBLE_PREFIXES), before
                    )

    def test_series_applies_cleanly_to_the_exact_base(self):
        self.assertTrue(DRIVER_WORKTREE.is_dir(), "driver checkout is required")
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory) / "libfprint"
            created = run(
                "git", "-C", str(DRIVER_WORKTREE), "worktree", "add", "--detach",
                str(checkout), BASE_COMMIT,
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            self.addCleanup(
                lambda: run(
                    "git", "-C", str(DRIVER_WORKTREE), "worktree", "remove", "--force",
                    str(checkout),
                )
            )
            resolved = run("git", "-C", str(checkout), "rev-parse", "HEAD").stdout.strip()
            self.assertEqual(resolved, BASE_COMMIT)
            for name in read_series():
                applied = run("git", "apply", "--index", str(PATCH_DIRECTORY / name), cwd=checkout)
                self.assertEqual(applied.returncode, 0, f"{name}: {applied.stderr}")

    def test_pkgbuild_applies_the_checked_series_in_order(self):
        package_build = (REPOSITORY / "packaging" / "arch" / "PKGBUILD").read_text()

        self.assertIn('done < "${srcdir}/series"', package_build)
        self.assertIn('git apply --index "${srcdir}/${patch_name}"', package_build)
        for name in read_series():
            self.assertIn(name, package_build)

    def test_exporter_refuses_a_dirty_checkout_without_replacing_series(self):
        self.assertTrue(DRIVER_WORKTREE.is_dir(), "driver checkout is required")
        self.assertEqual(run("git", "-C", str(DRIVER_WORKTREE), "status", "--porcelain").stdout, "")
        previous = SERIES.read_bytes()
        sentinel = DRIVER_WORKTREE / ".patch-series-test-dirty"
        sentinel.write_text("dirty\n")
        self.addCleanup(sentinel.unlink)

        result = run(str(EXPORTER), BASE_COMMIT, "verimark-factory-beta-driver")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(SERIES.read_bytes(), previous)

    def test_exporter_refuses_a_wrong_base_reference_without_replacing_series(self):
        previous = SERIES.read_bytes()

        result = run(str(EXPORTER), "HEAD", "verimark-factory-beta-driver")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(SERIES.read_bytes(), previous)


if __name__ == "__main__":
    unittest.main()
