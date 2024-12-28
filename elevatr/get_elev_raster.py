import os
import shutil
from typing import Optional, Tuple

import numpy as np

from .downloader import _get_aws_terrain
from .raster_operations import _merge_rasters


def get_elev_raster(
    locations: Tuple[float, float, float, float],
    zoom: int,
    cache_folder: Optional[str] = "./cache",
    use_cache: Optional[bool] = True,
    delete_cache: Optional[bool] = True,
    verbose: Optional[bool] = True,
) -> Tuple[np.ndarray, dict]:
    """
    Get elevation raster for a bounding box. The raster is downloaded from AWS Terrain Tiles.

    Parameters
    ----------
    locations : Tuple[float, float, float, float]
        Bounding box coordinates (min_lon, min_lat, max_lon, max_lat) in WGS84/EPSG:4326.
        (min_lon, min_lat) is the bottom-left corner and (max_lon, max_lat) is the top-right corner.
    zoom : int
        Zoom level of the raster. Between 0 and 14.
    cache_folder : Optional[str], optional
        Folder to store the downloaded tiles, by default "./cache"
    use_cache : Optional[bool], optional
        Use the cache if available, by default True
    delete_cache : Optional[bool], optional
        Delete the cache folder after the raster is created, by default True
    verbose : Optional[bool], optional
        Print progress messages, by default True

    Returns
    -------
    Tuple[np.ndarray, dict]
        Elevation raster and metadata dictionary with the following keys:

    Examples
    --------
    >>> from elevatr import get_elev_raster
    >>> locations = (-122.5, 37.5, -122, 38)
    >>> zoom = 8
    >>> raster, meta = get_elev_raster(locations, zoom)
    """
    # Validate inputs
    is_valid_locations = (
        isinstance(locations, tuple)
        and len(locations) == 4
        and all(isinstance(x, (int, float)) for x in locations)
        and all(-180 <= x <= 180 for x in locations[::2])  # Longitudes
        and all(-90 <= x <= 90 for x in locations[1::2])  # Latitudes
    )
    assert is_valid_locations, (
        "locations must be a tuple of length 4 containing only integers or floats. "
        "Longitude must be between -180 and 180. Latitude must be between -90 and 90."
    )

    bbx = {
        "xmin": locations[0],
        "ymin": locations[1],
        "xmax": locations[2],
        "ymax": locations[3],
    }

    assert (
        isinstance(zoom, int) and 0 <= zoom <= 14
    ), "zoom must be an integer between 0 and 14."
    assert isinstance(cache_folder, str), "cache_folder must be a string."
    assert isinstance(use_cache, bool), "use_cache must be a boolean."
    assert isinstance(delete_cache, bool), "delete_cache must be a boolean."
    assert isinstance(verbose, bool), "verbose must be a boolean."

    if not os.path.exists(cache_folder):
        os.makedirs(cache_folder)

    downloaded_tiles = _get_aws_terrain(
        bbx=bbx,
        zoom=zoom,
        cache_folder=cache_folder,
        use_cache=use_cache,
        verbose=verbose,
    )

    if verbose:
        print("Mosaicing tiles.")
        mosaic, meta = _merge_rasters(downloaded_tiles)
    else:
        mosaic, meta = _merge_rasters(downloaded_tiles)

    if delete_cache:
        shutil.rmtree(cache_folder)

    return mosaic, meta
