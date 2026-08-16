import argparse
from pathlib import Path
import sys

from .credential import CredentialError, validate_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="verimark-credential")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("path", type=Path)
    validate_parser.add_argument("--require-secure-mode", action="store_true")
    arguments = parser.parse_args(argv)

    if arguments.command == "validate":
        try:
            report = validate_file(arguments.path, arguments.require_secure_mode)
        except (CredentialError, FileNotFoundError, PermissionError) as error:
            print(f"invalid: {error}", file=sys.stderr)
            return 2
        tags = ",".join(f"{tag}:{length}" for tag, length in report.tags)
        print(f"valid size={report.size} sha256={report.sha256} tags={tags}")
        return 0

    parser.error("unknown command")
    return 2
