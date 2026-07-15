"""Point cloud geometry helpers (API-safe: laspy only, no PDAL)."""
from pathlib import Path

import laspy


def get_laz_bounds(path: str | Path) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """
    Read min/max XYZ from a LAS/LAZ file header without loading all points.

    Returns:
        (min_xyz, max_xyz) as ((x_min, y_min, z_min), (x_max, y_max, z_max))
    """
    path = Path(path)
    with laspy.open(path) as reader:
        header = reader.header
        min_xyz = (float(header.x_min), float(header.y_min), float(header.z_min))
        max_xyz = (float(header.x_max), float(header.y_max), float(header.z_max))
    return min_xyz, max_xyz


def validate_crop_within_bounds(
    crop_min_xyz: tuple[float | None, float | None, float | None] | None,
    crop_max_xyz: tuple[float | None, float | None, float | None] | None,
    bounds_min: tuple[float, float, float],
    bounds_max: tuple[float, float, float],
) -> None:
    """Raise ValueError if crop extends outside file bounds or min > max."""
    if crop_min_xyz is None and crop_max_xyz is None:
        return

    if crop_min_xyz is not None and len(crop_min_xyz) != 3:
        raise ValueError("crop_min_xyz must contain exactly 3 values: X, Y, Z")
    if crop_max_xyz is not None and len(crop_max_xyz) != 3:
        raise ValueError("crop_max_xyz must contain exactly 3 values: X, Y, Z")

    labels = ("X", "Y", "Z")
    for i, label in enumerate(labels):
        c_min = None if crop_min_xyz is None else crop_min_xyz[i]
        c_max = None if crop_max_xyz is None else crop_max_xyz[i]

        if c_min is not None:
            c_min = float(c_min)
            if c_min < bounds_min[i]:
                raise ValueError(
                    f"crop_min_xyz[{label}] must be >= file min {bounds_min[i]}"
                )
        if c_max is not None:
            c_max = float(c_max)
            if c_max > bounds_max[i]:
                raise ValueError(
                    f"crop_max_xyz[{label}] must be <= file max {bounds_max[i]}"
                )
        if c_min is not None and c_max is not None and c_min > c_max:
            raise ValueError(f"crop_min_xyz[{label}] must be <= crop_max_xyz[{label}]")
