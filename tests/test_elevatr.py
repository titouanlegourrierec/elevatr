import pytest

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
