import pytest

from elevatr.utils import _lonlat_to_tilenum


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
