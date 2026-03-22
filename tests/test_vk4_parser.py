import struct
import pytest
from convert_keyence_files.parsers.vk4 import parse_vk4_header, parse_offset_table

def make_vk4_header(file_type=0):
    """Build a minimal VK4 header (12 bytes)."""
    return b"VK4_" + struct.pack("<II", 0x00010200, file_type)

def make_offset_table(offsets=None):
    """Build an offset table (72 bytes = 18 x uint32 LE)."""
    if offsets is None:
        offsets = [0] * 18
    return struct.pack("<18I", *offsets)

def test_parse_header_valid():
    data = make_vk4_header(file_type=0)
    magic, dll_version, file_type = parse_vk4_header(data, 0)
    assert magic == b"VK4_"
    assert file_type == 0

def test_parse_header_bad_magic():
    data = b"XXXX" + b"\x00" * 8
    with pytest.raises(ValueError, match="VK4"):
        parse_vk4_header(data, 0)

def test_parse_offset_table():
    offsets_in = [100 * i for i in range(18)]
    data = make_offset_table(offsets_in)
    result = parse_offset_table(data, 0)
    assert result["setting"] == 0
    assert result["color_light"] == 200
    assert result["light"] == [300, 400, 500]
    assert result["height"] == [600, 700, 800]
    assert result["string_data"] == 1600
