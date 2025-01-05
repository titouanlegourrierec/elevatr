from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from mpl_toolkits.axes_grid1 import make_axes_locatable
from rasterio.plot import plotting_extent


@dataclass
class Raster:
    """A class to manage raster data."""

    data: np.ndarray
    meta: Dict[str, Any]
    driver: str = field(init=False, default="GTiff")
    crs: Optional[Any] = field(init=False)
    height: Optional[int] = field(init=False)
    width: Optional[int] = field(init=False)
    count: int = field(init=False, default=1)
    dtype: Optional[str] = field(init=False)
    nodata: Optional[Any] = field(init=False)
    transform: Optional[Any] = field(init=False)

    def __post_init__(self):
        """Post-initialization method."""
        self.data = self.data[0]
        self.crs = self.meta.get("crs", None)
        self.height = self.meta.get("height", None)
        self.width = self.meta.get("width", None)
        self.dtype = self.meta.get("dtype", None)
        self.nodata = self.meta.get("nodata", None)
        self.transform = self.meta.get("transform", None)

    def show(
        self,
        cmap: Optional[str] = "viridis",
        figsize: Optional[tuple] = (10, 10),
        clip_zero: Optional[bool] = False,
        clip_color: Optional[str] = "white",
        **kwargs
    ) -> None:
        """Display the raster data as an image.

        Parameters
        ----------
        cmap : str, optional
            The colormap to use for the image, by default "viridis".
        figsize : tuple, optional
            The size of the figure, by default (10, 10).
        clip_zero : bool, optional
            Whether to clip negative values to zero, by default False.
        clip_color : str, optional
            The color to use for clipped values, by default "white".
        **kwargs
            Additional keyword arguments to pass to `matplotlib.pyplot.imshow`.
        """

        data = np.where(self.data < 0, np.nan, self.data) if clip_zero else self.data

        cmap = plt.get_cmap(cmap) if isinstance(cmap, str) else cmap
        if cmap is not None:
            cmap.set_bad(color=clip_color)

        extent = plotting_extent(self.data, self.transform)
        fig, ax = plt.subplots(figsize=figsize)
        cax = ax.imshow(data, extent=extent, cmap=cmap, **kwargs)

        divider = make_axes_locatable(ax)
        cax_cb = divider.append_axes("right", size="3%", pad=0.05)
        fig.colorbar(cax, cax=cax_cb)

        plt.show()

    def to_numpy(self) -> np.ndarray:
        """Return the raster data as a NumPy array.

        Returns
        -------
        np.ndarray
            The raster data as a NumPy array.
        """
        return self.data

    def to_tif(self, path: str) -> None:
        """Write the raster data to a GeoTIFF file.

        Parameters
        ----------
        path : str
            The path to write the GeoTIFF file.
        """
        with rasterio.open(path, "w", **self.meta) as dst:
            dst.write(self.data, 1)
