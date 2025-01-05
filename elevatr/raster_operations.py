from contextlib import ExitStack
from typing import List, Tuple

import numpy as np
import pyproj
import rasterio
from rasterio.merge import merge


def _merge_rasters(raster_list: List[str]) -> Tuple[np.ndarray, dict]:
    """Merge a list of rasters into a single raster.

    Parameters
    ----------
    raster_list : List[str]
        List of paths to rasters to merge.

    Returns
    ----------
    mosaic : np.ndarray
        The merged raster data as a NumPy array.
    meta : dict
        Metadata for the merged raster, including driver, CRS, height, width, and transform.

    Examples
    --------
    >>> raster_list = ["raster1.tif", "raster2.tif", "raster3.tif"]
    >>> mosaic, meta = merge_rasters(raster_list)
    """

    with rasterio.open(raster_list[0]) as first_raster:
        with ExitStack() as stack:
            rasters = [first_raster] + [
                stack.enter_context(rasterio.open(raster)) for raster in raster_list[1:]
            ]
            mosaic, out_trans = merge(rasters)

            meta = first_raster.meta.copy()
            meta.update(
                {
                    "driver": "GTiff",
                    "crs": pyproj.CRS.from_epsg(3857),  # Web Mercator projection
                    "height": mosaic.shape[1],
                    "width": mosaic.shape[2],
                    "transform": out_trans,
                }
            )

    return mosaic, meta
