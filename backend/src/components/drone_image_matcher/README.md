# Drone Image Matcher

This component matches drone images with satellite images to find the most likely location of a drone image by comparing features extracted from both types of images.

## Overview

The Drone Image Matcher works by:

1. Taking a drone image and a set of potential coordinates
2. Downloading satellite images for each of those coordinates using Google Maps Static API
3. Extracting contour features from both the drone image and satellite images
4. Matching these features to determine which satellite image (and thus which coordinate) most closely matches the drone image
5. Returning results ranked by match score

## Components Used

This module integrates several other components:

- **get-map-image**: Downloads satellite images for given coordinates
- **contour_extractor**: Extracts contour features from images
- **contour_matcher**: Matches contour features between images to find the best match

## Usage

### Command Line

```bash
python drone_image_matcher.py --drone-image PATH_TO_DRONE_IMAGE --coordinates PATH_TO_COORDINATES_JSON [--output OUTPUT_DIR] [--api-key API_KEY]
```

Arguments:
- `--drone-image`, `-d`: Path to the drone image (required)
- `--coordinates`, `-c`: Path to JSON file with coordinates (required)
- `--output`, `-o`: Directory to save satellite images (optional)
- `--api-key`, `-k`: Google Maps API key (optional, will use the one from get-map-image if not provided)

### Coordinates JSON Format

The coordinates JSON file should contain a list of coordinates in the following format:

```json
[
  {
    "lat": 51.6794221,
    "lon": -0.5319316
  },
  {
    "lat": 51.6485691,
    "lon": -0.5238954
  },
  ...
]
```

### Example

```bash
python drone_image_matcher.py --drone-image examples/drone_shot.jpg --coordinates examples/potential_locations.json --output ./output
```

## Example Data

The component includes several example coordinate files:

- `example_coordinates.json`: Sample coordinates covering Rickmansworth and Reading areas (widely spaced)
- `nearby_coordinates.json`: Closely-spaced coordinates around Rickmansworth Park (within ~500m)
- `reading_university_coordinates.json`: Closely-spaced coordinates around Reading University (within ~500m)
- `examples/`: Directory where you can place drone images for testing

These coordinate sets serve different testing purposes:
- Use `example_coordinates.json` to test matching across very different locations
- Use `nearby_coordinates.json` or `reading_university_coordinates.json` to test precision in distinguishing between very similar nearby locations

Note: You will need to provide your own drone images for testing. Ideal test images would be aerial photos taken at approximately 120m altitude with visible landscape features like roads, buildings, and natural elements.

## API

You can also use the DroneImageMatcher class programmatically:

```python
from drone_image_matcher import DroneImageMatcher

# Initialize the matcher
matcher = DroneImageMatcher(output_dir="./output")

# Define drone image path and coordinates
drone_image_path = "path/to/drone_image.jpg"
coordinates = [
    {"lat": 51.6794221, "lon": -0.5319316},
    {"lat": 51.6485691, "lon": -0.5238954},
    # ...
]

# Find the best match
result = matcher.find_best_match(drone_image_path, coordinates)

# Access the results
best_match = result["best_match"]
print(f"Best matching coordinates: {best_match['coordinates']}")
print(f"Match score: {best_match['score']}")
```

## Requirements

- Python 3.6+
- OpenCV
- NumPy
- Requests

## Dependencies

Make sure you have the required components and their dependencies installed:

- get-map-image
- contour_extractor
- contour_matcher

## Notes

- The matching process may take some time depending on the number of coordinates and the complexity of the images.
- The quality of matches depends on the distinctiveness of features in the images.
- Satellite images from Google Maps may have different lighting conditions, seasons, or dates compared to drone images, which can affect matching results.
- When testing with nearby coordinates (e.g., `nearby_coordinates.json`), the algorithm should be able to identify subtle differences between locations that are just a few hundred meters apart. 