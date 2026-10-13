"""Versioned, CRC-protected protocol shared by the desktop app and firmware."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import struct


MAGIC = b"UPS1"
PROTOCOL_VERSION = 1
MAX_PAYLOAD = 4096
HEADER = struct.Struct("<4sBHBBH")


class Command(IntEnum):
    PING = 1
    GET_INFO = 2
    CONFIGURE_GPIO = 3
    RESET = 4
    CAPTURE_START = 5
    CAPTURE_STOP = 6


class Status(IntEnum):
    REQUEST = 0
    OK = 1
    BAD_COMMAND = 2
    BAD_PAYLOAD = 3
    BUSY = 4
    NOT_SUPPORTED = 5
    IO_ERROR = 6
    CRC_ERROR = 7


class ProtocolError(ValueError):
    """Raised when a packet cannot be trusted or decoded."""


def crc16(data: bytes) -> int:
    """CRC-16/CCITT-FALSE, matching the Teensy implementation."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


@dataclass(frozen=True, slots=True)
class Frame:
    sequence: int
    command: int
    payload: bytes = b""
    status: int = Status.REQUEST
    version: int = PROTOCOL_VERSION

    def encode(self) -> bytes:
        if not 0 <= self.sequence <= 0xFFFF:
            raise ProtocolError("sequence must fit in an unsigned 16-bit integer")
        if not 0 <= self.command <= 0xFF or not 0 <= self.status <= 0xFF:
            raise ProtocolError("command and status must fit in an unsigned byte")
        if len(self.payload) > MAX_PAYLOAD:
            raise ProtocolError(f"payload exceeds {MAX_PAYLOAD} bytes")
        header = HEADER.pack(MAGIC, self.version, self.sequence, self.command, self.status, len(self.payload))
        return header + self.payload + struct.pack("<H", crc16(header + self.payload))

    @classmethod
    def decode(cls, packet: bytes) -> "Frame":
        if len(packet) < HEADER.size + 2:
            raise ProtocolError("packet is truncated")
        magic, version, sequence, command, status, length = HEADER.unpack_from(packet)
        if magic != MAGIC:
            raise ProtocolError("invalid packet magic")
        if version != PROTOCOL_VERSION:
            raise ProtocolError(f"unsupported protocol version {version}")
        if length > MAX_PAYLOAD or len(packet) != HEADER.size + length + 2:
            raise ProtocolError("invalid payload length")
        body = packet[:-2]
        expected = struct.unpack_from("<H", packet, len(packet) - 2)[0]
        if crc16(body) != expected:
            raise ProtocolError("CRC mismatch")
        return cls(sequence, command, packet[HEADER.size:HEADER.size + length], status, version)


class FrameParser:
    """Incremental parser that safely resynchronizes after noise or corruption."""

    def __init__(self, max_payload: int = MAX_PAYLOAD):
        self.max_payload = max_payload
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[Frame]:
        self._buffer.extend(data)
        frames: list[Frame] = []
        while True:
            start = self._buffer.find(MAGIC)
            if start < 0:
                self._buffer[:] = self._buffer[-(len(MAGIC) - 1):]
                break
            if start:
                del self._buffer[:start]
            if len(self._buffer) < HEADER.size:
                break
            try:
                length = HEADER.unpack_from(self._buffer)[5]
            except struct.error:
                break
            if length > self.max_payload:
                del self._buffer[:len(MAGIC)]
                continue
            total = HEADER.size + length + 2
            if len(self._buffer) < total:
                break
            packet = bytes(self._buffer[:total])
            del self._buffer[:total]
            try:
                frames.append(Frame.decode(packet))
            except ProtocolError:
                # Drop one byte and search again so a valid frame following a
                # damaged frame is still delivered.
                self._buffer[:0] = packet[1:]
        return frames
