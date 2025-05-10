#!/usr/bin/env python3
"""
Test script for processing one drone image and multiple satellite images with ContourExtractor.
"""

import os
import json
from contour_extractor import ContourExtractor

def main():
    # Create output directory
    output_dir = "multi_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize the contour extractor
    extractor = ContourExtractor()
    
    # Define paths
    drone_image_path = "../../../Competition Release/Reading_1_cleaned.jpg"
    satellite_image_paths = [
        "../../../Competition Release/Reading_1_cleaned.jpg",
        "../../../Competition Release/Reading_2_cleaned.jpg",
        "../../../Competition Release/Reading_3_cleaned.jpg",
        "../../../Competition Release/Reading_4_cleaned.jpg"
    ]
    
    # Process drone image
    print(f"Processing drone image: {drone_image_path}")
    preprocessed_drone = extractor.preprocess_image(drone_image_path)
    drone_contours = extractor.extract_contours(preprocessed_drone)
    print(f"Found {len(drone_contours)} contours in drone image")
    
    # Save visualization of drone contours
    drone_vis_path = os.path.join(output_dir, "drone_contours.png")
    extractor.visualize_contours(drone_image_path, drone_contours, drone_vis_path)
    print(f"Saved drone contour visualization to {drone_vis_path}")
    
    # Format drone contours for output
    formatted_drone_contours = extractor.format_contours_for_output(drone_contours)
    
    # Process satellite images
    satellite_data = []
    
    for idx, sat_path in enumerate(satellite_image_paths):
        area_id = f"area_{idx+1}"
        print(f"Processing satellite image {area_id}: {sat_path}")
        
        # Extract contours
        preprocessed_sat = extractor.preprocess_image(sat_path)
        sat_contours = extractor.extract_contours(preprocessed_sat)
        print(f"Found {len(sat_contours)} contours in satellite image {area_id}")
        
        # Save visualization
        sat_vis_path = os.path.join(output_dir, f"satellite_contours_{area_id}.png")
        extractor.visualize_contours(sat_path, sat_contours, sat_vis_path)
        print(f"Saved satellite contour visualization to {sat_vis_path}")
        
        # Format contours
        formatted_sat_contours = extractor.format_contours_for_output(sat_contours)
        
        # Add to satellite data
        satellite_data.append({
            "area_id": area_id,
            "contours": formatted_sat_contours,
            "bounds": [0, 0, 1000, 1000],  # Placeholder bounds
            "image_path": sat_path
        })
    
    # Create complete output
    output = {
        "image_id": "reading_1_drone",
        "drone_contours": formatted_drone_contours,
        "satellite_contours": satellite_data
    }
    
    # Write output to JSON file
    output_json_path = os.path.join(output_dir, "multi_contours_output.json")
    with open(output_json_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Saved multi-image contour data to {output_json_path}")
    print("\nMulti-image test completed successfully!")

if __name__ == "__main__":
    main() 