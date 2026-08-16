import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from verimark_support.cli import main

from tests.fixtures import valid_blob


class CredentialCliTests(unittest.TestCase):
    def test_repository_wrapper_displays_help(self):
        repository = Path(__file__).resolve().parents[1]

        result = subprocess.run(
            [sys.executable, "tools/verimark-credential", "--help"],
            cwd=repository,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("validate", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_valid_file_prints_redacted_metadata_and_returns_zero(self):
        blob = valid_blob()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "credential.bin"
            path.write_bytes(blob)
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = main(["validate", str(path)])

        self.assertEqual(result, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertRegex(
            stdout.getvalue(),
            r"^valid size=1282 sha256=[0-9a-f]{64} tags=2:32,1:400,4:420,3:400,0:0\n$",
        )
        self.assertNotIn(bytes(range(32)).hex(), stdout.getvalue())

    def test_invalid_file_prints_concise_redacted_error_and_returns_two(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "credential.bin"
            path.write_bytes(b"invalid")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = main(["validate", str(path)])

        self.assertEqual(result, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertRegex(stderr.getvalue(), r"^invalid: .+\n$")
        self.assertNotIn(bytes(range(32)).hex(), stderr.getvalue())
