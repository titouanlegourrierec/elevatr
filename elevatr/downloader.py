# Copyright (c) 2025 Titouan Le Gourrierec
"""Module for downloading terrain tiles from AWS S3."""

import logging
from pathlib import Path
from urllib.parse import urlparse

import rasterio
import requests
from tqdm import tqdm

from .utils import _get_tile_xy


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


BASE_URL = "https://s3.amazonaws.com/elevation-tiles-prod/geotiff"
CHUNCK_SIZE = 8192


def _get_aws_terrain(
    bbx: tuple[float, float, float, float],
    zoom: int,
    cache_folder: str | Path,
    *,
    use_cache: bool,
    verbose: bool,
) -> list[str]:
    """
    Download terrain tiles of a specified zoom level within a bounding box from AWS.

    Args:
        bbx (tuple): A tuple representing the bounding box with coordinates (xmin, ymin, xmax, ymax).
            xmin and xmax are the minimum and maximum longitudes, ymin and ymax are the minimum and maximum latitudes.
        zoom (int): Zoom level, a integer between 0 and 14 where higher values correspond to more detailed tiles.
        cache_folder (str | Path): Path to the folder where tiles will be cached.
        use_cache (bool): If True, use cached tiles if they exist.
        verbose (bool): If True, display progress information.

    Returns:
        list[str]: List of filepaths to the downloaded tiles.

    """

    def _construct_tile_filename(url: str) -> str:
        """
        Generate a cache-friendly filename from a tile URL.

        Args:
            url (str): The URL of the tile.

        Returns:
            str: The constructed filepath for caching the tile.

        """
        parsed_url = urlparse(url)
        path_segments = parsed_url.path.split("/")
        filename = f"{path_segments[-4]}_{path_segments[-3]}_{path_segments[-2]}_{Path(url).name}"
        return str(Path(cache_folder) / filename)

    def _download_tile(url: str, destination: str) -> str:
        """
        Download a tile if it doesn't already exist locally.

        Args:
            url (str): The URL of the tile to download.
            destination (str): The local filepath where the tile will be saved.

        Returns:
            str: The filepath of the downloaded tile.

        Raises:
            RuntimeError: If the download fails.
            ValueError: If the downloaded file is not a valid TIF.

        """
        try:
            with requests.get(url, stream=True, timeout=10) as response:
                response.raise_for_status()
                if "image/tif" not in response.headers.get("Content-Type", ""):
                    msg = f"Invalid file type for URL {url}"
                    raise ValueError(msg)

                imagery_sources = response.headers.get("x-amz-meta-x-imagery-sources", "")
                imagery_sources_set = {source.split("/")[0].strip() for source in imagery_sources.split(",")}

                Path(Path(destination).parent).mkdir(exist_ok=True, parents=True)
                with Path(destination).open("wb") as file:
                    file.writelines(response.iter_content(chunk_size=CHUNCK_SIZE))

                # Update the TIF file metadata with imagery sources
                with rasterio.open(destination, "r+") as dataset:
                    metadata = dataset.meta.copy()
                    metadata.update({"imagery_sources": ", ".join(sorted(imagery_sources_set))})
                    dataset.update_tags(**metadata)

        except requests.RequestException as e:
            msg = f"Failed to download {url}: {e}"
            raise RuntimeError(msg) from e
        else:
            return destination

    def _filter_cached_and_uncached(urls: list[str]) -> tuple[list[str], list[str]]:
        """
        Separate cached and uncached tile URLs.

        Args:
            urls (list[str]): List of tile URLs.

        Returns:
            tuple[list[str], list[str]]: A tuple containing two lists - cached filepaths and uncached URLs.

        """
        cached, uncached = [], []
        for url in urls:
            filepath = _construct_tile_filename(url)
            if Path(filepath).exists() and use_cache:
                cached.append(filepath)
            else:
                uncached.append(url)
        return cached, uncached

    # Define the base URL and assemble tile URLs
    tiles_df = _get_tile_xy(bbx, zoom)
    urls = [f"{BASE_URL}/{zoom}/{tile.tile_x}/{tile.tile_y}.tif" for tile in tiles_df.to_records(index=False)]

    # Separate cached and uncached tiles
    cached_files, uncached_urls = _filter_cached_and_uncached(urls)

    if not uncached_urls:
        if verbose:
            logger.info("All tiles retrieved from cache.")
        return cached_files

    # Download uncached tiles
    downloaded_tiles = cached_files
    if verbose:
        uncached_urls = tqdm(uncached_urls, desc="Downloading tiles")
    for url in uncached_urls:
        filepath = _construct_tile_filename(url)
        downloaded_tiles.append(_download_tile(url, filepath))

    return downloaded_tiles
