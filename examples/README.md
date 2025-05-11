# Drone Image Matcher Examples

This directory contains example scripts that demonstrate how to use the drone image matching system, particularly focusing on the simplified holistic matching approach that offers excellent performance.

## Available Examples

1. **simplified_matching_example.py**: Demonstrates simplified holistic matching with an option to compare against full holistic matching.

## Requirements

To run the examples, you need:

1. A drone image (aerial photograph, ideally taken from directly above)
2. Python 3.6+
3. All dependencies installed (see main project requirements.txt)

## Running the Examples

### Simplified Holistic Matching Example

This example demonstrates the simplified holistic matching algorithm, which is 10-20x faster than full holistic matching while maintaining excellent accuracy for images with consistent orientation.

You can run it using the provided shell script:

```bash
# Make the script executable if needed
chmod +x run_example.sh

# Run with your drone image
./run_example.sh path/to/your/drone_image.jpg
```

Or directly with Python:

```bash
python simplified_matching_example.py --drone-image path/to/your/drone_image.jpg --output example_output
```

### What the Example Does

The simplified holistic matching example:

1. Creates a sample set of coordinates (for famous landmarks)
2. Downloads satellite images for each coordinate using Google Maps API
3. Extracts contours from both the drone image and satellite images
4. Matches the contours using simplified holistic matching (translations only)
5. Ranks the potential locations by similarity score
6. Optionally compares the performance against full holistic matching

### Example Output

```
Drone Image: path/to/your/drone_image.jpg
Best Match: {'lat': 48.8584, 'lon': 2.2945, 'description': 'Eiffel Tower, Paris'}
Score: 0.42
Satellite Image: example_output/satellite_1.png

All Matches (sorted by score):
1. Coordinates: {'lat': 48.8584, 'lon': 2.2945, 'description': 'Eiffel Tower, Paris'}, Score: 0.42
2. Coordinates: {'lat': 40.6892, 'lon': -74.0445, 'description': 'Statue of Liberty, New York'}, Score: 0.38
...

Total processing time: 4.82 seconds
```

## Notes for Real-World Usage

The example uses famous landmarks for demonstration purposes, but in real-world applications, you should:

1. Provide coordinates near where the drone image was captured
2. Use more densely distributed coordinates for better accuracy
3. Consider the altitude and orientation of the drone when capturing the image

For best results with simplified holistic matching:
- The drone should be pointing directly downward when capturing the image
- The drone image should have a similar orientation to the satellite images (typically north-up)
- The scale of the drone image should be reasonably close to the satellite images

## More Information

For more detailed documentation on the simplified holistic matching approach, see:
- [Simplified Holistic Matching](../docs/SIMPLIFIED_HOLISTIC_MATCHING.md) 