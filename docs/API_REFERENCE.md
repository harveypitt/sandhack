# API Reference

This document provides reference documentation for the key classes and methods in the drone image matching system.

## Components

### DroneImageMatcher

Main class for coordinating the image matching process.

#### Constructor

```python
DroneImageMatcher(output_dir=None, api_key=None, use_holistic=True, simplify=False)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `output_dir` | str | Directory to store satellite images |
| `api_key` | str | Google Maps API key |
| `use_holistic` | bool | Whether to use holistic matching (True) or contour matching (False) |
| `simplify` | bool | Whether to disable scale and rotation transformations in holistic matching |

#### Methods

##### download_satellite_images

```python
download_satellite_images(coordinates: List[Dict[str, float]]) -> List[str]
```

Downloads satellite images for a list of coordinates.

| Parameter | Type | Description |
|-----------|------|-------------|
| `coordinates` | List[Dict] | List of coordinate dictionaries with 'lat' and 'lon' keys |
| **Returns** | List[str] | List of paths to downloaded satellite images |

##### extract_features

```python
extract_features(image_path: str) -> Dict
```

Extracts features from an image using the contour extractor.

| Parameter | Type | Description |
|-----------|------|-------------|
| `image_path` | str | Path to the image |
| **Returns** | Dict | Extracted features including contours |

##### match_features

```python
match_features(drone_features: Dict, satellite_features: List[Dict]) -> List[Tuple[int, float]]
```

Matches features between a drone image and multiple satellite images.

| Parameter | Type | Description |
|-----------|------|-------------|
| `drone_features` | Dict | Features extracted from the drone image |
| `satellite_features` | List[Dict] | List of features extracted from satellite images |
| **Returns** | List[Tuple[int, float]] | List of (index, score) tuples sorted by score |

##### find_best_match

```python
find_best_match(drone_image_path: str, coordinates: List[Dict[str, float]]) -> Dict
```

Finds the best matching satellite image for a drone image.

| Parameter | Type | Description |
|-----------|------|-------------|
| `drone_image_path` | str | Path to the drone image |
| `coordinates` | List[Dict] | List of coordinate dictionaries with 'lat' and 'lon' keys |
| **Returns** | Dict | Best match result with coordinates, score, and paths |

### ContourExtractor

Class for extracting contours from images.

#### Constructor

```python
ContourExtractor()
```

#### Methods

##### extract_contours

```python
extract_contours(image_input, threshold=50)
```

Extracts contours from an image.

| Parameter | Type | Description |
|-----------|------|-------------|
| `image_input` | str or np.ndarray | Path to the input image or the image data |
| `threshold` | int | Contour detection threshold (0-100) |
| **Returns** | dict | Dictionary containing original image, contours, visualization |

### ContourMatcher

Class for matching contours between images using shape-based approaches.

#### Constructor

```python
ContourMatcher()
```

#### Methods

##### match_contours

```python
match_contours(drone_image_path, satellite_image_paths, threshold=50)
```

Matches contours between a drone image and multiple satellite images.

| Parameter | Type | Description |
|-----------|------|-------------|
| `drone_image_path` | str | Path to the drone image |
| `satellite_image_paths` | list | List of paths to satellite images |
| `threshold` | int | Contour detection threshold (0-100) |
| **Returns** | dict | Match results including scores and visualizations |

##### _compute_contour_similarity

```python
_compute_contour_similarity(drone_contours, sat_contours)
```

Computes similarity score between two sets of contours.

| Parameter | Type | Description |
|-----------|------|-------------|
| `drone_contours` | list | Drone contours |
| `sat_contours` | list | Satellite contours |
| **Returns** | float | Similarity score (0-100) |

### HolisticMatcher

Class for matching contours using a holistic pattern-based approach.

#### Constructor

```python
HolisticMatcher(logger=None)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `logger` | logging.Logger | Optional logger for debugging information |

#### Methods

##### match_contours

```python
match_contours(drone_contours, satellite_contours_list, **kwargs)
```

Matches drone contours against multiple satellite contour sets using holistic matching.

| Parameter | Type | Description |
|-----------|------|-------------|
| `drone_contours` | list | List of contours from the drone image |
| `satellite_contours_list` | list | List of lists of contours from satellite images |
| `**kwargs` | dict | Additional parameters for matching |
| `min_scale` | float | Minimum scale factor to try (default: 0.5) |
| `max_scale` | float | Maximum scale factor to try (default: 2.0) |
| `scale_steps` | int | Number of scale steps to try (default: 10) |
| `angle_step` | float | Step size for rotation angles in degrees (default: 10) |
| `translation_range` | int | Range for translation in pixels (default: 50) |
| `translation_step` | int | Step size for translation (default: 10) |
| `simplify` | bool | Whether to disable scale and rotation transformations (default: False) |
| **Returns** | list | List of (index, score) tuples sorted by score |

##### _find_best_transformation

```python
_find_best_transformation(drone_img, satellite_img, 
                         min_scale=0.5, max_scale=2.0, scale_steps=10,
                         angle_step=10.0, translation_range=50, translation_step=10,
                         simplify=False)
```

Finds the best transformation parameters to align drone image with satellite image.

| Parameter | Type | Description |
|-----------|------|-------------|
| `drone_img` | np.ndarray | Binary image with drone contours |
| `satellite_img` | np.ndarray | Binary image with satellite contours |
| `min_scale` | float | Minimum scale factor to try |
| `max_scale` | float | Maximum scale factor to try |
| `scale_steps` | int | Number of scale steps to try |
| `angle_step` | float | Step size for rotation angles in degrees |
| `translation_range` | int | Range for translation in pixels |
| `translation_step` | int | Step size for translation |
| `simplify` | bool | Whether to disable scale and rotation transformations |
| **Returns** | tuple | (best_scale, best_angle, best_iou, best_tx, best_ty, total_comparisons) |

## Command-Line Scripts

### drone_image_matcher.py

Main script for matching drone images with satellite images.

#### Usage

```
python3 drone_image_matcher.py --drone-image PATH --coordinates PATH [--output DIR] [--api-key KEY] [--use-contour] [--simplify]
```

| Argument | Description |
|----------|-------------|
| `--drone-image`, `-d` | Path to the drone image |
| `--coordinates`, `-c` | Path to JSON file with coordinates |
| `--output`, `-o` | Directory to save satellite images |
| `--api-key`, `-k` | Google Maps API key |
| `--use-contour` | Use contour matching instead of holistic matching |
| `--simplify` | Disable scale and rotation transformations in holistic matching |

### test_image_matcher.py

Script for testing the matcher using satellite images as simulated drone images.

#### Usage

```
python3 test_image_matcher.py [--use-contour] [--compare-methods] [--simplify]
```

| Argument | Description |
|----------|-------------|
| `--use-contour` | Use contour matching instead of holistic matching |
| `--compare-methods` | Run tests with both matching methods |
| `--simplify` | Disable scale and rotation transformations in holistic matching |

### test_offset_matching.py

Script for testing the matcher with slightly offset coordinates.

#### Usage

```
python3 test_offset_matching.py [--coordinate-file PATH] [--test-image-dir DIR] [--use-contour] [--compare-methods] [--simplify]
```

| Argument | Description |
|----------|-------------|
| `--coordinate-file` | JSON file with offset coordinates |
| `--test-image-dir` | Directory to store downloaded test images |
| `--use-contour` | Use contour matching instead of holistic matching |
| `--compare-methods` | Run tests with both matching methods |
| `--simplify` | Disable scale and rotation transformations in holistic matching | 