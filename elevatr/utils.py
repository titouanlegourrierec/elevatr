import math
from typing import Tuple

import numpy as np
import pandas as pd


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


def _get_tile_xy(bbx: dict, zoom: int) -> pd.DataFrame:
    """Generate a DataFrame of tile coordinates within a bounding box at a specific zoom level.

    Parameters
    ----------
    bbx : dict
        A dictionary representing the bounding box with keys 'xmin', 'xmax', 'ymin', and 'ymax'.
        - 'xmin' : float
            Minimum longitude of the bounding box.
        - 'xmax' : float
            Maximum longitude of the bounding box.
        - 'ymin' : float
            Minimum latitude of the bounding box.
        - 'ymax' : float
            Maximum latitude of the bounding box.
    zoom : int
        Zoom level, a non-negative integer where higher values correspond to more detailed tiles.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the tile coordinates within the bounding box at the specified zoom level.
        The DataFrame has two columns:
        - 'tile_x' : int
            The tile number along the x-axis (longitude).
        - 'tile_y' : int
            The tile number along the y-axis (latitude).

    Notes
    -----
    - The function normalizes the bounding box coordinates to ensure they are within valid ranges.
    - Tile indices are clamped to valid ranges: `[0, 2**zoom - 1]`.
    - The function uses the Web Mercator projection to map geographic coordinates onto a 2D plane.
    - For zoom levels 0 and 1, the function ensures that the tile coordinates are within the valid range for
    those zoom levels.

    Examples
    --------
    >>> bbx = {'xmin': -5.14, 'ymin': 41.33, 'xmax': 9.56, 'ymax': 51.09}
    >>>_get_tile_xy(bbx, 6)
       tile_x  tile_y
    0      31      21
    1      31      22
    2      31      23
    3      32      21
    4      32      22
    5      32      23
    6      33      21
    7      33      22
    8      33      23
    """

    # Normalize bounding box coordinates
    bbx["xmin"], bbx["xmax"] = sorted([bbx["xmin"], bbx["xmax"]])
    bbx["ymin"], bbx["ymax"] = sorted([bbx["ymin"], bbx["ymax"]])
    bbx["xmin"] = bbx["xmin"] - 360 if bbx["xmin"] > 180 else bbx["xmin"]
    bbx["xmax"] = bbx["xmax"] - 360 if bbx["xmax"] > 180 else bbx["xmax"]

    # Convert to float
    bbx = {k: float(v) for k, v in bbx.items()}

    # Get tile numbers
    min_tile = _lonlat_to_tilenum(bbx["xmin"], bbx["ymin"], zoom)
    max_tile = _lonlat_to_tilenum(bbx["xmax"], bbx["ymax"], zoom)
    xmin, xmax = min_tile[0], max_tile[0]
    ymin, ymax = min_tile[1], max_tile[1]

    if ymin > ymax:
        ymin, ymax = ymax, ymin

    # Generate tile coordinates
    x_tiles = np.arange(xmin, xmax + 1)
    y_tiles = np.arange(ymin, ymax + 1)
    tiles = pd.DataFrame(
        np.array(np.meshgrid(x_tiles, y_tiles)).T.reshape(-1, 2),
        columns=["tile_x", "tile_y"],
    )

    if zoom == 1:
        tiles = tiles[(tiles["tile_x"] < 2) & (tiles["tile_y"] < 2)]
    elif zoom == 0:
        tiles = tiles[(tiles["tile_x"] < 1) & (tiles["tile_y"] < 1)]

    return tiles
