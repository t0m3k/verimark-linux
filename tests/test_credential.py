import os
from pathlib import Path
import tempfile
import unittest

from verimark_support.credential import CredentialError, validate_blob, validate_file

from tests.fixtures import record, valid_blob


class ValidateBlobTests(unittest.TestCase):
    def test_valid_blob_returns_only_metadata(self):
        blob = valid_blob()
        report = validate_blob(blob)

        self.assertEqual(report.size, len(blob))
        self.assertEqual(
            report.tags, ((2, 32), (1, 400), (4, 420), (3, 400), (0, 0))
        )
        self.assertNotIn(bytes(range(32)).hex(), repr(report))

    def test_reordered_required_tags_are_accepted(self):
        report = validate_blob(valid_blob((3, 0, 1, 4, 2)))

        self.assertEqual(report.tags, ((3, 400), (0, 0), (1, 400), (4, 420), (2, 32)))

    def test_missing_required_tags_are_rejected(self):
        for missing_tag in (1, 2, 3):
            with self.subTest(missing_tag=missing_tag):
                order = tuple(tag for tag in (2, 1, 4, 3, 0) if tag != missing_tag)
                with self.assertRaisesRegex(CredentialError, "missing required credential tags"):
                    validate_blob(valid_blob(order))

    def test_duplicate_required_tag_is_rejected(self):
        blob = valid_blob() + record(1, bytes([0x11]) * 400)

        with self.assertRaisesRegex(CredentialError, "duplicate required tag 1"):
            validate_blob(blob)

    def test_invalid_required_lengths_are_rejected(self):
        values = {1: b"x" * 399, 2: b"y" * 31, 3: b"z" * 401}
        for tag, value in values.items():
            with self.subTest(tag=tag):
                blob = b"".join(
                    record(candidate, value if candidate == tag else {
                        0: b"", 1: b"a" * 400, 2: b"b" * 32,
                        3: b"c" * 400, 4: b"d" * 420,
                    }[candidate])
                    for candidate in (2, 1, 4, 3, 0)
                )
                with self.assertRaisesRegex(CredentialError, f"invalid length for required tag {tag}"):
                    validate_blob(blob)

    def test_truncated_header_is_rejected(self):
        with self.assertRaisesRegex(CredentialError, "truncated TLV header"):
            validate_blob(valid_blob() + b"\x00")

    def test_truncated_value_is_rejected(self):
        with self.assertRaisesRegex(CredentialError, "truncated TLV value"):
            validate_blob(valid_blob() + b"\x09\x00\x01\x00\x00\x00")

    def test_blob_larger_than_one_mebibyte_is_rejected(self):
        with self.assertRaisesRegex(CredentialError, "credential size is outside the accepted range"):
            validate_blob(b"x" * ((1 << 20) + 1))


class ValidateFileTests(unittest.TestCase):
    def test_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "credential.bin"
            target.write_bytes(valid_blob())
            link = root / "credential-link.bin"
            link.symlink_to(target)

            with self.assertRaisesRegex(CredentialError, "regular non-symlink"):
                validate_file(link)

    def test_insecure_mode_is_rejected_when_requested(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "credential.bin"
            path.write_bytes(valid_blob())
            os.chmod(path, 0o644)

            with self.assertRaisesRegex(CredentialError, "exactly 0600"):
                validate_file(path, require_secure_mode=True)
