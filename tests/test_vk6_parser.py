import io
import struct
import zipfile
import pytest
from tests.test_vk4_parser import build_complete_vk4
from convert_keyence_files.parsers.vk6 import parse_vk6


def make_vk6_zip(vk4_data, format_ext=".vk7"):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("Vk4File", vk4_data)
    return buf.getvalue(), format_ext


def test_parse_vk6_extracts_vk4():
    vk4_data = build_complete_vk4()
    zip_data, ext = make_vk6_zip(vk4_data, ".vk7")
    kf = parse_vk6(zip_data, source_format="vk7")
    assert kf.source_format == "vk7"
    assert kf.metadata["magnification"] == 50.0
    assert kf.optical is not None
    assert kf.laser is not None


def test_parse_vk6_missing_vk4file():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("SomeOtherEntry", b"data")
    with pytest.raises(ValueError, match="Vk4File"):
        parse_vk6(buf.getvalue(), source_format="vk6")
