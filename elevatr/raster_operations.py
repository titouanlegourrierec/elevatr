from contextlib import ExitStack
from typing import Any, Dict, List, Tuple

import numpy as np
import pyproj
import rasterio
from rasterio.merge import merge
from rasterio.windows import from_bounds

from .utils import convert_wgs84_bbox_to_web_mercator


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


def _clip_bbx(
    data: np.ndarray,
    meta: Dict[str, Any],
    bbx: Tuple[float, float, float, float],
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Clip a raster to a bounding box.

    Parameters
    ----------
    data : np.ndarray
        The raster data as a NumPy array.
    meta : dict
        Metadata for the raster, including driver, CRS, height, width, and transform.
    bbx : tuple
        A tuple representing the bounding box with coordinates (xmin, ymin, xmax, ymax).
        xmin and xmax are the minimum and maximum longitudes, ymin and ymax are the minimum and
        maximum latitudes.

    Returns
    ----------
    data : np.ndarray
        The clipped raster data as a NumPy array.
    meta : dict
        Metadata for the clipped raster, including driver, CRS, height, width, and transform.
    """

    with rasterio.io.MemoryFile() as memfile:
        with memfile.open(**meta) as dataset:
            dataset.write(data)

            web_mercator_bbox = convert_wgs84_bbox_to_web_mercator(bbx)

            # Calculate the window to clip
            window = from_bounds(*web_mercator_bbox, transform=dataset.transform)

            # Read the data in this window
            data = dataset.read(window=window)
            transform = dataset.window_transform(window)

    meta.update(transform=transform, height=data.shape[1], width=data.shape[2])

    return data, meta
