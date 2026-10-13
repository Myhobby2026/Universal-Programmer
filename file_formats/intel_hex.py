"""Strict Intel HEX parser with sparse-address and fill-value policies."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class IntelHexError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class HexImage:
    data: bytes
    start_address: int
    end_address: int
    fill_value: int = 0xFF

    @property
    def size(self) -> int:
        return len(self.data)


def parse_intel_hex(text: str, *, fill_value: int = 0xFF) -> HexImage:
    if not 0 <= fill_value <= 255:
        raise IntelHexError("fill_value must be between 0 and 255")
    memory: dict[int, int] = {}
    base = 0
    eof = False
    start_linear: int | None = None
    for line_number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if not line.startswith(":") or len(line) < 11 or len(line[1:]) % 2:
            raise IntelHexError(f"line {line_number}: malformed record")
        try:
            record = bytes.fromhex(line[1:])
        except ValueError as exc:
            raise IntelHexError(f"line {line_number}: non-hex characters") from exc
        length, address, kind = record[0], int.from_bytes(record[1:3], "big"), record[3]
        if len(record) != length + 5:
            raise IntelHexError(f"line {line_number}: byte count does not match record length")
        if sum(record) & 0xFF:
            raise IntelHexError(f"line {line_number}: checksum mismatch")
        payload = record[4:4 + length]
        if kind == 0x00:
            absolute = base + address
            for offset, byte in enumerate(payload):
                location = absolute + offset
                if location in memory and memory[location] != byte:
                    raise IntelHexError(f"line {line_number}: overlapping data differs at 0x{location:X}")
                memory[location] = byte
        elif kind == 0x01:
            if length != 0 or address != 0:
                raise IntelHexError(f"line {line_number}: invalid EOF record")
            eof = True
        elif kind == 0x02:
            if length != 2:
                raise IntelHexError(f"line {line_number}: invalid segment-address record")
            base = int.from_bytes(payload, "big") << 4
        elif kind == 0x04:
            if length != 2:
                raise IntelHexError(f"line {line_number}: invalid linear-address record")
            base = int.from_bytes(payload, "big") << 16
        elif kind == 0x05:
            if length != 4:
                raise IntelHexError(f"line {line_number}: invalid start-address record")
            start_linear = int.from_bytes(payload, "big")
        else:
            raise IntelHexError(f"line {line_number}: unsupported record type 0x{kind:02X}")
    if not eof:
        raise IntelHexError("missing EOF record")
    if not memory:
        return HexImage(b"", 0, 0, fill_value)
    start, end = min(memory), max(memory) + 1
    image = bytes(memory.get(address, fill_value) for address in range(start, end))
    return HexImage(image, start, end, fill_value)


def read_intel_hex(path: str | Path, *, fill_value: int = 0xFF) -> HexImage:
    return parse_intel_hex(Path(path).read_text(encoding="ascii"), fill_value=fill_value)
