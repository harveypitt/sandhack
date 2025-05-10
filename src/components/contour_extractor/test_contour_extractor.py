#!/usr/bin/env python3
"""
Test script for the ContourExtractor component.
"""

import os
import sys
import json
import argparse
from contour_extractor import ContourExtractor

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test the Contour Extractor component")
    parser.add_argument("--drone-image", required=True, help="Path to drone image")
    parser.add_argument("--satellite-image", required=True, help="Path to satellite image")
    parser.add_argument("--output-dir", default="output", help="Directory to save visualization output")
    parser.add_argument("--min-length", type=int, default=150, help="Minimum contour length")
    parser.add_argument("--canny-low", type=int, default=100, help="Lower threshold for Canny edge detector")
    parser.add_argument("--canny-high", type=int, default=200, help="Upper threshold for Canny edge detector")
    return parser.parse_args()

def main():
    """Run contour extraction test."""
    args = parse_args()
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize the contour extractor
    extractor = ContourExtractor(
        canny_threshold1=args.canny_low,
        canny_threshold2=args.canny_high,
        min_contour_length=args.min_length
    )
    
    print(f"Processing drone image: {args.drone_image}")
    
    # Extract contours from drone image
    preprocessed_drone = extractor.preprocess_image(args.drone_image)
    drone_contours = extractor.extract_contours(preprocessed_drone)
    
    print(f"Found {len(drone_contours)} contours in drone image")
    
    # Save visualization of drone contours
    drone_vis_path = os.path.join(args.output_dir, "drone_contours.png")
    extractor.visualize_contours(args.drone_image, drone_contours, drone_vis_path)
    print(f"Saved drone contour visualization to {drone_vis_path}")
    
    print(f"Processing satellite image: {args.satellite_image}")
    
    # Extract contours from satellite image
    preprocessed_satellite = extractor.preprocess_image(args.satellite_image)
    satellite_contours = extractor.extract_contours(preprocessed_satellite)
    
    print(f"Found {len(satellite_contours)} contours in satellite image")
    
    # Save visualization of satellite contours
    satellite_vis_path = os.path.join(args.output_dir, "satellite_contours.png")
    extractor.visualize_contours(args.satellite_image, satellite_contours, satellite_vis_path)
    print(f"Saved satellite contour visualization to {satellite_vis_path}")
    
    # Format contours for output
    formatted_drone_contours = extractor.format_contours_for_output(drone_contours)
    formatted_satellite_contours = extractor.format_contours_for_output(satellite_contours)
    
    # Create example output
    output = {
        "image_id": os.path.basename(args.drone_image).split('.')[0],
        "drone_contours": formatted_drone_contours,
        "satellite_contours": [
            {
                "area_id": "test_area",
                "contours": formatted_satellite_contours,
                "bounds": [0, 0, 1000, 1000]  # Placeholder bounds
            }
        ]
    }
    
    # Write output to JSON file
    output_json_path = os.path.join(args.output_dir, "contours_output.json")
    with open(output_json_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Saved contour data to {output_json_path}")
    print("\nTest completed successfully!")

if __name__ == "__main__":
    main() 