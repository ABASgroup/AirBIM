"""Unit tests for point cloud bound helpers."""

from pathlib import Path

import pytest

from utils.pointcloud import get_laz_bounds, validate_crop_within_bounds


def test_get_laz_bounds_reads_header(test_building_laz_path: Path) -> None:
    min_xyz, max_xyz = get_laz_bounds(test_building_laz_path)
    assert len(min_xyz) == 3
    assert len(max_xyz) == 3
    assert all(a <= b for a, b in zip(min_xyz, max_xyz))


def test_validate_crop_within_bounds_ok() -> None:
    validate_crop_within_bounds(
        (0.0, 0.0, 0.0),
        (1.0, 1.0, 1.0),
        bounds_min=(0.0, 0.0, 0.0),
        bounds_max=(2.0, 2.0, 2.0),
    )


def test_validate_crop_outside_min_raises() -> None:
    with pytest.raises(ValueError, match="crop_min_xyz"):
        validate_crop_within_bounds(
            (-1.0, 0.0, 0.0),
            None,
            bounds_min=(0.0, 0.0, 0.0),
            bounds_max=(2.0, 2.0, 2.0),
        )


def test_validate_crop_min_gt_max_raises() -> None:
    with pytest.raises(ValueError, match="must be <="):
        validate_crop_within_bounds(
            (1.5, None, None),
            (1.0, None, None),
            bounds_min=(0.0, 0.0, 0.0),
            bounds_max=(2.0, 2.0, 2.0),
        )
