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
