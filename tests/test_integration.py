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
