from __future__ import annotations

import math
import struct
from typing import Any, Dict, List, Tuple

from convert_keyence_files.models import KeyenceFile

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


INVALID_HEIGHT = 0xFFFFFFFF


def parse_string_data(data, offset):
    # type: (bytes, int) -> Tuple[str, str]
    pos = offset
    if len(data) < pos + 4:
        raise ValueError("VK4 file truncated: string data at offset %d" % pos)
    title_len = struct.unpack_from("<I", data, pos)[0]
    pos += 4
    if title_len == 0:
        title = ""
    else:
        byte_len = title_len * 2
        if len(data) < pos + byte_len:
            raise ValueError("VK4 file truncated: title string data")
        title = data[pos:pos + byte_len].decode("utf-16-le")
        pos += byte_len
    if len(data) < pos + 4:
        raise ValueError("VK4 file truncated: lens name string data")
    lens_len = struct.unpack_from("<I", data, pos)[0]
    pos += 4
    if lens_len == 0:
        lens_name = ""
    else:
        byte_len = lens_len * 2
        if len(data) < pos + byte_len:
            raise ValueError("VK4 file truncated: lens name string data")
        lens_name = data[pos:pos + byte_len].decode("utf-16-le")
        pos += byte_len
    return title, lens_name


def parse_vk4(data, source_format="vk4"):
    # type: (bytes, str) -> KeyenceFile
    parse_vk4_header(data, 0)
    offsets = parse_offset_table(data, HEADER_SIZE)
    metadata = {}  # type: Dict[str, Any]
    if offsets["setting"] != 0:
        metadata = parse_measurement_conditions(data, offsets["setting"])
    height_offset = offsets["height"][0]
    height = None  # type: Any
    if height_offset != 0:
        result = parse_false_color_image(data, height_offset)
        if result is not None:
            w, h, bit_depth, raw = result
            z_per_digit = metadata.get("z_length_per_digit_pm", 1)
            height = _convert_height(raw, w, h, z_per_digit)
    if height is None:
        raise ValueError("VK4 file has no height data")
    optical = None  # type: Any
    optical_offset = offsets["color_light"]
    if optical_offset != 0:
        result = parse_true_color_image(data, optical_offset)
        if result is not None:
            w, h, raw = result
            optical = _convert_optical(raw, w, h)
    laser = None  # type: Any
    laser_offset = offsets["light"][0]
    if laser_offset != 0:
        result = parse_false_color_image(data, laser_offset)
        if result is not None:
            w, h, bit_depth, raw = result
            laser = _convert_laser(raw, w, h, bit_depth)
    string_offset = offsets["string_data"]
    if string_offset != 0:
        title, lens_name = parse_string_data(data, string_offset)
        metadata["title"] = title
        metadata["lens_name"] = lens_name
    return KeyenceFile(
        height=height, optical=optical, laser=laser,
        metadata=metadata, source_format=source_format,
    )


def _convert_height(raw, width, height, z_length_per_digit_pm):
    # type: (bytes, int, int, int) -> List[List[float]]
    scale = z_length_per_digit_pm * 1e-6
    nan = float("nan")
    result = []
    for row in range(height):
        row_data = []
        for col in range(width):
            idx = (row * width + col) * 4
            val = struct.unpack_from("<I", raw, idx)[0]
            if val == INVALID_HEIGHT:
                row_data.append(nan)
            else:
                row_data.append(val * scale)
        result.append(row_data)
    return result


def _convert_optical(raw, width, height):
    # type: (bytes, int, int) -> List[List[Tuple[int, int, int]]]
    result = []
    for row in range(height):
        row_data = []
        for col in range(width):
            idx = (row * width + col) * 3
            b, g, r = raw[idx], raw[idx + 1], raw[idx + 2]
            row_data.append((r, g, b))
        result.append(row_data)
    return result


def _convert_laser(raw, width, height, bit_depth):
    # type: (bytes, int, int, int) -> List[List[int]]
    bps = bit_depth // 8
    fmt = "<H" if bit_depth == 16 else "<B" if bit_depth == 8 else "<I"
    result = []
    for row in range(height):
        row_data = []
        for col in range(width):
            idx = (row * width + col) * bps
            val = struct.unpack_from(fmt, raw, idx)[0]
            row_data.append(val)
        result.append(row_data)
    return result
