import struct
import pytest
from convert_keyence_files.parsers.vk4 import parse_vk4_header, parse_offset_table
from convert_keyence_files.parsers.vk4 import parse_measurement_conditions

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


def make_measurement_conditions():
    block = bytearray(304)
    struct.pack_into("<I", block, 0, 304)
    struct.pack_into("<7I", block, 4, 2022, 3, 15, 10, 30, 0, 0)
    struct.pack_into("<I", block, 96, 500)
    struct.pack_into("<I", block, 148, 1000)
    struct.pack_into("<I", block, 152, 1000)
    struct.pack_into("<I", block, 156, 100)
    return bytes(block)

def test_parse_measurement_conditions():
    data = make_measurement_conditions()
    meta = parse_measurement_conditions(data, 0)
    assert meta["year"] == 2022
    assert meta["month"] == 3
    assert meta["day"] == 15
    assert meta["magnification"] == 50.0
    assert meta["x_length_per_pixel_pm"] == 1000
    assert meta["y_length_per_pixel_pm"] == 1000
    assert meta["z_length_per_digit_pm"] == 100

def test_parse_measurement_conditions_truncated():
    data = bytes(100)
    with pytest.raises(ValueError, match="truncated"):
        parse_measurement_conditions(data, 0)
