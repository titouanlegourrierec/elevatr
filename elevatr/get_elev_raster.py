import os
import shutil
from typing import Optional, Tuple

from .downloader import _get_aws_terrain
from .raster import Raster
from .raster_operations import _clip_bbx, _merge_rasters


def get_elev_raster(
    locations: Tuple[float, float, float, float],
    zoom: int,
    clip: Optional[str] = "bbox",
    cache_folder: Optional[str] = "./cache",
    use_cache: Optional[bool] = True,
    delete_cache: Optional[bool] = True,
    verbose: Optional[bool] = True,
) -> Raster:
    """Get elevation raster for a bounding box. The raster is downloaded from AWS Terrain Tiles.

    Parameters
    ----------
    locations : Tuple[float, float, float, float]
        Bounding box coordinates (min_lon, min_lat, max_lon, max_lat) in WGS84/EPSG:4326.
        (min_lon, min_lat) is the bottom-left corner and (max_lon, max_lat) is the top-right corner.
    zoom : int
        Zoom level of the raster. Between 0 and 14. Greater zoom level means higher resolution.
    clip : str, optional
        Clip the raster to the bounding box ('bbox') or the tile ('tile'), by default 'bbox'.
    cache_folder : str, optional
        Folder to store the downloaded tiles, by default "./cache"
    use_cache : bool, optional
        Use the cache if available, by default True
    delete_cache : bool, optional
        Delete the cache folder after the raster is created, by default True
    verbose : bool, optional
        Print progress messages, by default True

    Returns
    -------
    Raster
        A Raster object containing the elevation raster and metadata.

    Examples
    --------
    >>> from elevatr import get_elev_raster
    >>> locations = (-5.14, 41.33, 9.56, 51.09)
    >>> zoom = 6
    >>> raster = get_elev_raster(locations, zoom)
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
    assert clip in ["bbox", "tile"], "clip must be either 'bbox' or 'tile'."
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

    # Clip the raster to the bounding box
    if clip == "bbox":
        mosaic, meta = _clip_bbx(mosaic, meta, bbx)

    if delete_cache:
        shutil.rmtree(cache_folder)

    return Raster(mosaic, meta)
