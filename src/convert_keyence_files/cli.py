from __future__ import annotations

import argparse
import os
import sys
from typing import Optional

from convert_keyence_files.reader import read_file
from convert_keyence_files.exporters import export_height_csv, export_optical, export_laser

EXTENSIONS = {".vk4", ".vk6", ".vk7"}
IMAGE_EXTENSIONS = {"png": ".png", "tiff": ".tiff"}


def collect_input_files(inputs, recursive=False):
    # type: (list, bool) -> list
    result = []
    for path in inputs:
        if os.path.isdir(path):
            if recursive:
                for root, dirs, files in os.walk(path):
                    for fname in sorted(files):
                        if os.path.splitext(fname)[1].lower() in EXTENSIONS:
                            result.append(os.path.join(root, fname))
            else:
                for fname in sorted(os.listdir(path)):
                    full = os.path.join(path, fname)
                    if os.path.isfile(full) and os.path.splitext(fname)[1].lower() in EXTENSIONS:
                        result.append(full)
        elif os.path.isfile(path):
            result.append(path)
        else:
            print("Warning: skipping %s (not a file or directory)" % path, file=sys.stderr)
    return result


def build_output_path(input_path, output_dir, layer_name, ext, input_base=None):
    # type: (str, str, str, str, Optional[str]) -> str
    stem = os.path.splitext(os.path.basename(input_path))[0]
    if input_base is not None:
        rel = os.path.relpath(os.path.dirname(input_path), input_base)
        if rel and rel != ".":
            stem = rel.replace(os.sep, "_") + "_" + stem
    return os.path.join(output_dir, "%s_%s%s" % (stem, layer_name, ext))


def main():
    # type: () -> None
    parser = argparse.ArgumentParser(
        prog="convert-keyence",
        description="Convert Keyence .vk4/.vk6/.vk7 files to PNG, TIFF, and CSV",
    )
    parser.add_argument("inputs", nargs="+", help="Input files or directories")
    parser.add_argument("-o", "--output", required=True, help="Output directory")
    parser.add_argument(
        "--only", help="Comma-separated list of layers to export: height, optical, laser"
    )
    parser.add_argument(
        "--recursive", action="store_true",
        help="When input is a directory, scan subdirectories too",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="List what would be converted without doing anything",
    )
    parser.add_argument(
        "--image-format", default="png", choices=["png", "tiff"],
        help="Image output format (default: png)",
    )

    args = parser.parse_args()

    layers = {"height", "optical", "laser"}
    if args.only:
        layers = set(args.only.split(","))
        invalid = layers - {"height", "optical", "laser"}
        if invalid:
            parser.error("Unknown layer(s): %s" % ", ".join(sorted(invalid)))

    files = collect_input_files(args.inputs, recursive=args.recursive)
    if not files:
        print("No .vk4/.vk6/.vk7 files found.", file=sys.stderr)
        sys.exit(1)

    input_base = None
    if args.recursive:
        for inp in args.inputs:
            if os.path.isdir(inp):
                input_base = inp
                break

    img_ext = IMAGE_EXTENSIONS[args.image_format]

    if not args.dry_run:
        os.makedirs(args.output, exist_ok=True)
    else:
        print("Would convert:")

    for fpath in files:
        outputs = []
        if "height" in layers:
            outputs.append(("height", ".csv"))
        if "optical" in layers:
            outputs.append(("optical", img_ext))
        if "laser" in layers:
            outputs.append(("laser", img_ext))

        out_paths = []
        for layer_name, ext in outputs:
            out_paths.append(
                (layer_name, build_output_path(fpath, args.output, layer_name, ext, input_base))
            )

        if args.dry_run:
            out_str = ", ".join(p for _, p in out_paths)
            print("  %s -> %s" % (fpath, out_str))
            continue

        try:
            kf = read_file(fpath)
        except Exception as e:
            print("Error reading %s: %s" % (fpath, e), file=sys.stderr)
            continue

        for layer_name, out_path in out_paths:
            try:
                if layer_name == "height":
                    export_height_csv(kf, out_path)
                elif layer_name == "optical":
                    if kf.optical is None:
                        print("Warning: %s has no optical data, skipping" % fpath, file=sys.stderr)
                        continue
                    export_optical(kf, out_path)
                elif layer_name == "laser":
                    if kf.laser is None:
                        print("Warning: %s has no laser data, skipping" % fpath, file=sys.stderr)
                        continue
                    export_laser(kf, out_path)
            except Exception as e:
                print("Error exporting %s from %s: %s" % (layer_name, fpath, e), file=sys.stderr)


if __name__ == "__main__":
    main()
