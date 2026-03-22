from __future__ import annotations

import os
import struct

from convert_keyence_files.models import KeyenceFile
from convert_keyence_files.parsers.vk4 import VK4_MAGIC, parse_vk4
from convert_keyence_files.parsers.vk6 import parse_vk6

ZIP_MAGIC = b"PK\x03\x04"
VK7_MAGIC = b"VK7f"
VK6_MAGIC = b"VK6f"

# VK7/VK6 files with a prefixed BMP thumbnail have the layout:
#   4 bytes: "VK7f" or "VK6f" magic
#   3 bytes: unknown (width hint / padding)
#   N bytes: BMP thumbnail (BMP file size is a uint32-LE at BMP offset 2,
#             i.e. at absolute offset 9 in the file)
#   remaining: ZIP archive containing Vk4File etc.
_VK_THUMBNAIL_MAGIC = {VK7_MAGIC, VK6_MAGIC}
_VK_THUMBNAIL_HEADER = 7   # 4-byte magic + 3-byte prefix before BMP


def _strip_thumbnail_prefix(data):
    # type: (bytes, ) -> bytes
    """Return the ZIP payload from a VK7f/VK6f file that has a BMP thumbnail prefix."""
    if len(data) < _VK_THUMBNAIL_HEADER + 4:
        raise ValueError("VK7/VK6 thumbnail-prefixed file too short")
    # BMP file size is stored as uint32-LE at byte 2 of the BMP header,
    # which is at absolute offset _VK_THUMBNAIL_HEADER + 2 = 9.
    bmp_size = struct.unpack_from("<I", data, _VK_THUMBNAIL_HEADER + 2)[0]
    zip_start = _VK_THUMBNAIL_HEADER + bmp_size
    if len(data) < zip_start + 4:
        raise ValueError(
            "VK7/VK6 thumbnail-prefixed file: BMP size %d leaves no room for ZIP data"
            % bmp_size
        )
    if data[zip_start:zip_start + 4] != ZIP_MAGIC:
        raise ValueError(
            "VK7/VK6 thumbnail-prefixed file: expected ZIP magic after BMP thumbnail "
            "(at offset %d), got %r" % (zip_start, data[zip_start:zip_start + 4])
        )
    return data[zip_start:]


def detect_format(data, filename):
    # type: (bytes, str) -> str
    if len(data) >= 4 and data[:4] == VK4_MAGIC:
        return "vk4"
    if len(data) >= 4 and data[:4] == ZIP_MAGIC:
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".vk6":
            return "vk6"
        if ext == ".vk7":
            return "vk7"
        return "vk6"
    if len(data) >= 4 and data[:4] in _VK_THUMBNAIL_MAGIC:
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".vk7":
            return "vk7"
        return "vk6"
    raise ValueError(
        "Unrecognized file format: magic bytes %r do not match VK4 or ZIP"
        % (data[:4],)
    )


def read_file(path):
    # type: (str) -> KeyenceFile
    with open(str(path), "rb") as f:
        data = f.read()
    fmt = detect_format(data, str(path))
    if fmt == "vk4":
        return parse_vk4(data, source_format="vk4")
    else:
        # If the file starts with a VK7f/VK6f thumbnail prefix, strip it first
        # so that parse_vk6 receives a plain ZIP archive.
        if data[:4] in _VK_THUMBNAIL_MAGIC:
            data = _strip_thumbnail_prefix(data)
        return parse_vk6(data, source_format=fmt)
