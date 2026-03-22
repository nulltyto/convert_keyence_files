import io
import os
import struct
import tempfile
import zipfile
import pytest
from tests.test_vk4_parser import build_complete_vk4
from convert_keyence_files.reader import detect_format, read_file


def test_detect_format_vk4():
    data = b"VK4_" + b"\x00" * 8
    assert detect_format(data, "anything.vk4") == "vk4"


def test_detect_format_zip_vk7():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("Vk4File", b"dummy")
    assert detect_format(buf.getvalue(), "scan.vk7") == "vk7"


def test_detect_format_zip_vk6():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("Vk4File", b"dummy")
    assert detect_format(buf.getvalue(), "scan.vk6") == "vk6"


def test_detect_format_unknown():
    with pytest.raises(ValueError, match="Unrecognized"):
        detect_format(b"XXXX", "file.bin")


def test_read_file_vk4():
    data = build_complete_vk4()
    with tempfile.NamedTemporaryFile(suffix=".vk4", delete=False) as f:
        f.write(data)
        f.flush()
        path = f.name
    try:
        kf = read_file(path)
        assert kf.source_format == "vk4"
        assert kf.metadata["magnification"] == 50.0
    finally:
        os.unlink(path)


def test_read_file_vk7():
    vk4_data = build_complete_vk4()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("Vk4File", vk4_data)
    with tempfile.NamedTemporaryFile(suffix=".vk7", delete=False) as f:
        f.write(buf.getvalue())
        f.flush()
        path = f.name
    try:
        kf = read_file(path)
        assert kf.source_format == "vk7"
    finally:
        os.unlink(path)
