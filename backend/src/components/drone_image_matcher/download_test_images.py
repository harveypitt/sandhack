#!/usr/bin/env python3
# Purpose: Test script to download satellite images for the defined coordinates
# This helps visualize the locations to prepare for drone image matching

import json
import os
import sys
import pathlib
import argparse
import requests

# Add parent directories to path so we can import from sibling components
script_dir = pathlib.Path(__file__).parent
backend_src_dir = script_dir.parent.parent
get_map_image_dir = script_dir.parent / "get-map-image"

# Append to sys.path
sys.path.append(str(backend_src_dir))
sys.path.append(str(get_map_image_dir))

# Import static_map_url function directly from the module
from get_map_image import static_map_url

def download_images_for_coordinates(coordinates_file, output_dir):
    """
    Download satellite images for all coordinates in the specified JSON file.
    
    Args:
        coordinates_file (str): Path to JSON file with coordinates
        output_dir (str): Directory to save satellite images
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load coordinates from JSON file
    with open(coordinates_file, 'r') as f:
        coordinates = json.load(f)
    
    print(f"Downloading {len(coordinates)} satellite images...")
    
    # Download images for each coordinate
    for i, coord in enumerate(coordinates):
        lat, lon = coord['lat'], coord['lon']
        description = coord.get('description', f"Location {i+1}")
        
        # Get filename from description
        filename = description.replace(' ', '_').replace('-', '_').lower()
        filename = f"{i+1:02d}_{filename}.png"
        
        # Get the satellite image URL
        url = static_map_url(lat, lon)
        
        # Download the image
        img_path = os.path.join(output_dir, filename)
        response = requests.get(url)
        response.raise_for_status()
        
        # Save the image
        with open(img_path, "wb") as f:
            f.write(response.content)
        
        print(f"Downloaded image {i+1}/{len(coordinates)}: {description}")
    
    print(f"All images downloaded to {output_dir}")
    return 0

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Download satellite images for coordinates.')
    parser.add_argument('--coordinates', '-c', required=True, 
                        help='Path to JSON file with coordinates')
    parser.add_argument('--output', '-o', default='satellite_images',
                        help='Directory to save satellite images')
    return parser.parse_args()

def main():
    """Main function to run the test script."""
    args = parse_args()
    return download_images_for_coordinates(args.coordinates, args.output)

if __name__ == "__main__":
    sys.exit(main()) 