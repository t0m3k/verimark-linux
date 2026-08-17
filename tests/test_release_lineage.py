import fnmatch
import os
from pathlib import Path
import subprocess
import unittest


FORBIDDEN_PATHS = {
    "windows",
    "verimark_support/install.py",
    "tests/test_install.py",
    "docs/fingerprint-first-pam-design.md",
}
SENSITIVE_PATTERNS = (
    "sub1*.bin",
    "*.pcap",
    "*.pcapng",
    "*.reg",
    "hardware-local/",
    ".driver-worktrees/",
)
REPOSITORY = Path(__file__).resolve().parents[1]


class ReleaseLineageTests(unittest.TestCase):
    def test_forbidden_paths_are_absent(self):
        for path in FORBIDDEN_PATHS:
            with self.subTest(path=path):
                self.assertFalse(os.path.lexists(REPOSITORY / path))

    def test_sensitive_artifact_patterns_are_ignored(self):
        ignored_patterns = {
            line.strip()
            for line in (REPOSITORY / ".gitignore").read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }

        for pattern in SENSITIVE_PATTERNS:
            with self.subTest(pattern=pattern):
                self.assertIn(pattern, ignored_patterns)

    def test_sensitive_artifacts_are_not_tracked(self):
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=REPOSITORY,
            capture_output=True,
            check=True,
            text=True,
        )
        tracked_files = result.stdout.splitlines()

        for pattern in SENSITIVE_PATTERNS:
            with self.subTest(pattern=pattern):
                if pattern.endswith("/"):
                    matches = [path for path in tracked_files if path.startswith(pattern)]
                else:
                    matches = [
                        path for path in tracked_files if fnmatch.fnmatch(path, pattern)
                    ]
                self.assertEqual(matches, [], f"tracked sensitive artifacts: {matches}")
