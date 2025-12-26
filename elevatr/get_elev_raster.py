# Copyright (c) 2025 Titouan Le Gourrierec
"""Get elevation raster for a bounding box from AWS Terrain Tiles."""

import logging
import pathlib
import shutil

from . import settings
from .downloader import _get_aws_terrain
from .raster import Raster
from .raster_operations import _clip_bbx, _merge_rasters
from .utils import _estimate_files_size


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

MIN_ZOOM, MAX_ZOOM = 0, 14
MIN_LATITUDE, MAX_LATITUDE = -90, 90
MIN_LONGITUDE, MAX_LONGITUDE = -180, 180


def get_elev_raster(
    locations: tuple[float, float, float, float],
    zoom: int,
    crs: str | None = "EPSG:3857",  # Web Mercator projection
    clip: str | None = "bbox",
    cache_folder: str | None = None,
    *,
    use_cache: bool | None = True,
    delete_cache: bool | None = True,
    verbose: bool | None = True,
) -> Raster | None:
    """
    Get elevation raster for a bounding box. The raster is downloaded from AWS Terrain Tiles.

    Args:
        locations (tuple): Bounding box coordinates (min_lon, min_lat, max_lon, max_lat) in WGS84/EPSG:4326.
            (min_lon, min_lat) is the bottom-left corner and (max_lon, max_lat) is the top-right corner.
        zoom (int): Zoom level of the raster. Between 0 and 14. Greater zoom level means higher resolution.
        crs (str, optional): Coordinate Reference System of the raster, by default "EPSG:3857" (Web Mercator proj).
        clip (str, optional): Clip the raster to the bounding box ('bbox') or the tile ('tile'), by default 'bbox'.
        cache_folder (str, optional): Folder to store the downloaded tiles, by default settings.cache_folder.
            NOTE: If you want to change the cache folder, it is recommended to set it with settings.cache_folder =
            "your_folder" just after the import to standardize the cache folder across the package.
        use_cache (bool, optional): Use the cache if available, by default True
        delete_cache (bool, optional): Delete the cache folder after the raster is created, by default True
        verbose (bool, optional): Print progress messages, by default True

    Returns:
        Raster: A Raster object containing the elevation raster and metadata.

    Examples:
    >>> import elevatr as elv
    >>> locations = (-5.14, 41.33, 9.56, 51.09)
    >>> zoom = 6
    >>> raster = elv.get_elev_raster(locations, zoom)

    Raises:
        AssertionError: If the inputs are not valid.
        ValueError: If clip is not 'bbox' or 'tile'.
        TypeError: If cache_folder is not a string, use_cache is not a boolean, delete_cache is not a boolean or
        verbose is not a boolean.

    """
    # Validate inputs
    if not (
        isinstance(locations, tuple)
        and len(locations) == 4  # noqa: PLR2004
        and all(isinstance(x, (int, float)) for x in locations)
        and all(MIN_LONGITUDE <= x <= MAX_LONGITUDE for x in locations[::2])  # Longitudes
        and all(MIN_LATITUDE <= x <= MAX_LATITUDE for x in locations[1::2])  # Latitudes
    ):
        msg = (
            "locations must be a tuple of length 4 containing only integers or floats. "
            "Longitude must be between -180 and 180. Latitude must be between -90 and 90."
        )
        raise AssertionError(msg)
    if not isinstance(zoom, int) or not (MIN_ZOOM <= zoom <= MAX_ZOOM):
        msg = f"zoom must be an integer between {MIN_ZOOM} and {MAX_ZOOM}."
        raise AssertionError(msg)
    if clip not in set({"bbox", "tile"}):
        msg = "clip must be either 'bbox' or 'tile'."
        raise ValueError(msg)
    if cache_folder is not None and not isinstance(cache_folder, str):
        msg = "cache_folder must be a string."
        raise TypeError(msg)
    if not isinstance(use_cache, bool):
        msg = "use_cache must be a boolean."
        raise TypeError(msg)
    if not isinstance(delete_cache, bool):
        msg = "delete_cache must be a boolean."
        raise TypeError(msg)
    if not isinstance(verbose, bool):
        msg = "verbose must be a boolean."
        raise TypeError(msg)

    cache_folder = cache_folder or settings.cache_folder
    if not pathlib.Path(cache_folder).exists():
        pathlib.Path(cache_folder).mkdir(parents=True)

    if settings.ask_confirmation:  # pragma: no cover
        size = _estimate_files_size(locations, zoom)
        if size > settings.min_size_for_confirmation:
            confirmation = input(f"The estimated file size is {int(size)} Go. Do you want to continue? (y/n)")
            if confirmation.lower() != "y":
                logger.info("Operation aborted by the user.")
                if delete_cache:
                    shutil.rmtree(cache_folder)
                return None

    downloaded_tiles = _get_aws_terrain(
        bbx=locations,
        zoom=zoom,
        cache_folder=cache_folder,
        use_cache=use_cache,
        verbose=verbose,
    )

    if verbose:
        logger.info("Mosaicing tiles.")
        mosaic, meta = _merge_rasters(downloaded_tiles)
    else:
        mosaic, meta = _merge_rasters(downloaded_tiles)

    # Clip the raster to the bounding box
    if clip == "bbox":
        mosaic, meta = _clip_bbx(mosaic, meta, locations)

    if delete_cache:
        shutil.rmtree(cache_folder)

    raster = Raster(mosaic, meta)

    # Reproject the raster if needed
    if crs is not None and crs != "EPSG:3857":
        raster.reproject(crs)

    return raster
