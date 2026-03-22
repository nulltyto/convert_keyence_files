from __future__ import annotations

import csv
import struct

from PIL import Image

from convert_keyence_files.models import KeyenceFile


def export_height_csv(kf, path):
    # type: (KeyenceFile, str) -> None
    with open(str(path), "w", newline="") as f:
        writer = csv.writer(f)
        for row in kf.height:
            writer.writerow([repr(v) for v in row])


def export_optical(kf, path):
    # type: (KeyenceFile, str) -> None
    if kf.optical is None:
        raise ValueError("Cannot export optical image: no optical data in file")
    height = len(kf.optical)
    width = len(kf.optical[0])
    img = Image.new("RGB", (width, height))
    for y, row in enumerate(kf.optical):
        for x, pixel in enumerate(row):
            img.putpixel((x, y), pixel)
    img.save(str(path))


def export_laser(kf, path):
    # type: (KeyenceFile, str) -> None
    if kf.laser is None:
        raise ValueError("Cannot export laser image: no laser data in file")
    height = len(kf.laser)
    width = len(kf.laser[0])
    raw_bytes = b""
    for row in kf.laser:
        for val in row:
            raw_bytes += struct.pack("<H", val)
    img = Image.frombytes("I;16", (width, height), raw_bytes)
    img.save(str(path))
