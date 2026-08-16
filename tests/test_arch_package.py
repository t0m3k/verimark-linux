import os
from pathlib import Path
import subprocess
import unittest


PIN = "66591aae03856bcefa7d7b4c0f08ea630f64b623"
REPOSITORY = Path(__file__).resolve().parents[1]
PACKAGE_DIRECTORY = REPOSITORY / "packaging" / "arch"
SOURCE_TREE = PACKAGE_DIRECTORY / "src" / "libfprint"


def run_command(*arguments):
    environment = os.environ.copy()
    environment["LC_ALL"] = "C"
    return subprocess.run(
        arguments,
        cwd=PACKAGE_DIRECTORY,
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )


def run_checked(test_case, *arguments):
    result = run_command(*arguments)
    test_case.assertEqual(
        result.returncode,
        0,
        f"{' '.join(arguments)} failed:\n{result.stderr}",
    )
    return result.stdout


def parse_srcinfo(output):
    info = {}
    for line in output.splitlines():
        if "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        info.setdefault(key, []).append(value)
    return info


def parse_pacman_info(output):
    info = {}
    current_key = None
    for line in output.splitlines():
        if ":" in line:
            key, value = (part.strip() for part in line.split(":", 1))
            current_key = key
            info[key] = value
        elif current_key and line.startswith(" "):
            info[current_key] += " " + line.strip()
    return info


def built_package():
    packages = sorted(
        path
        for path in PACKAGE_DIRECTORY.glob("libfprint-verimark-*.pkg.tar.*")
        if not path.name.endswith(".sig")
    )
    if not packages:
        raise unittest.SkipTest(
            "build the package artifact to exercise package inspection"
        )
    if len(packages) > 1:
        raise AssertionError(f"expected one package artifact, found {len(packages)}")
    return packages[0]


class GeneratedMetadataTests(unittest.TestCase):
    def setUp(self):
        self.info = parse_srcinfo(run_checked(self, "makepkg", "--printsrcinfo"))

    def test_generated_metadata_exposes_replacement_package_contract(self):
        self.assertEqual(self.info["pkgbase"], ["libfprint-verimark"])
        self.assertEqual(self.info["pkgver"], ["1.94.10.r1.g66591aa"])
        self.assertEqual(self.info["conflicts"], ["libfprint"])
        self.assertCountEqual(
            self.info["provides"], ["libfprint", "libfprint-2.so"]
        )
        self.assertIn(
            "libfprint::git+https://gitlab.freedesktop.org/s-celles/"
            "libfprint.git#commit=" + PIN,
            self.info["source"],
        )
        for dependency in ("gnutls", "nettle", "gmp", "libgusb"):
            self.assertIn(dependency, self.info["depends"])
        self.assertFalse(
            any("sub1" in value.lower() for value in self.info.get("source", []))
        )

    def test_generated_version_is_stable_across_metadata_runs(self):
        repeated = parse_srcinfo(run_checked(self, "makepkg", "--printsrcinfo"))

        self.assertEqual(repeated["pkgver"], self.info["pkgver"])

    def test_package_plan_produces_one_replacement_archive(self):
        package_paths = run_checked(self, "makepkg", "--packagelist").splitlines()

        self.assertEqual(len(package_paths), 1)
        self.assertTrue(
            Path(package_paths[0]).name.startswith(
                "libfprint-verimark-1.94.10.r1.g66591aa-1-x86_64.pkg.tar."
            )
        )


@unittest.skipUnless(SOURCE_TREE.is_dir(), "run makepkg --verifysource first")
class ResolvedSourceTests(unittest.TestCase):
    def test_resolved_source_is_the_reviewed_commit(self):
        resolved = run_checked(
            self, "git", "-C", str(SOURCE_TREE), "rev-parse", "HEAD"
        ).strip()

        self.assertEqual(resolved, PIN)


class BuiltPackageTests(unittest.TestCase):
    def setUp(self):
        self.package = built_package()

    def test_package_archive_has_expected_name_and_version(self):
        identity = run_checked(self, "pacman", "-Qp", str(self.package)).strip()

        self.assertEqual(
            identity, "libfprint-verimark 1.94.10.r1.g66591aa-1"
        )

    def test_package_archive_provides_the_fprintd_abi_without_credentials(self):
        metadata = run_checked(self, "pacman", "-Qip", str(self.package))
        info = parse_pacman_info(metadata)

        self.assertIn("libfprint", info["Provides"].split())
        self.assertIn("libfprint-2.so=2-64", info["Provides"].split())
        self.assertIn("libfprint", info["Conflicts With"].split())
        self.assertNotIn("sub1", metadata.lower())

    def test_package_archive_contains_only_normal_libfprint_payload(self):
        entries = run_checked(self, "pacman", "-Qlp", str(self.package)).splitlines()
        lowered = [entry.lower() for entry in entries]

        self.assertTrue(any("/usr/lib/libfprint-2.so" in entry for entry in entries))
        self.assertTrue(any("/usr/include/libfprint-2/" in entry for entry in entries))
        self.assertTrue(any("/gir-1.0/" in entry for entry in entries))
        self.assertTrue(
            any("/udev/" in entry or "/hwdb.d/" in entry for entry in entries)
        )
        self.assertTrue(any("/share/doc/" in entry for entry in entries))
        self.assertTrue(any("/share/metainfo/" in entry for entry in entries))
        forbidden = ("sub1", "windows", ".pcap", ".pcapng", ".dmp", "core.")
        self.assertFalse(
            any(token in entry for entry in lowered for token in forbidden),
            "package contains a credential, Windows export, capture, or crash artifact",
        )


if __name__ == "__main__":
    unittest.main()
