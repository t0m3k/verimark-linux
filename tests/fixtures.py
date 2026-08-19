import struct


def record(tag: int, value: bytes) -> bytes:
    return struct.pack("<HHH", tag, len(value), 0) + value


def valid_blob(order: tuple[int, ...] = (2, 1, 4, 3, 0)) -> bytes:
    values = {
        0: b"",
        1: bytes([0x11]) * 400,
        2: bytes(range(32)),
        3: bytes([0x33]) * 400,
        4: bytes([0x44]) * 420,
    }
    return b"".join(record(tag, values[tag]) for tag in order)
