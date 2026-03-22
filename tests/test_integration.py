import math
import os
import pytest

SAMPLE_VK7 = os.path.expanduser("~/Downloads/sample.vk7")

pytestmark = pytest.mark.skipif(
    not os.path.exists(SAMPLE_VK7),
    reason="Sample VK7 file not available at %s" % SAMPLE_VK7,
)


def test_read_real_vk7():
    from convert_keyence_files import read

    kf = read(SAMPLE_VK7)
    assert kf.source_format == "vk7"
    assert len(kf.height) > 0
    assert len(kf.height[0]) > 0
    has_valid = False
    for row in kf.height:
        for val in row:
            if not math.isnan(val):
                has_valid = True
                break
        if has_valid:
            break
    assert has_valid, "All height values are NaN — likely a parsing error"
    assert "magnification" in kf.metadata
    assert "x_length_per_pixel_pm" in kf.metadata
    assert kf.metadata["magnification"] > 0
    print("Height: %dx%d" % (len(kf.height), len(kf.height[0])))
    print("Optical: %s" % ("present" if kf.optical else "absent"))
    print("Laser: %s" % ("present" if kf.laser else "absent"))
    print("Metadata: %s" % kf.metadata)


def test_cli_real_vk7(tmp_path):
    """Test full CLI conversion with the real sample file."""
    from convert_keyence_files.cli import main
    import sys

    out = tmp_path / "output"
    out.mkdir()

    sys.argv = ["convert-keyence", SAMPLE_VK7, "-o", str(out)]
    main()

    csv_files = list(out.glob("*_height.csv"))
    assert len(csv_files) == 1, "Expected one height CSV, found: %s" % list(out.iterdir())

    with open(str(csv_files[0])) as f:
        lines = f.readlines()
    assert len(lines) > 0, "Height CSV is empty"
    vals = lines[0].strip().split(",")
    assert len(vals) > 0

    png_files = list(out.glob("*.png"))
    print("Output files: %s" % [f.name for f in out.iterdir()])
    print("CSV rows: %d, cols: %d" % (len(lines), len(vals)))
