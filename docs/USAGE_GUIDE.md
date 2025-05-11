# Drone Image Matcher Usage Guide

This guide provides step-by-step instructions for using the Drone Image Matcher system.

## Quick Start

### Step 1: Prepare Your Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/sandhack.git
   cd sandhack
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Step 2: Prepare Your Data

1. **Drone Image**: Have a drone image ready for matching.

2. **Coordinates File**: Create a JSON file with potential coordinates in the following format:
   ```json
   [
     {
       "lat": 51.6527061,
       "lon": -0.5245044,
       "description": "Rickmansworth park - Original Exact"
     },
     {
       "lat": 51.6527061,
       "lon": -0.52435919,
       "description": "Rickmansworth park - 10m East"
     }
   ]
   ```

### Step 3: Run the Matcher

Navigate to the drone-image-matcher directory:
```bash
cd backend/src/components/drone-image-matcher
```

#### Using Simplified Holistic Matching (Recommended)

```bash
python3 drone_image_matcher.py --drone-image path/to/your/drone_image.jpg --coordinates path/to/your/coordinates.json --simplify
```

This approach:
- Is much faster than full holistic matching
- Only tests different translations (positions), not rotations or scales
- Works well when drone images are already aligned with satellite imagery

#### Using Full Holistic Matching

```bash
python3 drone_image_matcher.py --drone-image path/to/your/drone_image.jpg --coordinates path/to/your/coordinates.json
```

This approach:
- Tests multiple scales, rotations, and translations
- Is more robust to differently oriented images
- Is computationally intensive and may take several minutes

#### Using Contour-Based Matching

```bash
python3 drone_image_matcher.py --drone-image path/to/your/drone_image.jpg --coordinates path/to/your/coordinates.json --use-contour
```

This approach:
- Is the fastest method
- May not work well with rotated images
- Treats contours individually rather than as a collective pattern

### Step 4: Interpret Results

The script will output results in the terminal:

```
Matching Results:
Drone Image: path/to/your/drone_image.jpg
Best Match: {'lat': 51.6527061, 'lon': -0.5245044, 'description': 'Rickmansworth park - Original Exact'}
Score: 100.0
Satellite Image: satellite_images/satellite_1.png

All Matches (sorted by score):
1. Coordinates: {'lat': 51.6527061, 'lon': -0.5245044, 'description': 'Rickmansworth park - Original Exact'}, Score: 100.0
2. Coordinates: {'lat': 51.6527061, 'lon': -0.52435919, 'description': 'Rickmansworth park - 10m East'}, Score: 1.01
```

The results include:
- The best matching location with coordinates and score
- A list of all locations sorted by match score

## Advanced Usage

### Testing with Offset Coordinates

To test how well the system handles slightly offset coordinates:

```bash
python3 test_offset_matching.py --simplify
```

This will test matching with coordinates at various distances from reference points.

### Comparing Different Matching Methods

To compare all matching methods on the same inputs:

```bash
python3 test_image_matcher.py --compare-methods
```

Note: This will take significantly longer as it runs full holistic matching.

### Customizing Output Directory

You can specify where to save the downloaded satellite images:

```bash
python3 drone_image_matcher.py --drone-image path/to/drone_image.jpg --coordinates path/to/coordinates.json --output custom_output_dir --simplify
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're running the script from the `drone-image-matcher` directory.

2. **Satellite Image Download Failures**: Check your internet connection or try again later if the Google Maps API is rate-limiting requests.

3. **No Matches Found**: If all scores are low, try:
   - Using the full holistic matching (remove `--simplify` flag)
   - Checking your coordinates file for accuracy
   - Ensuring the drone image has visible features

### Performance Optimization

- For faster processing, use the `--simplify` flag
- For best accuracy with rotated images, use full holistic matching
- For quick tests with many coordinates, use contour-based matching with `--use-contour` 