# Contour Extraction Component

This component is responsible for extracting contours from both drone and satellite images. 
It serves as the first part of the original Contour Matching Agent from the system design.

## Purpose

Extract well-defined contours from images that can be used for subsequent alignment and matching by the Rotation Normalization Agent.

## Installation

```bash
# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

## Running Tests

There are two test scripts available:

### 1. Basic Single-Image Test

Tests contour extraction on a single drone image and a single satellite image:

```bash
python3 test_contour_extractor.py --drone-image "PATH_TO_DRONE_IMAGE" --satellite-image "PATH_TO_SATELLITE_IMAGE" --output-dir ./output
```

Example using the competition images:

```bash
python3 test_contour_extractor.py --drone-image "../../../Competition Release/Reading_1_cleaned.jpg" --satellite-image "../../../Competition Release/Reading_1_cleaned.jpg" --output-dir ./output
```

Parameters:
- `--drone-image`: Path to the drone image
- `--satellite-image`: Path to the satellite image
- `--output-dir`: Directory to save visualizations and output JSON (default: ./output)
- `--min-length`: Minimum contour length in pixels (default: 150)
- `--canny-low`: Lower threshold for Canny edge detector (default: 100)
- `--canny-high`: Upper threshold for Canny edge detector (default: 200)

### 2. Multi-Image Test

Tests contour extraction on one drone image and multiple satellite images:

```bash
python3 multi_image_test.py
```

This script:
- Uses Reading_1_cleaned.jpg as the drone image
- Uses Reading_1 through Reading_4 as satellite images
- Saves all output to the ./multi_output directory

You can modify the paths in the script to use different images.

## How It Works

The contour extraction process works as follows:

1. **Image Preprocessing**:
   - Convert image to grayscale
   - Apply Gaussian blur to reduce noise
   - Apply Canny edge detection to find edges

2. **Contour Extraction**:
   - Use OpenCV's `findContours` function to extract contours from edges
   - Filter contours based on minimum length

3. **Output Generation**:
   - Format contours as JSON objects with points and metadata
   - Generate visualization images showing contours
   - Create a structured JSON output with all contours

## Output Format

The component outputs a JSON file with the following structure:

```json
{
  "image_id": "string",
  "drone_contours": [
    {
      "points": [[x1, y1], [x2, y2], ...],
      "length": float
    }
  ],
  "satellite_contours": [
    {
      "area_id": "string",
      "contours": [
        {
          "points": [[x1, y1], [x2, y2], ...],
          "length": float
        }
      ],
      "bounds": [minx, miny, maxx, maxy]
    }
  ]
}
```

## Visualization

The component generates visualization images showing the extracted contours:
- For single-image tests: `output/drone_contours.png` and `output/satellite_contours.png`
- For multi-image tests: `multi_output/drone_contours.png` and `multi_output/satellite_contours_area_X.png`

## Troubleshooting

- If you see "No module named 'cv2'" error, run `pip install -r requirements.txt`
- If images aren't found, check the paths and make sure they're accessible
- For poor contour quality, try adjusting the Canny thresholds and minimum contour length

## Todo List

- [x] Set up Python environment with required dependencies
- [x] Implement basic image preprocessing (Canny edge detection)
- [x] Extract contours from drone images
- [x] Extract contours from satellite images
- [x] Filter contours by length and quality
- [x] Format contours in JSON for the Rotation Normalization Agent
- [x] Add visualization tools for debugging
- [x] Write tests for contour extraction

## Known Issues

- High computational cost for multiple areas
- Noisy contours due to low image contrast
- Scale differences between drone and satellite images

## References

- [OpenCV Contours Documentation](https://docs.opencv.org/4.x/d4/d73/tutorial_py_contours_begin.html)
- [Canny Edge Detection](https://docs.opencv.org/4.x/da/d22/tutorial_py_canny.html) 