#!/bin/bash
# Simple script to run the simplified holistic matching example

# Purpose: This script helps users run the simplified holistic matching example
# with their own drone image or with a provided one.

# Display usage instructions
echo "Drone Image Matcher - Simplified Holistic Matching Example"
echo "=========================================================="
echo 
echo "This example demonstrates the simplified holistic matching algorithm,"
echo "which is 10-20x faster than full holistic matching while maintaining"
echo "excellent accuracy for images with consistent orientation."
echo

# Check if drone image was provided
if [ "$#" -lt 1 ]; then
    echo "Usage: ./run_example.sh path/to/drone_image.jpg"
    echo
    echo "You must provide a path to a drone image."
    echo "Ideally this should be an aerial image taken from directly above (nadir view)."
    exit 1
fi

# Get the drone image path
DRONE_IMAGE="$1"

# Check if the file exists
if [ ! -f "$DRONE_IMAGE" ]; then
    echo "Error: Cannot find drone image at $DRONE_IMAGE"
    echo "Please provide a valid path to a drone image."
    exit 1
fi

# Create output directory
OUTPUT_DIR="example_output"
mkdir -p "$OUTPUT_DIR"

echo "Running simplified holistic matching example..."
echo "Drone image: $DRONE_IMAGE"
echo "Output directory: $OUTPUT_DIR"
echo

# Run the example script
python3 simplified_matching_example.py --drone-image "$DRONE_IMAGE" --output "$OUTPUT_DIR"

# Check if execution was successful
if [ $? -ne 0 ]; then
    echo "Error: The example script failed to run successfully."
    echo "Please check the error messages above."
    exit 1
fi

echo
echo "Example completed! You can find the output in the $OUTPUT_DIR directory."
echo "For more information about simplified holistic matching, see:"
echo "docs/SIMPLIFIED_HOLISTIC_MATCHING.md" 