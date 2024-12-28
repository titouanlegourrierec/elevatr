import os
from typing import Dict, List, Tuple
from urllib.parse import urlparse

import requests  # type: ignore
from tqdm import tqdm

from .utils import _get_tile_xy

BASE_URL = "https://s3.amazonaws.com/elevation-tiles-prod/geotiff"
CHUNCK_SIZE = 8192


def _get_aws_terrain(
    bbx: Dict[str, float],
    zoom: int,
    cache_folder: str,
    use_cache: bool,
    verbose: bool,
) -> List[str]:
    """
    Download terrain tiles of a specified zoom level within a bounding box from AWS.

    Parameters
    ----------
    bbx : dict
        A dictionary representing the bounding box with keys 'xmin', 'xmax', 'ymin', and 'ymax'.
        - 'xmin' : float
            Minimum longitude of the bounding box.
        - 'xmax' : float
            Maximum longitude of the bounding box.
        - 'ymin' : float
            Minimum latitude of the bounding box.
        - 'ymax' : float
            Maximum latitude of the bounding box.
    zoom : int
        Zoom level, a non-negative integer where higher values correspond to more detailed tiles.
    cache_folder : str
        Path to the folder where tiles will be cached.
    use_cache : bool
        If True, use cached tiles if they exist.
    verbose : bool
    """

    def _construct_tile_filename(url: str) -> str:
        """Generate a cache-friendly filename from a tile URL."""
        parsed_url = urlparse(url)
        path_segments = parsed_url.path.split("/")
        filename = f"{path_segments[-4]}_{path_segments[-3]}_{path_segments[-2]}_{os.path.basename(url)}"
        return os.path.join(cache_folder, filename)

    def _download_tile(url: str, destination: str) -> str:
        """Download a tile if it doesn't already exist locally."""
        try:
            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                if "image/tif" not in response.headers.get("Content-Type", ""):
                    raise ValueError(f"Invalid file type for URL {url}")

                os.makedirs(os.path.dirname(destination), exist_ok=True)
                with open(destination, "wb") as file:
                    for chunk in response.iter_content(chunk_size=CHUNCK_SIZE):
                        file.write(chunk)
            return destination
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to download {url}: {e}")

    def _filter_cached_and_uncached(urls: List[str]) -> Tuple[List[str], List[str]]:
        """Separate cached and uncached tile URLs."""
        cached, uncached = [], []
        for url in urls:
            filepath = _construct_tile_filename(url)
            if os.path.exists(filepath) and use_cache:
                cached.append(filepath)
            else:
                uncached.append(url)
        return cached, uncached

    # Define the base URL and assemble tile URLs
    tiles_df = _get_tile_xy(bbx, zoom)
    urls = [
        f"{BASE_URL}/{zoom}/{tile.tile_x}/{tile.tile_y}.tif"
        for tile in tiles_df.to_records(index=False)
    ]

    # Separate cached and uncached tiles
    cached_files, uncached_urls = _filter_cached_and_uncached(urls)

    if not uncached_urls:
        if verbose:
            print("All tiles retrieved from cache.")
        return cached_files

    # Download uncached tiles
    downloaded_tiles = cached_files
    if verbose:
        uncached_urls = tqdm(uncached_urls, desc="Downloading tiles")
    for url in uncached_urls:
        filepath = _construct_tile_filename(url)
        downloaded_tiles.append(_download_tile(url, filepath))

    return downloaded_tiles
