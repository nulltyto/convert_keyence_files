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
