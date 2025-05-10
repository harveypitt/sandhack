#!/usr/bin/env python3
"""
OSM Search Area Processor

This module loads search area coordinates and converts them into the Overpass QL polygon format.
"""

import os
import json
import logging
import overpy
import geojson
from pathlib import Path

# Configure logging

logger = logging.getLogger(__name__)

# Hardcoded path to the search area JSON file
SEARCH_AREA_PATH = "/Users/harveypitt/Documents/Alive Industries/Repos/sandhack/data/example/images/rickmansworth_example_search_area.json"

def load_coordinates(file_path=SEARCH_AREA_PATH):
    """
    Load search area coordinates from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing coordinates
        
    Returns:
        List of coordinates (lat, lon pairs) or None if failed
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"Coordinates file not found: {file_path}")
            return None
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Try to use geojson library if available
        try:
            gj = geojson.loads(json.dumps(data))
            if hasattr(gj, 'features') and len(gj.features) > 0:
                # FeatureCollection
                feature = gj.features[0]
                if feature.geometry.type == 'Polygon':
                    # Get first (outer) ring of polygon
                    coords = feature.geometry.coordinates[0]
                    # GeoJSON uses [lon, lat], we need [lat, lon]
                    coordinates = [[coord[1], coord[0]] for coord in coords]
                    logger.info(f"Loaded {len(coordinates)} coordinates from {file_path} using geojson library")
                    return coordinates
        except (NameError, AttributeError, IndexError) as e:
            # Continue with manual parsing if geojson library isn't available or fails
            logger.debug(f"Couldn't use geojson library: {e}")
        
        # Manual parsing of different possible structures
        coordinates = []
        
        # Standard array of coordinates
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            coordinates = data
            
        # Object with coordinates array    
        elif 'coordinates' in data and isinstance(data['coordinates'], list):
            coordinates = data['coordinates']
            
        # GeoJSON direct geometry
        elif 'geometry' in data and 'coordinates' in data['geometry']:
            # GeoJSON polygons are arrays of arrays of [lon, lat] pairs
            coords = data['geometry']['coordinates']
            if len(coords) > 0:
                # If it's a multipolygon, take the first polygon
                if isinstance(coords[0][0], list) and isinstance(coords[0][0][0], (int, float)):
                    # This is a polygon, so coords[0] is the outer ring
                    coords = coords[0]
                # GeoJSON uses [lon, lat], we need [lat, lon]
                coordinates = [[coord[1], coord[0]] for coord in coords]
        
        # GeoJSON FeatureCollection
        elif 'type' in data and data['type'] == 'FeatureCollection' and 'features' in data and len(data['features']) > 0:
            feature = data['features'][0]
            if 'geometry' in feature and 'coordinates' in feature['geometry']:
                coords = feature['geometry']['coordinates']
                if len(coords) > 0:
                    # For Polygon type, get the first (outer) ring
                    if feature['geometry']['type'] == 'Polygon':
                        coords = coords[0]
                    # GeoJSON uses [lon, lat], we need [lat, lon]
                    coordinates = [[coord[1], coord[0]] for coord in coords]
        
        if not coordinates:
            logger.error(f"Could not find valid coordinates in {file_path}")
            return None
            
        logger.info(f"Loaded {len(coordinates)} coordinates from {file_path}")
        return coordinates
        
    except Exception as e:
        logger.error(f"Error loading coordinates: {e}")
        return None

def create_poly_string(coordinates):
    """
    Convert coordinates list to an Overpass QL polygon string.
    
    Args:
        coordinates: List of [lat, lon] pairs
        
    Returns:
        String in the format "lat1 lon1 lat2 lon2 ..." for Overpass QL poly filter
    """
    if not coordinates:
        return ""
    
    # Format each coordinate pair and join with spaces
    poly_string = " ".join([f"{lat} {lon}" for lat, lon in coordinates])
    logger.info(f"Created poly string with {len(coordinates)} points")
    
    return poly_string

def process_search_area(file_path=SEARCH_AREA_PATH):
    """
    Process the search area file and generate a poly string.
    
    Args:
        file_path: Path to the JSON file containing coordinates
        
    Returns:
        Poly string for Overpass QL or empty string if failed
    """
    coordinates = load_coordinates(file_path)
    if not coordinates:
        return ""
    
    return create_poly_string(coordinates)

def main():
    """Main function to run when script is executed directly."""
    poly_string = process_search_area()
    if poly_string:
        print(f"Poly string: {poly_string}")
        
        # Save to a file for use in other scripts
        output_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(output_dir, "poly_string.txt")
        
        with open(output_path, 'w') as f:
            f.write(poly_string)
        logger.info(f"Saved poly string to {output_path}")
        
        # Return the poly string for use in other scripts
        return poly_string
    else:
        logger.error("Failed to create poly string.")
        return ""

if __name__ == "__main__":
    main()
