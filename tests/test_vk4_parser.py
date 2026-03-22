import math
import struct
import pytest
from convert_keyence_files.parsers.vk4 import parse_vk4_header, parse_offset_table
from convert_keyence_files.parsers.vk4 import parse_measurement_conditions
from convert_keyence_files.parsers.vk4 import (
    parse_false_color_image, parse_true_color_image
)
from convert_keyence_files.parsers.vk4 import parse_string_data, parse_vk4

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


def make_false_color_image(width, height, bit_depth, pixel_data):
    palette = b"\x00" * 768
    byte_size = len(pixel_data)
    header = struct.pack("<5I", width, height, bit_depth, 0, byte_size)
    range_fields = struct.pack("<2I", 0, 0)
    return header + range_fields + palette + pixel_data

def make_true_color_image(width, height, pixel_data):
    byte_size = len(pixel_data)
    header = struct.pack("<5I", width, height, 24, 0, byte_size)
    return header + pixel_data

def test_parse_false_color_image_height():
    pixels = struct.pack("<4I", 1000, 2000, 0xFFFFFFFF, 3000)
    data = make_false_color_image(2, 2, 32, pixels)
    width, height, bit_depth, raw_data = parse_false_color_image(data, 0)
    assert width == 2
    assert height == 2
    assert bit_depth == 32
    assert len(raw_data) == 16

def test_parse_false_color_image_laser():
    pixels = struct.pack("<4H", 100, 200, 300, 400)
    data = make_false_color_image(2, 2, 16, pixels)
    width, height, bit_depth, raw_data = parse_false_color_image(data, 0)
    assert width == 2
    assert height == 2
    assert bit_depth == 16
    assert len(raw_data) == 8

def test_parse_true_color_image():
    pixels = bytes([255, 0, 0, 0, 255, 0, 0, 0, 255, 128, 128, 128])
    data = make_true_color_image(2, 2, pixels)
    width, height, raw_data = parse_true_color_image(data, 0)
    assert width == 2
    assert height == 2
    assert len(raw_data) == 12

def test_parse_false_color_image_zero_offset():
    result = parse_false_color_image(b"", 0, allow_missing=True)
    assert result is None


def make_string_data(title, lens_name):
    title_encoded = title.encode("utf-16-le")
    lens_encoded = lens_name.encode("utf-16-le")
    return (
        struct.pack("<I", len(title)) + title_encoded
        + struct.pack("<I", len(lens_name)) + lens_encoded
    )

def test_parse_string_data():
    data = make_string_data("My Scan", "50x Lens")
    title, lens_name = parse_string_data(data, 0)
    assert title == "My Scan"
    assert lens_name == "50x Lens"

def test_parse_string_data_empty():
    data = struct.pack("<I", 0) + struct.pack("<I", 0)
    title, lens_name = parse_string_data(data, 0)
    assert title == ""
    assert lens_name == ""

def build_complete_vk4():
    """Build a minimal but complete VK4 file with all sections."""
    meas = bytearray(304)
    struct.pack_into("<I", meas, 0, 304)
    struct.pack_into("<7I", meas, 4, 2022, 3, 15, 10, 30, 0, 0)
    struct.pack_into("<I", meas, 96, 500)
    struct.pack_into("<I", meas, 148, 1000)
    struct.pack_into("<I", meas, 152, 1000)
    struct.pack_into("<I", meas, 156, 100)

    optical_pixels = bytes([0, 0, 255, 0, 255, 0, 255, 0, 0, 128, 128, 128])
    optical_header = struct.pack("<5I", 2, 2, 24, 0, len(optical_pixels))
    optical = optical_header + optical_pixels

    laser_pixels = struct.pack("<4H", 100, 200, 300, 400)
    laser = make_false_color_image(2, 2, 16, laser_pixels)

    height_pixels = struct.pack("<4I", 1000000, 2000000, 0xFFFFFFFF, 3000000)
    height = make_false_color_image(2, 2, 32, height_pixels)

    strings = make_string_data("Test Scan", "50x")

    meas_offset = 84
    optical_offset = meas_offset + 304
    laser_offset = optical_offset + len(optical)
    height_offset = laser_offset + len(laser)
    string_offset = height_offset + len(height)

    offsets = [0] * 18
    offsets[0] = meas_offset
    offsets[2] = optical_offset
    offsets[3] = laser_offset
    offsets[6] = height_offset
    offsets[16] = string_offset
    table = struct.pack("<18I", *offsets)

    header = b"VK4_" + struct.pack("<II", 0x00010200, 0)
    return header + table + bytes(meas) + optical + laser + height + strings

def test_parse_vk4_full():
    data = build_complete_vk4()
    kf = parse_vk4(data)
    assert kf.source_format == "vk4"
    assert len(kf.height) == 2
    assert len(kf.height[0]) == 2
    # First pixel: 1000000 * 100 * 1e-6 = 100.0 micrometers
    assert abs(kf.height[0][0] - 100.0) < 0.001
    # Invalid pixel should be NaN
    assert math.isnan(kf.height[1][0])
    # Optical should be RGB (converted from BGR)
    assert kf.optical is not None
    assert kf.optical[0][0] == (255, 0, 0)
    # Laser
    assert kf.laser is not None
    assert kf.laser[0][0] == 100
    # Metadata
    assert kf.metadata["magnification"] == 50.0
    assert kf.metadata["title"] == "Test Scan"
    assert kf.metadata["lens_name"] == "50x"
