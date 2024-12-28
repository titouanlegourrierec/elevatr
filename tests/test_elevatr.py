import os
import tempfile
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import rasterio
import requests  # type: ignore
from rasterio.transform import from_origin

from elevatr.downloader import _get_aws_terrain
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


####


@pytest.fixture
def bbx():
    """Bounding box coordinates for testing."""
    return {
        "xmin": -123.1,
        "xmax": -122.9,
        "ymin": 37.7,
        "ymax": 37.8,
    }


@pytest.fixture
def zoom():
    """Zoom level for testing."""
    return 0


def test_get_aws_terrain(bbx, zoom, tmp_path):
    """Test downloading AWS terrain data."""
    cache_folder = str(tmp_path)  # Use a temporary directory for storing tiles

    # Call the actual function
    result = _get_aws_terrain(bbx, zoom, cache_folder, use_cache=False, verbose=True)

    # Assertions
    assert len(result) > 0  # Ensure files were downloaded
    for filepath in result:
        assert os.path.exists(filepath)  # Ensure files exist
        assert filepath.endswith(".tif")  # Ensure they are .tif files


def test_get_aws_terrain_with_cache(bbx, zoom, tmp_path):
    """Test downloading AWS terrain data with cache."""
    cache_folder = str(tmp_path)  # Use a temporary directory

    # Simulate a cached file
    existing_tile_filename = os.path.join(cache_folder, "geotiff_0_0_0.tif")
    os.makedirs(os.path.dirname(existing_tile_filename), exist_ok=True)
    with open(existing_tile_filename, "wb") as f:
        f.write(b"cached_tile_data")

    # Call the function
    result = _get_aws_terrain(bbx, zoom, cache_folder, use_cache=True, verbose=True)

    # Assertions
    assert len(result) > 0  # Ensure files are returned
    assert existing_tile_filename in result  # Ensure the cached file is included

    # Ensure new files are downloaded (if applicable)
    for filepath in result:
        assert os.path.exists(filepath)
        assert filepath.endswith(".tif")


def test_get_aws_terrain_invalid_file_type(bbx, zoom, tmp_path):
    """Test handling of invalid file types in AWS terrain data download."""
    cache_folder = str(tmp_path)

    # Simulate an HTTP response with an incorrect MIME type
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "text/html"}  # Incorrect MIME type
        mock_response.iter_content.return_value = iter([b"some data"])
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Ensure the function raises ValueError
        with pytest.raises(ValueError, match="Invalid file type for URL"):
            _get_aws_terrain(bbx, zoom, cache_folder, use_cache=False, verbose=False)


def test_get_aws_terrain_request_exception(bbx, zoom, tmp_path):
    """Test handling of network exceptions in AWS terrain data download."""
    cache_folder = str(tmp_path)

    # Simulate a network exception with RequestException
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.RequestException("Network error")

        # Ensure the function raises RuntimeError
        with pytest.raises(RuntimeError, match="Failed to download"):
            _get_aws_terrain(bbx, zoom, cache_folder, use_cache=False, verbose=False)
