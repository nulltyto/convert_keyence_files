from __future__ import annotations

import struct
from typing import Any, Dict, List, Tuple

VK4_MAGIC = b"VK4_"
HEADER_SIZE = 12
OFFSET_TABLE_SIZE = 72

OFFSET_TABLE_FIELDS = [
    "setting", "color_peak", "color_light",
    "light_0", "light_1", "light_2",
    "height_0", "height_1", "height_2",
    "color_peak_thumbnail", "color_thumbnail",
    "light_thumbnail", "height_thumbnail",
    "assemble", "line_measure", "line_thickness",
    "string_data", "reserved",
]


def parse_vk4_header(data, offset):
    # type: (bytes, int) -> Tuple[bytes, int, int]
    if len(data) < offset + HEADER_SIZE:
        raise ValueError("VK4 file truncated: too short for header")
    magic = data[offset:offset + 4]
    if magic != VK4_MAGIC:
        raise ValueError(
            "Not a VK4 file: expected magic bytes 'VK4_', got %r" % magic
        )
    dll_version, file_type = struct.unpack_from("<II", data, offset + 4)
    return magic, dll_version, file_type


def parse_offset_table(data, offset):
    # type: (bytes, int) -> Dict[str, Any]
    if len(data) < offset + OFFSET_TABLE_SIZE:
        raise ValueError("VK4 file truncated: too short for offset table")
    values = struct.unpack_from("<18I", data, offset)
    result = {}
    for i, name in enumerate(OFFSET_TABLE_FIELDS):
        result[name] = values[i]
    result["light"] = [result.pop("light_0"), result.pop("light_1"), result.pop("light_2")]
    result["height"] = [result.pop("height_0"), result.pop("height_1"), result.pop("height_2")]
    return result


FALSE_COLOR_HEADER_SIZE = 796  # 5*4 + 2*4 + 768
TRUE_COLOR_HEADER_SIZE = 20    # 5*4

MEASUREMENT_CONDITIONS_MIN_SIZE = 304

def parse_measurement_conditions(data, offset):
    # type: (bytes, int) -> Dict[str, Any]
    if len(data) < offset + MEASUREMENT_CONDITIONS_MIN_SIZE:
        raise ValueError(
            "VK4 file truncated: measurement conditions block too short "
            "(expected at least %d bytes at offset %d, got %d)"
            % (MEASUREMENT_CONDITIONS_MIN_SIZE, offset, len(data) - offset)
        )
    size = struct.unpack_from("<I", data, offset)[0]
    if size < MEASUREMENT_CONDITIONS_MIN_SIZE:
        raise ValueError(
            "VK4 measurement conditions: invalid size field %d" % size
        )
    year, month, day, hour, minute, second, diff_utc = struct.unpack_from(
        "<7I", data, offset + 4
    )
    lens_mag = struct.unpack_from("<I", data, offset + 96)[0]
    x_length_per_pixel, y_length_per_pixel, z_length_per_digit = struct.unpack_from(
        "<3I", data, offset + 148
    )
    return {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute, "second": second,
        "diff_utc_by_minutes": diff_utc,
        "magnification": lens_mag / 10.0,
        "x_length_per_pixel_pm": x_length_per_pixel,
        "y_length_per_pixel_pm": y_length_per_pixel,
        "z_length_per_digit_pm": z_length_per_digit,
    }


def parse_false_color_image(data, offset, allow_missing=False):
    # type: (bytes, int, bool) -> Any
    if offset == 0 and allow_missing:
        return None
    if len(data) < offset + FALSE_COLOR_HEADER_SIZE:
        raise ValueError(
            "VK4 file truncated: false-color image header at offset %d" % offset
        )
    width, height, bit_depth, compression, byte_size = struct.unpack_from(
        "<5I", data, offset
    )
    if bit_depth not in (8, 16, 32):
        raise ValueError("VK4 false-color image: unsupported bit depth %d" % bit_depth)
    palette_range_min, palette_range_max = struct.unpack_from("<2I", data, offset + 20)
    pixel_offset = offset + FALSE_COLOR_HEADER_SIZE
    expected_size = width * height * (bit_depth // 8)
    if byte_size != expected_size:
        raise ValueError(
            "VK4 false-color image: byte_size %d != expected %d"
            % (byte_size, expected_size)
        )
    if len(data) < pixel_offset + byte_size:
        raise ValueError(
            "VK4 file truncated: false-color pixel data at offset %d" % pixel_offset
        )
    raw_data = data[pixel_offset:pixel_offset + byte_size]
    return width, height, bit_depth, raw_data


def parse_true_color_image(data, offset, allow_missing=False):
    # type: (bytes, int, bool) -> Any
    if offset == 0 and allow_missing:
        return None
    if len(data) < offset + TRUE_COLOR_HEADER_SIZE:
        raise ValueError(
            "VK4 file truncated: true-color image header at offset %d" % offset
        )
    width, height, bit_depth, compression, byte_size = struct.unpack_from(
        "<5I", data, offset
    )
    if bit_depth != 24:
        raise ValueError("VK4 true-color image: expected bit depth 24, got %d" % bit_depth)
    pixel_offset = offset + TRUE_COLOR_HEADER_SIZE
    expected_size = width * height * 3
    if byte_size != expected_size:
        raise ValueError(
            "VK4 true-color image: byte_size %d != expected %d"
            % (byte_size, expected_size)
        )
    if len(data) < pixel_offset + byte_size:
        raise ValueError(
            "VK4 file truncated: true-color pixel data at offset %d" % pixel_offset
        )
    raw_data = data[pixel_offset:pixel_offset + byte_size]
    return width, height, raw_data
