__author__ = "Titouan Le Gourrierec"
__email__ = "titouanlegourrierec@icloud.com"
__license__ = "MIT"
__description__ = (
    "A Python package to simplify downloading and processing elevation data."
)


from ._version import __version__  # noqa F401
from .get_elev_raster import get_elev_raster
from .raster import Raster  # noqa F401

__all__ = ["get_elev_raster"]
