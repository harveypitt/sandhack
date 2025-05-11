# Purpose: Process competition area polygons and generate satellite images
# for points within or around these areas using Google Maps Static API
import json
import os
import pathlib
import sys
import math
import urllib.parse
import requests

# Add parent directory to path so we can import from get-map-image
script_dir = pathlib.Path(__file__).parent
sys.path.append(str(script_dir.parent / "get-map-image"))
from get_map_image import static_map_url

# Constants
API_KEY = "AIzaSyCQGFKY2w5DZMzxDAmMNrXRBFHRQqbijI8"
COMPETITION_DIR = pathlib.Path("/Users/henryallen/Desktop/sandhack/Competition Release")
OUTPUT_BASE_DIR = script_dir / "competition_images"
OUTPUT_BASE_DIR.mkdir(exist_ok=True)

def process_polygon(polygon, output_dir, area_name):
    """
    Extract and process coordinates from a GeoJSON polygon.
    For each polygon, we'll take:
    1. Each corner point
    2. The center point of the polygon
    """
    coordinates = polygon["coordinates"][0]  # First (and usually only) ring of coordinates
    
    # Create output directory for this area
    area_dir = output_dir / area_name
    area_dir.mkdir(exist_ok=True)
    
    # Process each corner point
    for i, coord in enumerate(coordinates[:-1]):  # Skip the last one as it duplicates the first in a closed polygon
        lon, lat = coord
        url = static_map_url(lat, lon)
        img = requests.get(url)
        img.raise_for_status()
        img_path = area_dir / f"corner_{i+1}.png"
        img_path.write_bytes(img.content)
        print(f"Saved {img_path}")
    
    # Calculate and process center point (average of all coordinates)
    sum_lon = sum(coord[0] for coord in coordinates[:-1])
    sum_lat = sum(coord[1] for coord in coordinates[:-1])
    count = len(coordinates[:-1])
    center_lon = sum_lon / count
    center_lat = sum_lat / count
    
    url = static_map_url(center_lat, center_lon)
    img = requests.get(url)
    img.raise_for_status()
    img_path = area_dir / "center.png"
    img_path.write_bytes(img.content)
    print(f"Saved {img_path}")

def process_geojson_file(file_path):
    """Process a GeoJSON file containing polygon features"""
    file_path = pathlib.Path(file_path)
    area_name = file_path.stem.replace('_cleaned_search_area', '')
    
    # Create output directory for this file
    output_dir = OUTPUT_BASE_DIR / area_name
    output_dir.mkdir(exist_ok=True)
    
    with open(file_path) as f:
        data = json.load(f)
    
    # Process each feature in the GeoJSON
    for i, feature in enumerate(data["features"]):
        if feature["geometry"]["type"] == "Polygon":
            process_polygon(
                feature["geometry"], 
                output_dir, 
                f"polygon_{i+1}"
            )

def main():
    # Get all JSON files in the competition directory
    json_files = list(COMPETITION_DIR.glob("*_search_area.json"))
    
    if not json_files:
        print("No JSON files found in the competition directory")
        return
    
    # Group files by type (Reading vs Rickmansworth)
    reading_files = [f for f in json_files if "Reading" in f.name]
    rick_files = [f for f in json_files if "Rickmansworth" in f.name]
    
    print(f"Found {len(reading_files)} Reading files and {len(rick_files)} Rickmansworth files")
    
    # Process Reading files
    for file_path in reading_files:
        print(f"Processing {file_path.name}...")
        process_geojson_file(file_path)
    
    # Process Rickmansworth files
    for file_path in rick_files:
        print(f"Processing {file_path.name}...")
        process_geojson_file(file_path)
    
    print("All files processed successfully!")

if __name__ == "__main__":
    main() 