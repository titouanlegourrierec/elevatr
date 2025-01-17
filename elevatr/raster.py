from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from mpl_toolkits.axes_grid1 import make_axes_locatable
from pyproj import CRS
from rasterio.plot import plotting_extent

from .raster_operations import _reproject_raster


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
    bounds: Optional[Tuple[float, float, float, float]] = field(init=False)
    resolution: Optional[Dict[str, Any]] = field(init=False)
    imagery_sources: Optional[str] = field(init=False)

    def __post_init__(self):
        """Post-initialization method."""
        self.data = self.data[0]
        self.crs = self.meta.get("crs", None)
        self.height = self.meta.get("height", None)
        self.width = self.meta.get("width", None)
        self.dtype = self.meta.get("dtype", None)
        self.nodata = self.meta.get("nodata", None)
        self.transform = self.meta.get("transform", None)
        self.bounds = (
            float(self.transform[2]),
            float(self.transform[5] + self.height * self.transform[4]),
            float(self.transform[2] + self.width * self.transform[0]),
            float(self.transform[5]),
        )
        self.resolution = self._resolution()
        self.imagery_sources = self.meta.get("imagery_sources", None)

    def _resolution(self) -> Dict[str, Any]:
        resolution = (abs(self.transform[0]), abs(self.transform[4]))  # type: ignore

        if self.crs:
            crs_obj = CRS.from_user_input(self.crs)
            resolution_unit = crs_obj.axis_info[0].unit_name
        else:
            resolution_unit = "unknown"

        return {"x": resolution[0], "y": resolution[1], "unit": resolution_unit}

    def show(
        self,
        cmap: Optional[str] = "viridis",
        figsize: Optional[tuple] = (10, 10),
        clip_zero: Optional[bool] = False,
        clip_color: Optional[str] = "white",
        show_extras: Optional[bool] = True,
        file_path: Optional[str] = None,
        **kwargs,
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
        show_extras : bool, optional
            Whether to show the colorbar and axis, by default True.
        file_path : str, optional
            The path to save the image to, by default None.
        **kwargs
            Additional keyword arguments to pass to `matplotlib.pyplot.imshow`.
        """

        data = np.where(self.data < 0, np.nan, self.data) if clip_zero else self.data

        cmap = plt.get_cmap(cmap) if isinstance(cmap, str) else cmap  # type: ignore
        if cmap is not None:
            cmap.set_bad(color=clip_color)  # type: ignore

        extent = plotting_extent(self.data, self.transform)
        fig, ax = plt.subplots(figsize=figsize)
        cax = ax.imshow(data, extent=extent, cmap=cmap, **kwargs)

        if show_extras:
            divider = make_axes_locatable(ax)
            cax_cb = divider.append_axes("right", size="3%", pad=0.05)
            fig.colorbar(cax, cax=cax_cb)
            ax.set_axis_on()
        else:  # pragma: no cover
            ax.axis("off")

        if file_path:  # pragma: no cover
            plt.savefig(file_path, bbox_inches="tight", pad_inches=0, dpi=300)

        plt.show()

    def to_numpy(self) -> np.ndarray:
        """Return the raster data as a NumPy array.

        Returns
        -------
        np.ndarray
            The raster data as a NumPy array.
        """
        return self.data

    def to_tif(self, path: str, compress: Optional[str] = None) -> None:
        """Write the raster data to a GeoTIFF file.

        Parameters
        ----------
        path : str
            The path to write the GeoTIFF file.
        compress : str, optional
            The compression type to use for the GeoTIFF file, by default None. Options are:

            - None: no compression
            - "lzw": Lempel-Ziv-Welch (LZW) compression, lossless, good for general use
            - "packbits": PackBits compression, simple and fast, but less efficient
            - "deflate": DEFLATE compression, lossless, balances speed and compression ratio
            - "zstd": Zstandard compression, lossless, high compression ratio and fast decompression
            - "lzma": LZMA compression, lossless, very high compression ratio but slower
        """
        valid_compressions = [None, "lzw", "packbits", "deflate", "zstd", "lzma"]
        if compress not in valid_compressions:
            raise ValueError(f"Invalid compression type: {compress}. Valid options are {valid_compressions}")

        self.meta.update(compress=compress)
        with rasterio.open(path, "w", **self.meta) as dst:
            dst.write(self.data, 1)

    def reproject(self, crs: str) -> None:
        """
        Reproject raster data to the desired CRS.

        Parameters
        ----------
        crs : str
            The target coordinate reference system (CRS) to reproject the raster to.

        Notes
        -----
        This method updates the class attributes in place. The original raster data is overwritten.
        """
        if self.crs != crs:
            self.data, self.meta = _reproject_raster(self.data, self.meta, crs)

            # Update the class attributes
            self.crs = self.meta["crs"]
            self.transform = self.meta["transform"]
            self.height, self.width = self.meta["height"], self.meta["width"]
            self.bounds = (
                float(self.transform[2]),
                float(self.transform[5] + self.height * self.transform[4]),
                float(self.transform[2] + self.width * self.transform[0]),
                float(self.transform[5]),
            )
            self.resolution = self._resolution()

    def to_obj(
        self,
        output_path: str,
        clip_zero: bool = False,
        zscale: float = 1.0,
        reduce_quality: int = 1,
        solid: bool = False,
        texture_path: Optional[str] = None,
    ):
        """
        Write the raster data to an OBJ file.

        Parameters
        ----------
        output_path : str
            The path to write the OBJ file.
        clip_zero : bool, optional
            Whether to clip negative values to zero (sea level), by default False.
        zscale : float, optional
            The scaling factor to apply to the z-axis. Decrease to attenuate elevation and increase
            to accentuate it, by default 1.0.
        reduce_quality : int, optional
            The factor to reduce the quality of the mesh. Increase this integer value (greater than 1)
            to reduce the quality, by default 1.
        solid : bool, optional
            Whether to add a base below the surface to create a solid object, by default False.
        texture_path : str, optional
            The path to the texture image file, by default None.
        """
        if clip_zero:
            data = np.where(self.data < 0, np.nan, self.data)
        else:
            data = self.data

        height, width = data.shape
        min_z = np.nanmin(data) * zscale if solid else 0  # Minimum z-value

        with open(output_path, "w") as f:
            # Write vertices
            for y in range(0, height, reduce_quality):
                for x in range(0, width, reduce_quality):
                    z = data[y, x] * zscale
                    if np.isnan(z):
                        z = 0  # Handle NaN values
                    f.write(f"v {x} {height - 1 - y} {z}\n")  # Invert y-axis

            if solid:
                # Write base vertices
                for y in range(0, height, reduce_quality):
                    for x in range(0, width, reduce_quality):
                        f.write(f"v {x} {height - 1 - y} {min_z}\n")  # Base vertex

            # Write texture coordinates if texture_path is provided
            if texture_path:
                for y in range(0, height, reduce_quality):
                    for x in range(0, width, reduce_quality):
                        u = x / (width - 1)
                        v = (height - 1 - y) / (height - 1)
                        f.write(f"vt {u} {v}\n")

            # Write faces
            for y in range(0, height - reduce_quality, reduce_quality):
                for x in range(0, width - reduce_quality, reduce_quality):
                    v1 = (y // reduce_quality) * (width // reduce_quality) + (x // reduce_quality) + 1
                    v2 = v1 + 1
                    v3 = v1 + (width // reduce_quality)
                    v4 = v3 + 1
                    if texture_path:
                        f.write(f"f {v1}/{v1} {v3}/{v3} {v4}/{v4} {v2}/{v2}\n")
                    else:
                        f.write(f"f {v1} {v3} {v4} {v2}\n")

            if solid:
                base_offset = (height // reduce_quality) * (width // reduce_quality)
                # Write side faces
                for y in range(0, height - reduce_quality, reduce_quality):
                    for x in range(0, width - reduce_quality, reduce_quality):
                        v1 = (y // reduce_quality) * (width // reduce_quality) + (x // reduce_quality) + 1
                        v2 = v1 + 1
                        v3 = v1 + (width // reduce_quality)
                        v4 = v3 + 1
                        bv1 = v1 + base_offset
                        bv2 = v2 + base_offset
                        bv3 = v3 + base_offset
                        bv4 = v4 + base_offset
                        f.write(f"f {v1} {v2} {bv2} {bv1}\n")
                        f.write(f"f {v2} {v4} {bv4} {bv2}\n")
                        f.write(f"f {v4} {v3} {bv3} {bv4}\n")
                        f.write(f"f {v3} {v1} {bv1} {bv3}\n")

                # Write bottom face
                bottom_vertices = [
                    (0, 0),
                    (width - reduce_quality, 0),
                    (width - reduce_quality, height - reduce_quality),
                    (0, height - reduce_quality),
                ]
                bottom_indices = [
                    (y // reduce_quality) * (width // reduce_quality)
                    + (x // reduce_quality)
                    + 1
                    + base_offset
                    for x, y in bottom_vertices
                ]
                f.write(f"f {' '.join(map(str, bottom_indices))}\n")

        # Write the material file if texture_path is provided
        if texture_path:
            mtl_path = output_path.replace(".obj", ".mtl")
            with open(mtl_path, "w") as mtl_file:
                mtl_file.write("newmtl material_0\n")
                mtl_file.write(f"map_Kd {texture_path}\n")
            with open(output_path, "a") as f:
                f.write(f"mtllib {mtl_path}\n")
