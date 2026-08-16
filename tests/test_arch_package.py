import gzip
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import tempfile
import unittest

from tests.fixtures import valid_blob
from verimark_support.credential import CredentialError, validate_blob


PIN = "66591aae03856bcefa7d7b4c0f08ea630f64b623"
REPOSITORY = Path(__file__).resolve().parents[1]
PACKAGE_DIRECTORY = REPOSITORY / "packaging" / "arch"
SOURCE_CACHE = PACKAGE_DIRECTORY / "libfprint"
PACKAGE_METADATA = {".BUILDINFO", ".MTREE", ".PKGINFO"}
EXPECTED_DIRECTORIES = {
    PurePosixPath(path)
    for path in (
        "usr",
        "usr/include",
        "usr/include/libfprint-2",
        "usr/lib",
        "usr/lib/girepository-1.0",
        "usr/lib/pkgconfig",
        "usr/lib/udev",
        "usr/lib/udev/hwdb.d",
        "usr/lib/udev/rules.d",
        "usr/share",
        "usr/share/gir-1.0",
        "usr/share/gtk-doc",
        "usr/share/gtk-doc/html",
        "usr/share/gtk-doc/html/libfprint-2",
        "usr/share/metainfo",
    )
}
EXPECTED_REGULAR_FILES = {
    PurePosixPath(path)
    for path in (
        "usr/lib/girepository-1.0/FPrint-2.0.typelib",
        "usr/lib/libfprint-2.so.2.0.0",
        "usr/lib/pkgconfig/libfprint-2.pc",
        "usr/lib/udev/hwdb.d/60-autosuspend-libfprint-2.hwdb",
        "usr/lib/udev/rules.d/70-libfprint-2.rules",
        "usr/share/gir-1.0/FPrint-2.0.gir",
        "usr/share/metainfo/org.freedesktop.libfprint.metainfo.xml",
    )
}
EXPECTED_SYMLINKS = {
    PurePosixPath("usr/lib/libfprint-2.so"): "libfprint-2.so.2",
    PurePosixPath("usr/lib/libfprint-2.so.2"): "libfprint-2.so.2.0.0",
}
DOCUMENTATION_DIRECTORY = PurePosixPath("usr/share/gtk-doc/html/libfprint-2")
DOCUMENTATION_ASSETS = {
    "home.png",
    "left-insensitive.png",
    "left.png",
    "libfprint-2.devhelp2",
    "right-insensitive.png",
    "right.png",
    "style.css",
    "up-insensitive.png",
    "up.png",
}
FORBIDDEN_SUFFIXES = {
    ".dmp",
    ".key",
    ".p12",
    ".pcap",
    ".pcapng",
    ".pem",
    ".pfx",
    ".reg",
}


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


def build_package_fixture(directory, extra_path=None, extra_content=b"fixture"):
    payload = directory / "payload"
    files = {
        ".PKGINFO": (
            b"pkgname = libfprint-verimark\n"
            b"pkgbase = libfprint-verimark\n"
            b"pkgver = 1.94.10.r1.g66591aa-1\n"
            b"pkgdesc = Synthetic libfprint package for safety tests\n"
            b"arch = x86_64\n"
        ),
        "usr/include/libfprint-2/fprint.h": b"/* public header */\n",
        "usr/lib/girepository-1.0/FPrint-2.0.typelib": b"GIR fixture\n",
        "usr/lib/libfprint-2.so.2.0.0": b"\x7fELFfixture",
        "usr/lib/pkgconfig/libfprint-2.pc": b"Name: libfprint\n",
        "usr/lib/udev/hwdb.d/60-autosuspend-libfprint-2.hwdb": b"usb:v047D\n",
        "usr/lib/udev/rules.d/70-libfprint-2.rules": b"ACTION==\"add\"\n",
        "usr/share/gir-1.0/FPrint-2.0.gir": b"<repository/>\n",
        "usr/share/gtk-doc/html/libfprint-2/index.html": b"<html/>\n",
        "usr/share/metainfo/org.freedesktop.libfprint.metainfo.xml": (
            b"<component/>\n"
        ),
    }
    if extra_path is not None:
        files[extra_path] = extra_content
    for relative_path, content in files.items():
        destination = payload / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    (payload / "usr/lib/libfprint-2.so.2").symlink_to("libfprint-2.so.2.0.0")
    (payload / "usr/lib/libfprint-2.so").symlink_to("libfprint-2.so.2")
    package = directory / "libfprint-verimark-fixture.pkg.tar.zst"
    archive_members = [
        name for name in sorted(PACKAGE_METADATA) if (payload / name).exists()
    ]
    archive_members.append("usr")
    result = subprocess.run(
        ["bsdtar", "-caf", str(package), *archive_members],
        cwd=payload,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"could not build package fixture: {result.stderr}")
    return package


def assert_no_sensitive_content(test_case, path, content):
    if content.startswith(b"\x1f\x8b"):
        try:
            content = gzip.decompress(content)
        except OSError:
            test_case.fail(f"invalid gzip content in {path}")
    if b"PRIVATE KEY" in content.upper():
        test_case.fail(f"private-key marker in {path}")
    try:
        validate_blob(content)
    except CredentialError:
        pass
    else:
        test_case.fail(f"credential structure in {path}")


def assert_normal_libfprint_payload(test_case, package):
    pacman_entries = run_checked(
        test_case, "pacman", "-Qlp", str(package)
    ).splitlines()
    paths = []
    for entry in pacman_entries:
        _, installed_path = entry.split(None, 1)
        test_case.assertTrue(installed_path.startswith("/"), "invalid package path")
        paths.append(PurePosixPath(installed_path.lstrip("/")))

    archive_entries = run_checked(
        test_case, "bsdtar", "-tf", str(package)
    ).splitlines()
    archive_paths = {
        entry.removeprefix("./").rstrip("/")
        for entry in archive_entries
        if entry.removeprefix("./").rstrip("/") not in PACKAGE_METADATA
    }
    test_case.assertEqual(archive_paths, {str(path) for path in paths})

    for path in paths:
        lowered = str(path).lower()
        normalized = lowered.replace("_", "-")
        basename = path.name.lower()
        test_case.assertNotIn("sub1", lowered, f"forbidden path: {path}")
        test_case.assertNotIn("windows-driver", lowered, f"forbidden path: {path}")
        test_case.assertNotIn(
            "windows-extracted", lowered, f"forbidden path: {path}"
        )
        test_case.assertNotIn("credential", lowered, f"forbidden path: {path}")
        test_case.assertNotIn("private-key", normalized, f"forbidden path: {path}")
        test_case.assertFalse(
            basename == "core" or basename.startswith("core."),
            f"forbidden path: {path}",
        )
        test_case.assertNotIn(path.suffix.lower(), FORBIDDEN_SUFFIXES)

        expected = (
            path in EXPECTED_DIRECTORIES
            or path in EXPECTED_REGULAR_FILES
            or path in EXPECTED_SYMLINKS
            or (
                path.parent == PurePosixPath("usr/include/libfprint-2")
                and path.suffix == ".h"
                and (path.name == "fprint.h" or path.name.startswith("fp-"))
            )
            or (
                path.parent == DOCUMENTATION_DIRECTORY
                and (path.suffix == ".html" or path.name in DOCUMENTATION_ASSETS)
            )
        )
        test_case.assertTrue(expected, f"unexpected package path: {path}")

    with tempfile.TemporaryDirectory() as directory:
        result = subprocess.run(
            ["bsdtar", "-xf", str(package), "-C", directory],
            capture_output=True,
            text=True,
            check=False,
        )
        test_case.assertEqual(
            result.returncode, 0, f"could not extract package: {result.stderr}"
        )
        extracted = Path(directory)
        for path in paths:
            candidate = extracted / str(path)
            mode = candidate.lstat().st_mode
            if path in EXPECTED_DIRECTORIES:
                test_case.assertTrue(stat.S_ISDIR(mode), f"not a directory: {path}")
                continue
            if path in EXPECTED_SYMLINKS:
                test_case.assertTrue(stat.S_ISLNK(mode), f"not a symlink: {path}")
                test_case.assertEqual(os.readlink(candidate), EXPECTED_SYMLINKS[path])
                continue
            test_case.assertTrue(stat.S_ISREG(mode), f"not a regular file: {path}")
            content = candidate.read_bytes()
            if path == PurePosixPath("usr/lib/libfprint-2.so.2.0.0"):
                test_case.assertTrue(content.startswith(b"\x7fELF"), "library is not ELF")
                continue
            assert_no_sensitive_content(test_case, path, content)
        for metadata in sorted(PACKAGE_METADATA):
            candidate = extracted / metadata
            if not candidate.exists():
                continue
            test_case.assertTrue(
                stat.S_ISREG(candidate.lstat().st_mode),
                f"package metadata is not a regular file: {metadata}",
            )
            assert_no_sensitive_content(
                test_case, PurePosixPath(metadata), candidate.read_bytes()
            )


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

    def test_generated_metadata_pins_local_check_fix(self):
        patch_source = "fix-generated-data-checks.patch"

        self.assertIn(patch_source, self.info["source"])
        patch_index = self.info["source"].index(patch_source)
        self.assertRegex(self.info["b2sums"][patch_index], r"^[0-9a-f]{128}$")

    def test_package_plan_produces_one_replacement_archive(self):
        package_paths = run_checked(self, "makepkg", "--packagelist").splitlines()

        self.assertEqual(len(package_paths), 1)
        self.assertTrue(
            Path(package_paths[0]).name.startswith(
                "libfprint-verimark-1.94.10.r1.g66591aa-1-x86_64.pkg.tar."
            )
        )


@unittest.skipUnless(SOURCE_CACHE.is_dir(), "run makepkg --verifysource first")
class ResolvedSourceTests(unittest.TestCase):
    def test_verified_source_cache_resolves_the_reviewed_commit(self):
        origin = run_checked(
            self,
            "git",
            "-C",
            str(SOURCE_CACHE),
            "config",
            "--get",
            "remote.origin.url",
        ).strip()
        resolved = run_checked(
            self,
            "git",
            "-C",
            str(SOURCE_CACHE),
            "rev-parse",
            PIN + "^{commit}",
        ).strip()

        self.assertEqual(
            origin, "https://gitlab.freedesktop.org/s-celles/libfprint.git"
        )
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
        assert_normal_libfprint_payload(self, self.package)


class PackagePayloadSafetyTests(unittest.TestCase):
    def assert_fixture_rejected(self, relative_path, content=b"fixture"):
        with tempfile.TemporaryDirectory() as directory:
            package = build_package_fixture(
                Path(directory), relative_path, extra_content=content
            )

            with self.assertRaises(AssertionError) as rejection:
                assert_normal_libfprint_payload(self, package)

        return rejection.exception

    def test_controlled_normal_payload_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            package = build_package_fixture(Path(directory))

            assert_normal_libfprint_payload(self, package)

    def test_global_forbidden_names_and_extensions_are_rejected(self):
        forbidden_paths = (
            "usr/share/gtk-doc/html/libfprint-2/export.reg",
            "usr/share/gtk-doc/html/libfprint-2/sub1.bin",
            "usr/share/gtk-doc/html/libfprint-2/capture.pcap",
            "usr/share/gtk-doc/html/libfprint-2/capture.pcapng",
            "usr/share/gtk-doc/html/libfprint-2/crash.dmp",
            "usr/share/gtk-doc/html/libfprint-2/core",
            "usr/share/gtk-doc/html/libfprint-2/core.1234",
            "usr/share/gtk-doc/html/libfprint-2/windows-driver/readme.html",
            "usr/share/gtk-doc/html/libfprint-2/windows-extracted/readme.html",
        )

        for relative_path in forbidden_paths:
            with self.subTest(relative_path=relative_path):
                self.assert_fixture_rejected(relative_path)

    def test_generic_sensitive_names_are_rejected(self):
        for basename in ("credential.html", "private-key.html"):
            with self.subTest(basename=basename):
                self.assert_fixture_rejected(
                    "usr/share/gtk-doc/html/libfprint-2/" + basename
                )

    def test_unexpected_file_under_normal_prefix_is_rejected(self):
        self.assert_fixture_rejected(
            "usr/share/gtk-doc/html/libfprint-2/machine-state.bin"
        )

    def test_private_key_marker_is_rejected_without_echoing_bytes(self):
        marker = b"-----BEGIN PRIVATE KEY-----\nsecret fixture bytes\n"

        rejection = self.assert_fixture_rejected(
            "usr/share/gtk-doc/html/libfprint-2/diagnostics.html", marker
        )

        self.assertNotIn("secret fixture bytes", str(rejection))

    def test_private_key_marker_in_package_metadata_is_rejected(self):
        rejection = self.assert_fixture_rejected(
            ".BUILDINFO", b"-----BEGIN PRIVATE KEY-----\nmetadata secret\n"
        )

        self.assertNotIn("metadata secret", str(rejection))

    def test_credential_structure_is_rejected_without_echoing_bytes(self):
        credential = valid_blob()

        rejection = self.assert_fixture_rejected(
            "usr/share/gtk-doc/html/libfprint-2/diagnostics.html", credential
        )

        self.assertNotIn(credential[:16].hex(), str(rejection))


if __name__ == "__main__":
    unittest.main()
