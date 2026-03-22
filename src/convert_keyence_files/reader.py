from __future__ import annotations

import os

from convert_keyence_files.models import KeyenceFile
from convert_keyence_files.parsers.vk4 import VK4_MAGIC, parse_vk4
from convert_keyence_files.parsers.vk6 import parse_vk6

ZIP_MAGIC = b"PK\x03\x04"


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
        return parse_vk6(data, source_format=fmt)
