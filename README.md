# Drone Image Location Matcher

This repository contains a system for matching drone images with satellite imagery to determine the location where a drone image was captured. The system downloads satellite images for a set of coordinates, extracts visual features from both drone and satellite images, and compares them to find the best match.

## Overview

The drone image matching system is designed to solve the problem of identifying the precise location where a drone image was captured, given a set of potential coordinates. This is useful for:

- Verifying drone flight paths
- Locating unauthorized drone flights
- Rescue operations using drone imagery
- Mapping and surveying applications

## Key Features

- Download satellite imagery from Google Maps API
- Extract visual features (contours) from images
- Match drone images to satellite images using multiple matching algorithms
- Robust to differences in scale, rotation, and position
- Fast matching with simplified algorithm option

## Components

The system consists of several key components:

1. **Satellite Image Acquisition**: Downloads satellite imagery from Google Maps API
2. **Feature Extraction**: Processes images to identify key visual features
3. **Feature Matching**: Compares features between drone and satellite images
4. **Drone Image Matcher**: Orchestrates the entire matching process

## Matching Algorithms

The system provides three different matching approaches to balance speed and accuracy:

1. **Contour-based matching**: Fastest approach that compares individual contours between images. Works well for distinctive shapes but less robust to rotation and scale differences.

2. **Full holistic matching**: Most robust approach that finds the optimal transformation (scale, rotation, translation) to align drone and satellite images. Computationally intensive but handles all kinds of transformations.

3. **Simplified holistic matching (Recommended)**: A 10-20x faster variant of holistic matching that only tests translations (positions), not rotations or scales. Shows excellent results with 100% accuracy even with offset images (10m-100m) when the orientation is consistent.

## Quick Start

### Prerequisites

- Python 3.6+
- OpenCV
- NumPy
- Requests

Install dependencies:

```bash
pip install -r requirements.txt
```

### Basic Usage

1. Prepare a JSON file with potential coordinates:

```json
[
  {
    "lat": 51.6527061,
    "lon": -0.5245044,
    "description": "Location 1"
  },
  {
    "lat": 51.65279619,
    "lon": -0.5245044,
    "description": "Location 2"
  }
]
```

2. Run the simplified holistic matching (recommended for most use cases):

```bash
# Using the simplified wrapper script (easiest)
python match_drone_image.py --drone-image path/to/drone_image.jpg --coordinates path/to/coordinates.json

# Or directly with the component
cd backend/src/components/drone-image-matcher
python3 drone_image_matcher.py --drone-image path/to/drone_image.jpg --coordinates path/to/coordinates.json --simplify
```

3. View the results:

```
Best Match: {'lat': 51.6527061, 'lon': -0.5245044, 'description': 'Location 1'}
Score: 100.0
```

## Advanced Usage

### Command Line Options

The system supports multiple matching algorithms via the command line:

- **Contour-based matching**: Fast but less robust to rotation and scale differences
  ```bash
  python match_drone_image.py --drone-image path/to/drone_image.jpg --coordinates path/to/coordinates.json --contour
  ```

- **Full holistic matching**: Most robust but computationally intensive
  ```bash
  python match_drone_image.py --drone-image path/to/drone_image.jpg --coordinates path/to/coordinates.json --full
  ```

- **Simplified holistic matching**: Good balance of speed and accuracy (default)
  ```bash
  python match_drone_image.py --drone-image path/to/drone_image.jpg --coordinates path/to/coordinates.json
  ```

### Example Script

Check out the example script for a complete demonstration:

```bash
python examples/simplified_matching_example.py --drone-image path/to/drone_image.jpg
```

This example allows you to compare the speed and accuracy of simplified holistic matching with full holistic matching.

## Testing

The repository includes several testing scripts:

- `test_image_matcher.py`: Tests using satellite images as simulated drone images
- `test_offset_matching.py`: Tests with slightly offset coordinates

Run tests with:

```bash
python3 test_image_matcher.py --simplify
python3 test_offset_matching.py --simplify
```

## Documentation

For more detailed information, see:

- [System Architecture](docs/SYSTEM_ARCHITECTURE.md): Detailed explanation of system components
- [API Reference](docs/API_REFERENCE.md): Reference documentation for key functions and classes
- [Simplified Holistic Matching](docs/SIMPLIFIED_HOLISTIC_MATCHING.md): Comprehensive guide to the simplified matching approach
- [Usage Guide](docs/USAGE_GUIDE.md): Step-by-step usage instructions

## Performance Comparison

| Matching Method | Speed | Accuracy for Exact Matches | Robustness to Rotation | Robustness to Scale | Robustness to Position Offset |
|-----------------|-------|----------------------------|------------------------|---------------------|------------------------------|
| Contour-based   | Fast  | High                       | Low                    | Low                 | Medium                       |
| Holistic (Full) | Slow  | High                       | High                   | High                | High                         |
| Holistic (Simplified) | Medium | High                | Low                    | Low                 | High                         |

## License

This project is licensed under the MIT License - see the LICENSE file for details.
