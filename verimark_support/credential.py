from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import os
import stat
import struct

MAX_BLOB_SIZE = 1 << 20
REQUIRED_LENGTHS = {1: 400, 2: 32, 3: 400}


class CredentialError(ValueError):
    pass


@dataclass(frozen=True)
class ValidationReport:
    size: int
    sha256: str
    tags: tuple[tuple[int, int], ...]


def validate_blob(blob: bytes) -> ValidationReport:
    if not blob or len(blob) > MAX_BLOB_SIZE:
        raise CredentialError("credential size is outside the accepted range")
    offset = 0
    seen: set[int] = set()
    tags: list[tuple[int, int]] = []
    while offset < len(blob):
        if len(blob) - offset < 6:
            raise CredentialError("truncated TLV header")
        tag, length, reserved = struct.unpack_from("<HHH", blob, offset)
        if reserved != 0:
            raise CredentialError("non-zero TLV reserved field")
        offset += 6
        if length > len(blob) - offset:
            raise CredentialError("truncated TLV value")
        if tag in REQUIRED_LENGTHS:
            if tag in seen:
                raise CredentialError(f"duplicate required tag {tag}")
            if length != REQUIRED_LENGTHS[tag]:
                raise CredentialError(f"invalid length for required tag {tag}")
            seen.add(tag)
        tags.append((tag, length))
        offset += length
    missing = set(REQUIRED_LENGTHS) - seen
    if missing:
        raise CredentialError("missing required credential tags")
    return ValidationReport(len(blob), sha256(blob).hexdigest(), tuple(tags))


def validate_file(path: Path, require_secure_mode: bool = False) -> ValidationReport:
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise CredentialError("credential path must be a regular non-symlink file")
    if require_secure_mode and stat.S_IMODE(info.st_mode) != 0o600:
        raise CredentialError("credential mode must be exactly 0600")
    if info.st_size > MAX_BLOB_SIZE:
        raise CredentialError("credential file is too large")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    with os.fdopen(fd, "rb", closefd=True) as stream:
        opened = os.fstat(stream.fileno())
        if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
            raise CredentialError("credential changed while being opened")
        blob = stream.read(MAX_BLOB_SIZE + 1)
    return validate_blob(blob)
