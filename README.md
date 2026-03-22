# convert-keyence-files

Convert Keyence .vk4, .vk6, and .vk7 microscope files to PNG, TIFF, and CSV.

## Install

```
pip install .
```

## CLI

```bash
# Convert a single file (outputs height CSV + optical/laser PNGs)
convert-keyence scan.vk7 -o output/

# Convert all Keyence files in a directory
convert-keyence scans/ -o output/

# Recursive
convert-keyence scans/ -o output/ --recursive

# Export only specific layers
convert-keyence scan.vk7 -o output/ --only height
convert-keyence scan.vk7 -o output/ --only optical,laser

# TIFF instead of PNG
convert-keyence scan.vk7 -o output/ --image-format tiff

# Preview what would be converted
convert-keyence scans/ -o output/ --dry-run
```

## Python API

```python
from convert_keyence_files import read, export_height_csv, export_optical, export_laser

kf = read("scan.vk7")

export_height_csv(kf, "height.csv")
export_optical(kf, "optical.png")
export_laser(kf, "laser.tiff")
```

The `KeyenceFile` object contains:

- `kf.height` — 2D list of floats (micrometers), `NaN` for invalid pixels
- `kf.optical` — 2D list of `(R, G, B)` tuples, or `None`
- `kf.laser` — 2D list of ints (16-bit intensity), or `None`
- `kf.metadata` — dict with magnification, pixel size, timestamp, etc.

## Supported Formats

| Format | Source |
|--------|--------|
| .vk4 | VK-X series (binary) |
| .vk6 | VK-X1000/X3000 series (ZIP container) |
| .vk7 | VK-X1000/X3000 series (ZIP container) |
