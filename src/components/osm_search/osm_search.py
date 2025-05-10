#!/usr/bin/env python3
"""
OSM Search Area Processor

This module loads search area coordinates and converts them into the Overpass QL polygon format.
It also substitutes the polygon string into Overpass QL queries.
"""

import os
import json
import logging
import overpy
import geojson
from pathlib import Path

# Configure logging

logger = logging.getLogger(__name__)

# Hardcoded paths
SEARCH_AREA_PATH = "/Users/harveypitt/Documents/Alive Industries/Repos/sandhack/data/example/images/rickmansworth_example_search_area.json"
QUERY_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "osm_search.json")
OUTPUT_QUERY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "final_query.txt")

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

def load_query_template(file_path=QUERY_TEMPLATE_PATH):
    """
    Load Overpass QL query template from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing the query template
        
    Returns:
        Query string or None if failed
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"Query template file not found: {file_path}")
            return None
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if 'query' in data and isinstance(data['query'], str):
            logger.info(f"Loaded query template from {file_path}")
            return data['query']
        else:
            logger.error(f"No 'query' field found in {file_path}")
            return None
            
    except Exception as e:
        logger.error(f"Error loading query template: {e}")
        return None

def substitute_poly_string(query_template, poly_string):
    """
    Replace {poly_string} placeholder in query template with actual polygon string.
    
    Args:
        query_template: Overpass QL query with {poly_string} placeholder
        poly_string: Polygon string to substitute
        
    Returns:
        Final query with polygon string substituted
    """
    if not query_template or not poly_string:
        return ""
    
    final_query = query_template.replace("{poly_string}", poly_string)
    logger.info("Substituted polygon string into query template")
    
    return final_query

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

def convert_to_geojson(overpy_result):
    """
    Convert Overpy result to GeoJSON format.
    
    Args:
        overpy_result: Result from Overpy query
        
    Returns:
        GeoJSON FeatureCollection as a dictionary
    """
    features = []
    
    # Process nodes
    for node in overpy_result.nodes:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(node.lon), float(node.lat)]
            },
            "properties": {
                "id": node.id,
                "type": "node"
            }
        }
        
        # Add tags as properties
        for key, value in node.tags.items():
            feature["properties"][key] = value
            
        features.append(feature)
    
    # Process ways - can be linestrings or polygons
    for way in overpy_result.ways:
        # Extract coordinates from nodes in the way
        coords = [[float(node.lon), float(node.lat)] for node in way.nodes]
        
        # Determine if it's a polygon (closed way) or linestring
        geometry_type = "Polygon" if len(coords) > 2 and coords[0] == coords[-1] else "LineString"
        
        # For polygons, coordinates need to be in an extra array level
        geometry = {
            "type": geometry_type,
            "coordinates": [coords] if geometry_type == "Polygon" else coords
        }
        
        feature = {
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "id": way.id,
                "type": "way"
            }
        }
        
        # Add tags as properties
        for key, value in way.tags.items():
            feature["properties"][key] = value
            
        features.append(feature)
    
    # Process relations - more complex, but basic support
    for relation in overpy_result.relations:
        properties = {
            "id": relation.id,
            "type": "relation"
        }
        
        # Add tags as properties
        for key, value in relation.tags.items():
            properties[key] = value
        
        # For now, just add the relation as a property collection without geometry
        # Full relation geometry processing is complex and would need each member
        # to be processed based on its role and type
        feature = {
            "type": "Feature",
            "geometry": None,
            "properties": properties
        }
        
        features.append(feature)
    
    # Create the GeoJSON FeatureCollection
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    return geojson

def execute_query(query):
    """
    Execute an Overpass QL query and return both the raw result and GeoJSON.
    
    Args:
        query: Overpass QL query string
        
    Returns:
        Tuple of (overpy_result, geojson_dict) or (None, None) if failed
    """
    try:
        print("Executing Overpass query...")
        api = overpy.Overpass()
        result = api.query(query)
        print(f"Query executed successfully! Found {len(result.nodes)} nodes, {len(result.ways)} ways, and {len(result.relations)} relations.")
        
        # Convert to GeoJSON
        geojson_data = convert_to_geojson(result)
        print(f"Converted to GeoJSON with {len(geojson_data['features'])} features.")
        
        return result, geojson_data
        
    except Exception as e:
        logger.warning(f"Could not execute query: {e}")
        print("The query could not be executed automatically.")
        print("You can copy the query and execute it manually at https://overpass-turbo.eu/")
        return None, None

def main():
    """Main function to run when script is executed directly."""
    # Step 1: Generate the polygon string
    poly_string = process_search_area()
    if not poly_string:
        logger.error("Failed to create polygon string.")
        return False
    
    print(f"Polygon string created: {poly_string[:60]}... ({len(poly_string)} chars)")
    
    # Save the poly string to a file
    poly_string_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "poly_string.txt")
    with open(poly_string_path, 'w') as f:
        f.write(poly_string)
    logger.info(f"Saved polygon string to {poly_string_path}")
    
    # Step 2: Load the query template
    query_template = load_query_template()
    if not query_template:
        logger.error("Failed to load query template.")
        return False
    
    # Step 3: Substitute the polygon string into the query
    final_query = substitute_poly_string(query_template, poly_string)
    if not final_query:
        logger.error("Failed to substitute polygon string into query.")
        return False
    
    print(f"Final query created: {final_query[:100]}... ({len(final_query)} chars)")
    
    # Step 4: Save the final query
    with open(OUTPUT_QUERY_PATH, 'w') as f:
        f.write(final_query)
    print(f"Saved final query to {OUTPUT_QUERY_PATH}")
    
    # Step 5: Execute the query and convert to GeoJSON
    result, geojson_data = execute_query(final_query)
    if result and geojson_data:
        # Save the GeoJSON data
        geojson_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "query_result.geojson")
        with open(geojson_path, 'w') as f:
            json.dump(geojson_data, f, indent=2)
        print(f"Saved GeoJSON results to {geojson_path}")
        return True
    else:
        print("Could not generate GeoJSON results.")
        return False

if __name__ == "__main__":
    # Configure logging for main execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = main()
    if success:
        print("Process completed successfully!")
    else:
        print("Process completed with errors. Check the logs for details.")
