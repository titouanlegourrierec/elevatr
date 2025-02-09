# CHANGELOG

## [Unreleased]
### Added
- Add `to_obj` method to `Raster` class to convert the raster to a 3D object.

## 0.3.0 - 2025-01-08
### Added
- Ask for user confirmation before downloading large files.
- Add reprojection functionality to `get_elev_raster` function and `Raster` class.
- Added the ability to access the resolution of the raster through the `Raster` class via the `raster.resolution`
- Added the ability to access the imagery sources through the `Raster` class via the `raster.imagery_sources`
- Added two parameters to the `show` method of the `Raster` class: `show_extras` to control the display of additional elements, and `file_path` to specify the file path for saving the image.

## 0.2.0 - 2025-01-06
### Added
- Add clipping functionality to `get_elev_raster` function to clip the raster to the bounding box.

### Changed
- Improved documentation

### Fixed
- Update image links in README
- Removed unnecessary imports and path adjustments in examples.ipynb

## 0.1.0 - 2025-01-05
### Added
- Core features for fetching and processing elevation data for multiple resolutions.
- Raster class for handling raster data (show, save, convert to numpy array).
- Basic documentation and examples.
