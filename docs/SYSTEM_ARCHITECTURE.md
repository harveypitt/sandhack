# Drone Image Matching System Architecture

## Overview

The Drone Image Matching System is designed to match drone imagery with satellite imagery to determine the location where a drone image was captured. The system works by downloading satellite images from the Google Maps API, extracting visual features from both drone and satellite images, and comparing these features to find the best match.

## System Components

The system consists of several key components that work together:

1. **Satellite Image Acquisition** (`get-map-image`)
   - Downloads satellite imagery from Google Maps API
   - Calculates appropriate zoom levels based on latitude
   - Maintains consistent scale across different locations

2. **Feature Extraction** (`contour_extractor`)
   - Processes images to identify key visual features
   - Extracts contours representing roads, buildings, and other landmarks
   - Filters and categorizes features by size and shape

3. **Feature Matching** (`contour_matcher`)
   - Compares contours between drone and satellite images
   - Uses both shape-based and holistic pattern matching
   - Calculates similarity scores between images

4. **Drone Image Matcher** (`drone-image-matcher`)
   - Orchestrates the entire matching process
   - Coordinates between all components
   - Ranks potential matches by similarity score

## Component Interaction

```
┌─────────────────┐         ┌─────────────────┐        ┌─────────────────┐
│                 │         │                 │        │                 │
│  get-map-image  │────────▶│contour_extractor│───────▶│ contour_matcher │
│                 │         │                 │        │                 │
└─────────────────┘         └─────────────────┘        └─────────────────┘
         ▲                          ▲                          ▲
         │                          │                          │
         │                          │                          │
         │                          │                          │
         └──────────────────────────┴──────────────────────────┘
                                    │
                                    │
                                    ▼
                          ┌─────────────────┐
                          │                 │
                          │drone-image-matcher
                          │                 │
                          └─────────────────┘
```

### Data Flow

1. Drone Image Matcher receives a drone image and potential coordinates
2. Get-Map-Image downloads satellite images for each coordinate
3. Contour Extractor processes both drone and satellite images to identify features
4. Contour Matcher compares extracted features and calculates similarity scores
5. Drone Image Matcher ranks the potential matches and returns the best location

## Implementation Details

### Satellite Image Acquisition

The `get_map_image.py` module handles satellite imagery download:

```python
def static_map_url(lat, lon, width_m=250, pix=640, scale=2):
    # Calculate zoom level based on latitude to maintain consistent scale
    m_per_pix = width_m / (pix * scale)
    zoom = round(math.log2(math.cos(math.radians(lat))*156543.03392 / m_per_pix))
    zoom = max(0, min(21, zoom))  # clamp
    
    # Construct Google Maps Static API URL
    params = dict(center=f"{lat},{lon}",
                  zoom=zoom,
                  size=f"{pix}x{pix}",
                  scale=scale,
                  maptype="satellite",
                  key=API_KEY)
    return "https://maps.googleapis.com/maps/api/staticmap?" + urllib.parse.urlencode(params)
```

### Feature Extraction

The `contour_extractor.py` module handles feature extraction using multiple image processing techniques:

```python
def extract_contours(image):
    # Convert to grayscale and apply Gaussian blur
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Apply Canny edge detection with dynamic thresholds
    edges = cv2.Canny(blurred, canny_low, canny_high)
    
    # Find and filter contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
    
    return filtered_contours
```

### Feature Matching

The `contour_matcher.py` module handles matching using both shape-based and holistic approaches:

```python
def match_contours(drone_contours, sat_contours):
    # Calculate shape similarity for individual contours
    shape_similarity = _compute_contour_similarity(drone_contours, sat_contours)
    
    # Calculate holistic pattern similarity between contour sets
    holistic_similarity = _compute_holistic_similarity(drone_contours, sat_contours)
    
    # Combine similarities with appropriate weights
    combined_score = 0.4 * shape_similarity + 0.6 * holistic_similarity
    
    return combined_score
```

### Drone Image Matcher

The `drone_image_matcher.py` module orchestrates the entire process:

```python
def find_best_match(drone_image_path, coordinates):
    # Download satellite images for all coordinates
    satellite_image_paths = download_satellite_images(coordinates)
    
    # Extract features from the drone image
    drone_features = extract_features(drone_image_path)
    
    # Extract features from all satellite images
    satellite_features = []
    for path in satellite_image_paths:
        features = extract_features(path)
        satellite_features.append(features)
    
    # Match features and rank results
    match_scores = match_features(drone_features, satellite_features)
    
    return {
        'drone_image': drone_image_path,
        'best_match': results[0],
        'all_matches': results
    }
```

## Test Framework

The system includes a test framework for validating the matching process:

1. **Test Data Generation**
   - `download_test_images.py`: Downloads satellite images for test coordinates
   - Test datasets for both Rickmansworth Park and Reading University areas

2. **Controlled Testing**
   - `test_image_matcher.py`: Uses satellite images as simulated drone images
   - Test cases verify that the system can correctly match images to their source locations

## Usage Guide

### Downloading Test Images

```bash
python download_test_images.py --coordinates nearby_coordinates.json --output rickmansworth_images
```

### Running Tests

```bash
python test_image_matcher.py
```

### Using the Drone Image Matcher

```bash
python drone_image_matcher.py --drone-image my_drone_image.png --coordinates possible_locations.json
```

## Performance Considerations

- **Contour Extraction Parameters**: Adjust threshold values to balance feature quantity and quality
- **Matching Algorithms**: Shape-based matching is faster but less accurate; holistic matching is more accurate but computationally intensive
- **Test Coverage**: Always verify matching accuracy with controlled tests before deployment

## Future Improvements

1. **Machine Learning Integration**: Train models to improve matching accuracy
2. **Scale Invariance**: Enhance matching across images taken at different altitudes
3. **Multi-sensor Fusion**: Incorporate other sensor data (altitude, heading) to improve matching
4. **Distributed Processing**: Enable parallel processing for faster matching with large datasets

## Image Matching Approaches

The system implements multiple approaches for matching drone images with satellite imagery:

### 1. Contour-Based Matching

The contour-based approach compares individual contours between images:

- Each contour from the drone image is compared with each contour from satellite images
- Shape descriptors (area, perimeter, circularity, Hu moments) are used to calculate similarity
- Contours are matched based on shape similarity, regardless of position
- Best matches between contour pairs are averaged to produce a final similarity score

This approach works well when distinctive shapes are present and relatively isolated. It is the fastest method but may miss matches when images are rotated or at different scales.

### 2. Holistic Matching (Full)

The full holistic approach treats all contours as a collective pattern and tests many transformations:

- Creates composite binary images containing all contours from both drone and satellite images
- Finds the optimal transformation (scale, rotation, translation) to align the patterns
- Tests multiple scale factors (0.5x to 2.0x)
- Tests multiple rotation angles (0° to 350° in steps)
- Tests multiple translations in X and Y directions
- Uses Intersection over Union (IoU) to measure similarity between transformed images
- Accounts for the spatial relationships between contours

This approach is more robust to:
- Rotation of the drone image relative to satellite imagery
- Scale differences between images
- Small positioning offsets
- Partial matches where only a portion of features align

However, the full holistic matching is computationally intensive as it tests hundreds of different transformations for each image pair.

### 3. Holistic Matching (Simplified)

The simplified holistic approach maintains the pattern-matching concept but restricts transformations:

- Uses the same composite image approach as full holistic matching
- Only tests different translations (X and Y positions)
- Keeps scale fixed at 1.0 (no scaling)
- Keeps rotation fixed at 0° (no rotation)
- Significantly faster than full holistic matching (10-20x faster)

This approach is ideal when:
- Drone images are already aligned with the satellite imagery (same orientation)
- The scale is consistent between drone and satellite images
- Only small position adjustments are needed to find the match

The simplified matching can be enabled with the `--simplify` flag in the command line interface.

### Performance Comparison

| Matching Method | Speed | Accuracy for Exact Matches | Robustness to Rotation | Robustness to Scale | Robustness to Position Offset |
|-----------------|-------|----------------------------|------------------------|---------------------|------------------------------|
| Contour-based   | Fast  | High                       | Low                    | Low                 | Medium                       |
| Holistic (Full) | Slow  | High                       | High                   | High                | High                         |
| Holistic (Simplified) | Medium | High                | Low                    | Low                 | High                         |

The system will use holistic matching by default, falling back to contour-based matching if needed. The simplified holistic matching can be enabled through the command line interface.

## Testing Approaches

The system includes robust testing capabilities:

1. **Controlled Testing**: Using satellite images as simulated drone images for predictable results
2. **Offset Testing**: Testing with coordinates slightly offset from reference points to evaluate robustness
3. **Method Comparison**: Directly comparing holistic vs. contour-based matching on the same inputs

These tests help assess the system's performance in controlled environments before deployment with real drone imagery.

## Conclusion

The Drone Image Matching System provides a robust pipeline for matching drone imagery with satellite images to determine the location where a drone image was captured. By leveraging image processing techniques and contour matching algorithms, the system can identify the most likely location from a set of candidate coordinates. 