import pytest

from transport.protocol import Frame, FrameParser, ProtocolError, crc16


def test_frame_round_trip_and_incremental_parser():
    frame = Frame(7, 2, b"hello")
    encoded = frame.encode()
    parser = FrameParser()
    assert parser.feed(encoded[:4]) == []
    assert parser.feed(encoded[4:]) == [frame]


def test_crc_rejects_tampering():
    encoded = bytearray(Frame(1, 1, b"x").encode())
    encoded[-3] ^= 1
    with pytest.raises(ProtocolError, match="CRC"):
        Frame.decode(bytes(encoded))
