# Location Estimation App

A web application for estimating locations from images using computer vision and LLM analysis.

## Project Structure

The project is organized into two main components:

- **Backend**: A FastAPI service that processes images and returns location estimations
- **Frontend**: A React/TypeScript web interface for uploading images and displaying results

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js (for local frontend development)
- Python 3.10+ (for local backend development)

### Running with Docker Compose

The easiest way to run the application is using Docker Compose:

```bash
# Build and start all services
docker-compose up --build

# Access the application at http://localhost
```

### Local Development

#### Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
uvicorn app:app --reload
```

The API will be available at http://localhost:8000 with automatic documentation at http://localhost:8000/docs

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at http://localhost:5173

## API Endpoints

### Basic Endpoints

#### `GET /`

Health check endpoint that returns status information.

#### `POST /analyze` (deprecated)

Legacy endpoint. Use `/llm-analysis/analyze` instead.

### LLM Analysis Endpoints

#### `POST /llm-analysis/analyze`

Analyzes an uploaded image and returns location estimation using LLM.

**Parameters:**
- `file`: The image file to analyze (form data)
- `global_mode`: Whether to use global analysis mode (default: false for UK-specific)

**Response:**
```json
{
  "estimated-location": "Reading, UK",
  "confidence": 0.85,
  "visual-features": ["red brick buildings", "train station", "river"],
  "matching-regions": ["Reading Town Center", "Reading University Campus"]
}
```

### Contour Analysis Endpoints

#### `POST /contour/extract`

Extracts contours from an uploaded image.

**Parameters:**
- `file`: The image file to analyze (form data)
- `threshold`: Contour detection threshold 0-100 (form data)

#### `POST /contour/match`

Matches contours between a drone image and satellite images.

**Parameters:**
- `drone_image`: Drone image file (form data)
- `satellite_images`: Up to 4 satellite image files (form data)
- `threshold`: Contour detection threshold 0-100 (form data)

For detailed information about contour analysis, see [CONTOUR_ANALYSIS_USAGE.md](CONTOUR_ANALYSIS_USAGE.md).

## Frontend Features

- Image upload and preview
- Option to toggle between UK-specific and global analysis modes
- Display of analysis results including estimated location, confidence, and visual features
- Contour extraction and matching for location estimation
- Responsive design for desktop and mobile devices

## Documentation

- [LLM Analyzer Usage](LLM_ANALYZER_USAGE.md) - Guide for using the LLM analysis features
- [Contour Analysis Usage](CONTOUR_ANALYSIS_USAGE.md) - Guide for using the contour analysis features

# 25-LDTH-Relocalisation
Repo for Arondite's Relocalisation with Multi-scale Feature Matching challenge.

## Problem
In a contested environment, GPS is not a reliable navigation method. There are several approaches to mitigate this; one is to use pre-
loaded satellite imagery to localise against the ground you can see.

We have provided you with a set of aerial photos taken by UAVs. Your challenge is to figure out the the WSG84 coordinates of 
the drone when each photo was taken. Given the difficulty of this challenge, we will provide WSG84 box area hints, in the format of FeatureCollections, alongside the 
images.

To achieve this, we suggest that you can try either classical or DL/ML based approaches (or both together) to match visual features 
present in the images with features visible in aerial images/photograpy; but we'd be delighted to see more creative solutions as well.
Contestants will be evaluated based on the error (distance calculated by Haversine) between the true and predicted WSG84 coordinates for a set of validation images.

## Setup
Run `uv sync`. If you don't have uv on your computer, you can find installation instructions [here](https://github.com/astral-sh/uv). We'd generally recommend using it for this project as it's lightweight and easy to manage! Feel free to add whatever libraries you need.

## Data
Under `data/example/images`, there's:
1. An example image, `rickmansworth_example.png`
1. The area in which to search for the image, `rickmansworth_example_search_area.json`, in GeoJSON FeatureCollection format

The test set of images will follow this format, a flat directory structure with `X.png` and `X_search_area.json`. 

**All drone images are taken from an altitude of between 110m and 120m**.

Arondite will make the full test set of drone images available at 10am on Saturday; further details on this will follow as a PR in this repo.

For satellite data, we've provided a helper function under `src/utility/get_satellite_image.py` which queries the [Copernicus VHR Image Mosaic](https://land.copernicus.eu/en/products/european-image-mosaic/very-high-resolution-image-mosaic-2021-true-colour-2m) using a bounding box in `EPSG:3035` format. We've also provided a helper function in `src/utility/epsg_4326_to_3035.py` that can read in a FeatureCollection bounds box in `EPSG:4326` format (i.e. the `_search_area.json` files) and convert it into the relevant format.

## Evaluating
If you take a look at `data/example`, you'll see two `.csv` files: `estimations.csv` and `truth.csv`. The output of your code should be an `estimations.csv` file with guesses in a simple `id | latitude | longitude` format, which is then compared against a `truth.csv` by ID.

We've provided a `run_eval.sh` script, which you can pass a directory to and compare the estimations and truth csvs within that directory. If you want to see our very simple comparison algorithm, take a look at `evaluate_estimations.py`; if you'd like to set up your testing and file structure differently, you can use this instead of `run_eval.sh`. To run it, you can run `uv run python evaluate_estimations.py`.

The final evaluation will be run in `data/eval` - so please don't put anything in here! - with a witheld set of validation images; the winning team will be the one with the lowest error. There's also a bonus award for the best-designed interface, if you want to spend time on that!

## Final Remarks
- Both the area to search and the evaluation coordinates are in WSG84/EPSG:4326 format
- Please use this repo to flag any issues you come across
- Arondite will also be present on-site for any questions you have
- Good luck!

# Contour Matcher Component

This component provides tools for matching drone and satellite images by treating all contours as a single pattern, using a holistic approach.

## Holistic Contour Matching

Unlike individual contour matching, the holistic approach treats the entire set of contours as a single pattern. It creates composite images containing all contours from both drone and satellite images, then finds the optimal transformation (scale, rotation, translation) to align them.

### Why Holistic Matching?

The holistic approach is superior for several reasons:

1. **Considers spatial relationships** - It maintains the relationships between contours, which is crucial for landmark recognition
2. **More robust to noise** - Less affected by individual contour variations or extraction errors
3. **Single transformation** - Provides one coherent transformation that aligns the entire image
4. **Mimics human perception** - Similar to how humans recognize locations by overall pattern, not by individual features

## How It Works

1. **Pattern Creation**:
   - Converts all contours from both drone and satellite images into binary images
   - Centers the patterns for consistent comparison
   - Preserves the spatial relationships between contours

2. **Transformation Search**:
   - Tries different scales to account for altitude differences
   - Applies rotation to handle orientation differences
   - Tests translations to align the patterns
   - Uses a grid search to find optimal parameters

3. **Similarity Calculation**:
   - Uses Intersection over Union (IoU) to measure similarity
   - Compares the entire pattern rather than individual contours
   - Produces a score from 0 to 1 (perfect match)

4. **Visualization**:
   - Generates composite images showing the contour patterns
   - Creates alignment visualizations showing how well patterns match
   - Shows transformation parameters (scale, rotation, translation)

## Usage

### Fast Mode (Recommended)

For quick results with reasonable accuracy:
```bash
python3 holistic_test.py --input-json path/to/contours.json --fast
```

Options:
- `--fast`: Use faster settings with fewer scale/rotation steps
- `--output-dir folder_name`: Set output directory (default: holistic_output)
- `--debug`: Enable detailed debugging output

### Full Control

For precise control over matching parameters:
```bash
python3 holistic_matcher.py --input-json path/to/contours.json --output-dir folder_name
```

Options:
- `--min-score 0.15`: Minimum similarity score (0-1)
- `--min-scale 0.5`: Minimum scale factor to try
- `--max-scale 2.0`: Maximum scale factor to try
- `--scale-steps 10`: Number of scale steps to try
- `--angle-step 10`: Step size for rotation angles (degrees)
- `--debug`: Enable detailed debugging output

## Input Format

The input JSON file should have the following structure:

```json
{
  "image_id": "Reading_1",
  "drone_contours": [
    {
      "points": [[x1, y1], [x2, y2], ...],
      "length": 123.4
    }
  ],
  "satellite_contours": [
    {
      "area_id": "area_1",
      "contours": [
        {
          "points": [[x1, y1], [x2, y2], ...],
          "length": 456.7
        }
      ]
    }
  ]
}
```

## Output

The matching process generates:

1. **Composite Images**:
   - `drone_composite.png`: All drone contours
   - `satellite_composite_area_*.png`: All contours for each satellite area

2. **Match Visualizations**:
   - `holistic_match_area_*.png`: Visual alignment of patterns
   - Color-coded: blue (satellite), green (drone), yellow (overlap)

3. **Results JSON**:
   - `holistic_match_results.json`: Detailed match results with scores and transformation parameters

## Performance Considerations

- The full matcher with detailed parameters is more computationally intensive
- Use the `--fast` option for quicker results (5x to 10x faster)
- For very large datasets, consider reducing the number of scale steps and increasing the angle step
- Processing time increases with the number of transformation parameters tested

## Requirements

```
numpy>=1.20.0
opencv-python>=4.5.0
matplotlib>=3.4.0
```
