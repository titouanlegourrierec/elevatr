import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

import matplotlib
import numpy as np
import pytest
import rasterio
import requests  # type: ignore
from rasterio.transform import from_origin

from elevatr.downloader import _get_aws_terrain
from elevatr.get_elev_raster import get_elev_raster
from elevatr.raster import Raster
from elevatr.raster_operations import _merge_rasters
from elevatr.utils import _get_tile_xy, _lonlat_to_tilenum

matplotlib.use("Agg")  # Use a non-interactive backend for testing

# Test cases for utils


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


# Test cases for raster_operations


@pytest.fixture
def create_test_rasters():
    """Fixture to create temporary raster files for testing."""
    rasters = []
    temp_dir = tempfile.TemporaryDirectory()

    for i in range(2):
        data = np.ones((1, 2, 2), dtype=np.float32) * (i + 1)  # Create 2x2 raster data
        transform = from_origin(10 + i * 2, 10, 1, 1)

        raster_path = os.path.join(temp_dir.name, f"test_raster_{i}.tif")
        with rasterio.open(
            raster_path,
            "w",
            driver="GTiff",
            height=2,
            width=2,
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

    assert mosaic.shape == (1, 2, 4)  # Check mosaic shape
    assert meta["crs"].to_string() == "EPSG:3857"  # Check CRS
    assert mosaic[0, 0, 0] == 1  # Check the first pixel value
    assert mosaic[0, 0, 2] == 2  # Check the transition between rasters


# Test cases for downloader


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


# Test cases for get_elev_raster


@pytest.fixture
def mock_bbox():
    """Fixture to provide a valid mock bounding box."""
    return (-122.5, 37.5, -122.0, 38.0)


@pytest.fixture
def mock_zoom():
    """Fixture to provide a valid zoom level."""
    return 8


@pytest.fixture
def mock_cache_folder(tmp_path):
    """Fixture to create a temporary cache folder."""
    return str(tmp_path / "cache")


def test_get_elev_raster_valid_inputs(mock_bbox, mock_zoom, mock_cache_folder):
    """Test get_elev_raster with valid inputs."""
    with patch("elevatr.downloader._get_aws_terrain") as mock_get_aws_terrain, patch(
        "elevatr.raster_operations._merge_rasters"
    ) as mock_merge_rasters:
        mock_get_aws_terrain.return_value = ["tile1.tif", "tile2.tif"]
        mock_merge_rasters.return_value = (np.zeros((1, 2, 2)), {"crs": "EPSG:3857"})

        raster = get_elev_raster(
            locations=mock_bbox,
            zoom=mock_zoom,
            cache_folder=mock_cache_folder,
            use_cache=True,
            delete_cache=False,
            verbose=False,
        )

        data = raster.data
        meta = raster.meta

        assert isinstance(data, np.ndarray), "Raster should be a numpy array."
        assert isinstance(meta, dict), "Metadata should be a dictionary."
        assert "crs" in meta, "Metadata should contain CRS."


def test_get_elev_raster_delete_cache(mock_bbox, mock_zoom, mock_cache_folder):
    """Test get_elev_raster with cache deletion."""
    with patch("shutil.rmtree") as mock_rmtree, patch(
        "elevatr.downloader._get_aws_terrain"
    ) as mock_get_aws_terrain, patch(
        "elevatr.raster_operations._merge_rasters"
    ) as mock_merge_rasters:
        mock_get_aws_terrain.return_value = []
        mock_merge_rasters.return_value = (np.zeros((1, 2, 2)), {"crs": "EPSG:3857"})

        get_elev_raster(
            locations=mock_bbox,
            zoom=mock_zoom,
            cache_folder=mock_cache_folder,
            use_cache=True,
            delete_cache=True,
            verbose=False,
        )

        mock_rmtree.assert_called_once_with(mock_cache_folder)


def test_get_elev_raster_invalid_locations():
    """Test get_elev_raster with invalid locations."""
    invalid_locations = "invalid"

    with pytest.raises(AssertionError, match="locations must be a tuple of length 4"):
        get_elev_raster(
            locations=invalid_locations,
            zoom=8,
            cache_folder="./cache",
            use_cache=True,
            delete_cache=True,
            verbose=False,
        )


def test_get_elev_raster_invalid_zoom(mock_bbox):
    """Test get_elev_raster with invalid zoom level."""
    invalid_zoom = 20  # Out of valid range

    with pytest.raises(
        AssertionError, match="zoom must be an integer between 0 and 14"
    ):
        get_elev_raster(
            locations=mock_bbox,
            zoom=invalid_zoom,
            cache_folder="./cache",
            use_cache=True,
            delete_cache=True,
            verbose=False,
        )


def test_get_elev_raster_no_cache_folder(mock_bbox, mock_zoom):
    """Test get_elev_raster when the cache folder does not exist."""
    cache_folder = "./non_existing_cache"

    with patch("elevatr.downloader._get_aws_terrain") as mock_get_aws_terrain, patch(
        "elevatr.raster_operations._merge_rasters"
    ) as mock_merge_rasters:
        mock_get_aws_terrain.return_value = ["tile1.tif", "tile2.tif"]
        mock_merge_rasters.return_value = (np.zeros((1, 2, 2)), {"crs": "EPSG:3857"})

        get_elev_raster(
            locations=mock_bbox,
            zoom=mock_zoom,
            cache_folder=cache_folder,
            use_cache=True,
            delete_cache=False,
            verbose=True,
        )

        assert os.path.exists(cache_folder), "Cache folder should be created."

        shutil.rmtree(cache_folder)


# Test cases for raster


def test_raster_post_init():
    """Test the initialization of the Raster class."""
    data = np.random.rand(1, 2, 2)
    meta = {
        "crs": "EPSG:4326",
        "height": 2,
        "width": 2,
        "dtype": "float32",
        "nodata": -9999,
        "transform": rasterio.transform.from_origin(0, 0, 1, 1),
    }
    raster = Raster(data=data, meta=meta)

    assert raster.crs == "EPSG:4326"
    assert raster.height == 2
    assert raster.width == 2
    assert raster.dtype == "float32"
    assert raster.nodata == -9999
    assert raster.transform == meta["transform"]


def test_raster_show():
    """Test the show method of the Raster class."""
    data = np.random.rand(1, 2, 2)
    meta = {"transform": rasterio.transform.from_origin(0, 0, 1, 1)}
    raster = Raster(data=data, meta=meta)

    with patch("matplotlib.pyplot.show") as mock_show:
        raster.show(cmap="viridis", clip_zero=True)
        mock_show.assert_called_once()


def test_raster_to_numpy():
    """Test the to_numpy method of the Raster class."""
    data = np.random.rand(1, 2, 2)
    meta = {}
    raster = Raster(data=data, meta=meta)

    np_array = raster.to_numpy()
    assert isinstance(np_array, np.ndarray)
    assert np.array_equal(np_array, data[0])


def test_raster_to_tif():
    """Test the to_tif method of the Raster class."""
    data = np.random.rand(1, 2, 2).astype(np.float32)
    meta = {
        "driver": "GTiff",
        "height": 2,
        "width": 2,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:4326",
        "transform": rasterio.transform.from_origin(1, 0, 1, 1),
    }
    raster = Raster(data=data, meta=meta)

    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as temp_tif:
        temp_tif.close()
        raster.to_tif(temp_tif.name)
        assert os.path.exists(temp_tif.name)

        assert os.path.exists(temp_tif.name)

        with rasterio.open(temp_tif.name) as src:
            read_data = src.read(1)
            assert np.array_equal(read_data, data[0])
            assert src.crs.to_string() == "EPSG:4326"
            assert src.meta["dtype"] == "float32"

    os.remove(temp_tif.name)


def test_raster_to_tif_invalid_compression():
    """Test the to_tif method of the Raster class with an invalid compression format."""
    data = np.random.rand(1, 2, 2).astype(np.float32)
    meta = {
        "driver": "GTiff",
        "height": 2,
        "width": 2,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:4326",
        "transform": rasterio.transform.from_origin(1, 0, 1, 1),
    }
    raster = Raster(data=data, meta=meta)

    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as temp_tif:
        temp_tif.close()
        with pytest.raises(
            ValueError,
            match="Invalid compression type: invalid_compression. Valid options are",
        ):
            raster.to_tif(temp_tif.name, compress="invalid_compression")


@pytest.fixture
def mock_raster_data():
    """Fixture to provide mock raster data and metadata."""
    data = np.random.rand(1, 2, 2).astype(np.float32)
    meta = {
        "driver": "GTiff",
        "height": 2,
        "width": 2,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:3857",
        "transform": rasterio.transform.from_origin(1, 0, 1, 1),
    }
    return data, meta


def test_raster_save_and_load(mock_raster_data):
    """Test saving and loading raster data to and from a GeoTIFF file."""
    data, meta = mock_raster_data
    raster = Raster(data=data, meta=meta)

    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as temp_tif:
        temp_tif.close()
        raster.to_tif(temp_tif.name)

        with rasterio.open(temp_tif.name) as src:
            loaded_data = src.read(1)
            assert np.array_equal(loaded_data, raster.to_numpy())
            assert src.meta["crs"] == raster.meta["crs"]

    os.remove(temp_tif.name)


def test_raster_show_clip_zero():
    """Test the show method with clip_zero=True."""
    data = np.random.randn(1, 2, 2)  # Random data including negative values
    meta = {"transform": rasterio.transform.from_origin(0, 0, 1, 1)}
    raster = Raster(data=data, meta=meta)

    with patch("matplotlib.pyplot.show") as mock_show:
        raster.show(cmap="viridis", clip_zero=True)
        clipped_data = np.where(data[0] < 0, np.nan, data[0])
        assert np.array_equal(
            raster.to_numpy()[raster.to_numpy() >= 0], clipped_data[clipped_data >= 0]
        )
        mock_show.assert_called_once()
