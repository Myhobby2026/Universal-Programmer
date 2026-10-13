import pytest

from file_formats import IntelHexError, parse_intel_hex


def test_intel_hex_preserves_address_range_and_fill():
    image = parse_intel_hex(":020000040001F9\n:020010000102EB\n:00000001FF\n")
    assert image.start_address == 0x10010
    assert image.data == bytes([1, 2])


def test_intel_hex_rejects_bad_checksum():
    with pytest.raises(IntelHexError, match="checksum"):
        parse_intel_hex(":00000001FE\n")
