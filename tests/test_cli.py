import io
import os
import struct
import sys
import tempfile
import zipfile
import pytest
from tests.test_vk4_parser import build_complete_vk4
from convert_keyence_files.cli import collect_input_files, build_output_path, main


def test_collect_input_files_single_file(tmp_path):
    f = tmp_path / "scan.vk4"
    f.write_bytes(b"data")
    files = collect_input_files([str(f)], recursive=False)
    assert files == [str(f)]


def test_collect_input_files_directory(tmp_path):
    (tmp_path / "a.vk4").write_bytes(b"data")
    (tmp_path / "b.vk7").write_bytes(b"data")
    (tmp_path / "c.txt").write_bytes(b"data")
    files = collect_input_files([str(tmp_path)], recursive=False)
    basenames = sorted(os.path.basename(f) for f in files)
    assert basenames == ["a.vk4", "b.vk7"]


def test_collect_input_files_recursive(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (tmp_path / "a.vk4").write_bytes(b"data")
    (sub / "b.vk6").write_bytes(b"data")
    files = collect_input_files([str(tmp_path)], recursive=True)
    assert len(files) == 2


def test_build_output_path_simple():
    result = build_output_path(
        "/data/scan.vk4", "/output", "height", ".csv", input_base=None,
    )
    assert result == os.path.join("/output", "scan_height.csv")


def test_build_output_path_recursive():
    result = build_output_path(
        "/data/sub/scan.vk4", "/output", "optical", ".png", input_base="/data",
    )
    assert result == os.path.join("/output", "sub_scan_optical.png")


def test_dry_run(tmp_path, capsys):
    vk4_data = build_complete_vk4()
    f = tmp_path / "scan.vk4"
    f.write_bytes(vk4_data)
    out = tmp_path / "output"
    out.mkdir()
    sys.argv = ["convert-keyence", str(f), "-o", str(out), "--dry-run"]
    main()
    captured = capsys.readouterr()
    assert "Would convert:" in captured.out
    assert "scan_height.csv" in captured.out
    assert "scan_optical.png" in captured.out
    assert "scan_laser.png" in captured.out
    assert len(list(out.iterdir())) == 0


def test_full_conversion(tmp_path):
    vk4_data = build_complete_vk4()
    f = tmp_path / "scan.vk4"
    f.write_bytes(vk4_data)
    out = tmp_path / "output"
    out.mkdir()
    sys.argv = ["convert-keyence", str(f), "-o", str(out)]
    main()
    assert (out / "scan_height.csv").exists()
    assert (out / "scan_optical.png").exists()
    assert (out / "scan_laser.png").exists()


def test_only_flag(tmp_path):
    vk4_data = build_complete_vk4()
    f = tmp_path / "scan.vk4"
    f.write_bytes(vk4_data)
    out = tmp_path / "output"
    out.mkdir()
    sys.argv = ["convert-keyence", str(f), "-o", str(out), "--only", "height"]
    main()
    assert (out / "scan_height.csv").exists()
    assert not (out / "scan_optical.png").exists()
    assert not (out / "scan_laser.png").exists()
