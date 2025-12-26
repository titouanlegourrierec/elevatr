# Copyright (c) 2025 Titouan Le Gourrierec
"""elevatr - A Python package to simplify downloading and processing elevation data."""

__author__ = "Titouan Le Gourrierec"
__email__ = "titouanlegourrierec@icloud.com"
__license__ = "MIT"
__description__ = "A Python package to simplify downloading and processing elevation data."


from importlib.metadata import version

from . import settings
from .get_elev_raster import get_elev_raster
from .raster import Raster


__version__ = version(__name__)

__all__ = ["Raster", "get_elev_raster", "settings"]
