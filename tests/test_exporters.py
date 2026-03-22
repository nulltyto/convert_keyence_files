import csv
import math
import os
import tempfile
import pytest
from convert_keyence_files.models import KeyenceFile
from convert_keyence_files.exporters import export_height_csv, export_optical, export_laser


def make_sample_kf():
    return KeyenceFile(
        height=[[1.5, 2.0, float("nan")], [3.0, 4.5, 5.0]],
        optical=[
            [(255, 0, 0), (0, 255, 0), (0, 0, 255)],
            [(128, 128, 128), (0, 0, 0), (255, 255, 255)],
        ],
        laser=[[100, 200, 300], [400, 500, 600]],
        metadata={"magnification": 50.0},
        source_format="vk4",
    )


def test_export_height_csv():
    kf = make_sample_kf()
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        path = f.name
    try:
        export_height_csv(kf, path)
        with open(path, "r") as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) == 2
        assert len(rows[0]) == 3
        assert float(rows[0][0]) == 1.5
        assert float(rows[0][1]) == 2.0
        assert rows[0][2].lower() == "nan"
        assert float(rows[1][0]) == 3.0
    finally:
        os.unlink(path)


def test_export_optical_png():
    kf = make_sample_kf()
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name
    try:
        export_optical(kf, path)
        from PIL import Image
        img = Image.open(path)
        assert img.size == (3, 2)
        assert img.mode == "RGB"
        assert img.getpixel((0, 0)) == (255, 0, 0)
    finally:
        os.unlink(path)


def test_export_laser_png():
    kf = make_sample_kf()
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name
    try:
        export_laser(kf, path)
        from PIL import Image
        img = Image.open(path)
        assert img.size == (3, 2)
        assert img.mode == "I;16"
        assert img.getpixel((0, 0)) == 100
    finally:
        os.unlink(path)


def test_export_optical_tiff():
    kf = make_sample_kf()
    with tempfile.NamedTemporaryFile(suffix=".tiff", delete=False) as f:
        path = f.name
    try:
        export_optical(kf, path)
        from PIL import Image
        img = Image.open(path)
        assert img.size == (3, 2)
        assert img.mode == "RGB"
    finally:
        os.unlink(path)


def test_export_optical_none_raises():
    kf = make_sample_kf()
    kf.optical = None
    with pytest.raises(ValueError, match="optical"):
        export_optical(kf, "out.png")


def test_export_laser_none_raises():
    kf = make_sample_kf()
    kf.laser = None
    with pytest.raises(ValueError, match="laser"):
        export_laser(kf, "out.png")
