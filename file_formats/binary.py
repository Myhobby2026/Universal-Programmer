"""Raw binary loading and saving with bounded, explicit file handling."""

from __future__ import annotations

from pathlib import Path
import zlib


def read_binary(path: str | Path, *, max_size: int = 512 * 1024 * 1024) -> bytes:
    source = Path(path)
    size = source.stat().st_size
    if size > max_size:
        raise ValueError(f"binary file is {size} bytes; limit is {max_size}")
    return source.read_bytes()


def write_binary(path: str | Path, data: bytes) -> None:
    Path(path).write_bytes(data)


def checksums(data: bytes) -> dict[str, str]:
    return {"size": str(len(data)), "crc32": f"{zlib.crc32(data) & 0xFFFFFFFF:08x}"}
