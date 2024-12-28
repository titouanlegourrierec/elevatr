import os
import tempfile

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from elevatr.raster_operations import _merge_rasters
from elevatr.utils import _get_tile_xy, _lonlat_to_tilenum


@pytest.mark.parametrize(
    "lon_deg, lat_deg, zoom, expected",
    [
        (0, 0, 2, (2, 2)),  # Center of the map
        (-180, 0, 2, (0, 2)),  # Left edge
        (180, 0, 2, (3, 2)),  # Right edge
        (0, 85, 2, (2, 0)),  # Near the North Pole
        (0, -85, 2, (2, 3)),  # Near the South Pole
        (-180, -85, 0, (0, 0)),  # Minimum zoom level
        (180, 85, 0, (0, 0)),  # Minimum zoom with extreme coordinates
        (0, 0, 20, (524288, 524288)),  # High zoom level
    ],
)
def test_lonlat_to_tilenum(lon_deg, lat_deg, zoom, expected):
    """Test the conversion of longitude/latitude coordinates to tile numbers."""
    result = _lonlat_to_tilenum(lon_deg, lat_deg, zoom)
    assert (
        result == expected
    ), f"Failed for lon={lon_deg}, lat={lat_deg}, zoom={zoom}. Got: {result}, expected: {expected}"


@pytest.mark.parametrize(
    "bbx, zoom, max_tile_x, max_tile_y",
    [
        ({"xmin": -10, "xmax": 10, "ymin": -10, "ymax": 10}, 0, 0, 0),
        ({"xmin": -10, "xmax": 10, "ymin": -10, "ymax": 10}, 1, 1, 1),
    ],
)
def test_get_tile_xy_zoom_levels(bbx, zoom, max_tile_x, max_tile_y):
    """Test if the tiles are correctly filtered based on zoom level."""
    result = _get_tile_xy(bbx, zoom)
    assert (
        result["tile_x"] <= max_tile_x
    ).all(), f"Tile x-coordinates exceed max for zoom {zoom}"
    assert (
        result["tile_y"] <= max_tile_y
    ).all(), f"Tile y-coordinates exceed max for zoom {zoom}"


@pytest.fixture
def create_test_rasters():
    """Fixture to create temporary raster files for testing."""
    rasters = []
    temp_dir = tempfile.TemporaryDirectory()

    for i in range(2):
        data = np.ones((1, 5, 5), dtype=np.float32) * (i + 1)  # Create 5x5 raster data
        transform = from_origin(i * 5, 0, 1, 1)

        raster_path = os.path.join(temp_dir.name, f"test_raster_{i}.tif")
        with rasterio.open(
            raster_path,
            "w",
            driver="GTiff",
            height=5,
            width=5,
            count=1,
            dtype="float32",
            crs="EPSG:3857",
            transform=transform,
        ) as dst:
            dst.write(data)

        rasters.append(raster_path)

    yield rasters
    temp_dir.cleanup()


def test_merge_rasters(create_test_rasters):
    """Test the merge_rasters function."""
    raster_list = create_test_rasters
    mosaic, meta = _merge_rasters(raster_list)

    assert mosaic.shape == (1, 5, 10)  # Check mosaic shape
    assert meta["crs"].to_string() == "EPSG:3857"  # Check CRS
    assert mosaic[0, 0, 0] == 1  # Check the first pixel value
    assert mosaic[0, 0, 5] == 2  # Check the transition between rasters
