from __future__ import annotations

import io
import zipfile

from convert_keyence_files.models import KeyenceFile
from convert_keyence_files.parsers.vk4 import parse_vk4


def parse_vk6(data, source_format="vk6"):
    # type: (bytes, str) -> KeyenceFile
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise ValueError("Not a valid VK6/VK7 file: not a ZIP archive")
    names = zf.namelist()
    if "Vk4File" not in names:
        raise ValueError(
            "Not a valid VK6/VK7 file: ZIP archive does not contain 'Vk4File' entry. "
            "Found: %s" % ", ".join(names)
        )
    vk4_data = zf.read("Vk4File")
    kf = parse_vk4(vk4_data, source_format=source_format)
    return kf
