import math
from typing import Tuple


def _lonlat_to_tilenum(lon_deg: float, lat_deg: float, zoom: int) -> Tuple[int, int]:
    """Convert geographic coordinates (longitude, latitude) to tile numbers at a specific zoom level.

    Parameters
    ----------
    lon_deg : float
        Longitude in degrees, ranging from -180 to 180.
    lat_deg : float
        Latitude in degrees, ranging from -90 to 90.
    zoom : int
        Zoom level, a non-negative integer where higher values correspond to more detailed tiles.

    Returns
    -------
    xtile : int
        The tile number along the x-axis (longitude).
    ytile : int
        The tile number along the y-axis (latitude).

    Notes
    -----
    - The function uses the Web Mercator projection to map geographic coordinates onto a 2D plane.
    - Tile indices are clamped to valid ranges: `[0, 2**zoom - 1]`.
    - The function is based on the Slippy Map tilenames documented here:
        https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames

    Examples
    --------
    >>> lonlat_to_tilenum(0, 0, 2)
    (2, 2)

    >>> lonlat_to_tilenum(-180, 0, 2)
    (0, 2)

    >>> lonlat_to_tilenum(180, 85, 4)
    (15, 0)

    >>> lonlat_to_tilenum(0, -85, 3)
    (4, 7)
    """

    lon_rad = math.radians(lon_deg)
    lat_rad = math.radians(lat_deg)

    x = (1 + (lon_rad / math.pi)) / 2
    y = (1 - (math.asinh(math.tan(lat_rad)) / math.pi)) / 2

    n_tiles = 2**zoom

    xtile = max(0, min(n_tiles - 1, int(x * n_tiles)))
    ytile = max(0, min(n_tiles - 1, int(y * n_tiles)))

    return xtile, ytile
