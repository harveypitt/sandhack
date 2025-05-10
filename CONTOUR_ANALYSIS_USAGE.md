# Contour Analysis Feature Documentation

This document describes how to use the Contour Analysis feature for location estimation in the application.

## Overview

The Contour Analysis feature extracts contours from drone images and satellite imagery, then matches them to identify potential location matches. It uses computer vision algorithms to detect edges, shapes, and patterns in the images, making it useful for estimating locations when GPS data is unavailable.

## Components

The feature consists of several components:

1. **ContourExtractor**: Extracts contours from images using adaptive thresholding
2. **ContourMatcher**: Matches contours between drone and satellite images
3. **Frontend UI**: Allows users to upload and process images
4. **API Endpoints**: Handles the extraction and matching processes

## How to Use the Feature

### Step 1: Upload Images

1. Navigate to the Contour Analysis page in the web application
2. Upload a drone/UAV image using the "Upload Drone Image" button
3. Upload 1-4 satellite images using the "Upload Satellite Images" button

### Step 2: Extract Contours

1. Adjust the "Contour Detection Threshold" slider as needed:
   - Higher values (toward 100): Detect more contours, including weaker ones
   - Lower values (toward 0): Detect fewer contours, but stronger and more distinct
2. Click the "Extract Contours" button
3. View the contour extraction results, showing the original image and detected contours

### Step 3: Match Contours

1. After successful extraction, click the "Match Contours" button
2. The system will process all uploaded satellite images and compare them to the drone image
3. View the results, including:
   - Best match with score
   - Comparison visualizations
   - Holistic pattern matching
   - Individual contour visualizations

## Understanding the Results

### Match Score

The match score (0-100%) indicates how well the contours from the drone image match each satellite image. Higher scores indicate better matches.

### Visualizations

1. **Comparison View**: Shows drone image (left) and satellite image (right) with extracted contours
2. **Holistic View**: Shows contour patterns against a dark background to visualize the overall pattern matching
3. **Contour View**: Shows extracted contours overlaid on the original images

## Technical Details

### Contour Extraction

The system uses OpenCV to process images with the following steps:
1. Convert to grayscale
2. Apply Gaussian blur to reduce noise
3. Use Canny edge detection with dynamic thresholds
4. Find and filter contours based on area

### Contour Matching

Matching uses several techniques:
1. **Shape Descriptors**: Comparing properties like area, perimeter, and circularity
2. **Hu Moments**: Scale and rotation invariant shape descriptors
3. **Holistic Pattern Matching**: Treating all contours as a single pattern

## API Endpoints

For developers integrating with the API:

### Extract Contours

```
POST /api/contour/extract
```

**Parameters:**
- `file`: Image file (form-data)
- `threshold`: Integer value 0-100 (form-data)

**Response:**
```json
{
  "original_image": "<base64-encoded-image>",
  "contour_visualization": "<base64-encoded-image>",
  "contours": [...],
  "contour_count": 42,
  "major_features": ["Found 3 major structural elements", "..."],
  "threshold_used": 50
}
```

### Match Contours

```
POST /api/contour/match
```

**Parameters:**
- `drone_image`: Drone image file (form-data)
- `satellite_images`: Up to 4 satellite image files (form-data)
- `threshold`: Integer value 0-100 (form-data)

**Response:**
```json
{
  "drone_image": "<base64-encoded-image>",
  "drone_contour_count": 24,
  "drone_contour_visualization": "<base64-encoded-image>",
  "satellite_results": [
    {
      "image_index": 0,
      "match_score": 76.5,
      "satellite_image": "<base64-encoded-image>",
      "visualization": "<base64-encoded-image>",
      "holistic_visualization": "<base64-encoded-image>",
      "contour_count": 38,
      "contour_visualization": "<base64-encoded-image>",
      "filename": "satellite1.jpg"
    },
    ...
  ],
  "best_match_index": 2,
  "best_match_score": 82.1
}
```

## Limitations

- Processing large or high-resolution images may take longer
- Contour matching works best when the images have clear, distinct features
- Very similar-looking areas may produce similar match scores
- Weather conditions, lighting, and seasonal changes can affect matching accuracy

## Troubleshooting

1. **Low match scores for all images**: Try adjusting the threshold to find more or fewer contours
2. **Long processing times**: Reduce image size/resolution before uploading
3. **No contours detected**: Ensure the image has clear features and good contrast
4. **Browser timeouts**: For large images, the backend timeout is set to 2 minutes 