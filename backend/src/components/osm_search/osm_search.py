#!/usr/bin/env python3
"""
OSM Search Area Processor

This module loads search area coordinates and converts them into the Overpass QL polygon format.
It also substitutes the polygon string into Overpass QL queries and executes them.
Can be used as a standalone script or imported for use in other modules.
"""

import os
import json
import logging
import overpy
import geojson
from pathlib import Path
import argparse
from typing import Dict, List, Tuple, Union, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Determine search area path - prioritize environment variable
ENV_SEARCH_AREA_PATH = os.environ.get("OSM_SEARCH_AREA_PATH")
DEFAULT_SEARCH_AREA_PATH = "/Users/harveypitt/Documents/Alive Industries/Repos/sandhack/Competition Release/Reading_1_cleaned_search_area.json"
SEARCH_AREA_PATH = ENV_SEARCH_AREA_PATH if ENV_SEARCH_AREA_PATH else DEFAULT_SEARCH_AREA_PATH

# Default file paths
QUERY_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "osm_search.json")
OUTPUT_QUERY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "final_query.txt")


class OSMSearchProcessor:
    """
    Processes search areas and Overpass QL queries to retrieve OSM data.
    Can be used programmatically or via command line.
    """
    
    def __init__(self, search_area_path=None, query_template_path=None):
        """
        Initialize the OSM Search Processor.
        
        Args:
            search_area_path: Path to the search area GeoJSON file (optional)
            query_template_path: Path to the query template JSON file (optional)
        """
        self.search_area_path = search_area_path or SEARCH_AREA_PATH
        self.query_template_path = query_template_path or QUERY_TEMPLATE_PATH
        self.api = overpy.Overpass()
        
        # Log which search area path we're using
        if search_area_path:
            logger.info(f"Using provided search area path: {self.search_area_path}")
        elif ENV_SEARCH_AREA_PATH:
            logger.info(f"Using search area path from environment variable: {self.search_area_path}")
        else:
            logger.info(f"Using default search area path: {self.search_area_path}")
    
    def load_coordinates_from_file(self, file_path=None, feature_index=0):
        """
        Load search area coordinates from a JSON file.
        
        Args:
            file_path: Path to the JSON file containing coordinates (defaults to self.search_area_path)
            feature_index: Index of the feature to use (for GeoJSON FeatureCollection)
            
        Returns:
            List of coordinates (lat, lon pairs) or None if failed
        """
        # Use provided path or fall back to instance path
        if file_path is None:
            file_path = self.search_area_path
        
        logger.info(f"Loading coordinates from file: {file_path} (feature index: {feature_index})")
        
        try:
            if not os.path.exists(file_path):
                logger.error(f"Coordinates file not found: {file_path}")
                return None
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            return self._extract_coordinates_from_data(data, feature_index)
                
        except Exception as e:
            logger.error(f"Error loading coordinates from file: {e}")
            return None
    
    def load_coordinates_from_geojson(self, geojson_data, feature_index=0):
        """
        Load search area coordinates directly from a GeoJSON object.
        
        Args:
            geojson_data: GeoJSON data as a Python dictionary
            feature_index: Index of the feature to use (for GeoJSON FeatureCollection)
            
        Returns:
            List of coordinates (lat, lon pairs) or None if failed
        """
        logger.info(f"Loading coordinates from GeoJSON data (feature index: {feature_index})")
        
        try:
            return self._extract_coordinates_from_data(geojson_data, feature_index)
                
        except Exception as e:
            logger.error(f"Error loading coordinates from GeoJSON data: {e}")
            return None
    
    def _extract_coordinates_from_data(self, data, feature_index=0):
        """
        Extract coordinates from JSON/GeoJSON data.
        
        Args:
            data: JSON/GeoJSON data as a Python dictionary
            feature_index: Index of the feature to use (for GeoJSON FeatureCollection)
            
        Returns:
            List of coordinates (lat, lon pairs) or None if failed
        """
        # Try to use geojson library if available
        try:
            gj = geojson.loads(json.dumps(data))
            if hasattr(gj, 'features') and len(gj.features) > 0:
                # FeatureCollection
                if feature_index >= len(gj.features):
                    logger.error(f"Feature index {feature_index} is out of range (0-{len(gj.features)-1})")
                    return None
                
                feature = gj.features[feature_index]
                if feature.geometry.type == 'Polygon':
                    # Get first (outer) ring of polygon
                    coords = feature.geometry.coordinates[0]
                    # GeoJSON uses [lon, lat], we need [lat, lon]
                    coordinates = [[coord[1], coord[0]] for coord in coords]
                    logger.info(f"Loaded {len(coordinates)} coordinates from feature {feature_index} using geojson library")
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
            if feature_index >= len(data['features']):
                logger.error(f"Feature index {feature_index} is out of range (0-{len(data['features'])-1})")
                return None
                
            feature = data['features'][feature_index]
            if 'geometry' in feature and 'coordinates' in feature['geometry']:
                coords = feature['geometry']['coordinates']
                if len(coords) > 0:
                    # For Polygon type, get the first (outer) ring
                    if feature['geometry']['type'] == 'Polygon':
                        coords = coords[0]
                    # GeoJSON uses [lon, lat], we need [lat, lon]
                    coordinates = [[coord[1], coord[0]] for coord in coords]
        
        if not coordinates:
            logger.error("Could not find valid coordinates in the provided data")
            return None
            
        logger.info(f"Loaded {len(coordinates)} coordinates (feature index: {feature_index})")
        return coordinates

    def create_poly_string(self, coordinates):
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

    def load_query_template_from_file(self, file_path=None):
        """
        Load Overpass QL query template from a JSON file.
        
        Args:
            file_path: Path to the JSON file containing the query template
            
        Returns:
            Query string or None if failed
        """
        if file_path is None:
            file_path = self.query_template_path
            
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

    def substitute_poly_string(self, query_template, poly_string):
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

    def convert_to_geojson(self, overpy_result):
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
        geojson_result = {
            "type": "FeatureCollection",
            "features": features
        }
        
        return geojson_result

    def execute_query(self, query):
        """
        Execute an Overpass QL query and return both the raw result and GeoJSON.
        
        Args:
            query: Overpass QL query string
            
        Returns:
            Tuple of (overpy_result, geojson_dict) or (None, None) if failed
        """
        try:
            logger.info("Executing Overpass query...")
            result = self.api.query(query)
            logger.info(f"Query executed successfully! Found {len(result.nodes)} nodes, {len(result.ways)} ways, and {len(result.relations)} relations.")
            
            # Convert to GeoJSON
            geojson_data = self.convert_to_geojson(result)
            logger.info(f"Converted to GeoJSON with {len(geojson_data['features'])} features.")
            
            return result, geojson_data
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            print("The query could not be executed automatically.")
            print("You can copy the query and execute it manually at https://overpass-turbo.eu/")
            return None, None
    
    def save_query_to_file(self, query, output_path):
        """
        Save an Overpass QL query to a file.
        
        Args:
            query: Overpass QL query string
            output_path: Path to save the query to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(query)
            logger.info(f"Saved query to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving query to file: {e}")
            return False
    
    def save_geojson_to_file(self, geojson_data, output_path):
        """
        Save GeoJSON data to a file.
        
        Args:
            geojson_data: GeoJSON data as a Python dictionary
            output_path: Path to save the GeoJSON to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(geojson_data, f, indent=2)
            logger.info(f"Saved GeoJSON data to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving GeoJSON data to file: {e}")
            return False
    
    def process_search_area_from_file(self, file_path=None, feature_index=0):
        """
        Process a search area file and generate a poly string.
        
        Args:
            file_path: Path to the JSON file containing coordinates
            feature_index: Index of the feature to use (for GeoJSON FeatureCollection)
            
        Returns:
            Poly string for Overpass QL or empty string if failed
        """
        coordinates = self.load_coordinates_from_file(file_path, feature_index)
        if not coordinates:
            return ""
        
        return self.create_poly_string(coordinates)
    
    def process_search_area_from_geojson(self, geojson_data, feature_index=0):
        """
        Process a GeoJSON search area directly and generate a poly string.
        
        Args:
            geojson_data: GeoJSON data as a Python dictionary
            feature_index: Index of the feature to use (for GeoJSON FeatureCollection)
            
        Returns:
            Poly string for Overpass QL or empty string if failed
        """
        coordinates = self.load_coordinates_from_geojson(geojson_data, feature_index)
        if not coordinates:
            return ""
        
        return self.create_poly_string(coordinates)
    
    def process_query(self, query=None, query_template=None, poly_string=None, search_area_file=None, 
                     search_area_geojson=None, feature_index=0):
        """
        Process and execute an Overpass QL query.
        
        Args:
            query: Direct Overpass QL query string (highest priority)
            query_template: Overpass QL query template with {poly_string} placeholder
            poly_string: Polygon string to substitute in the query template
            search_area_file: Path to the search area GeoJSON file
            search_area_geojson: GeoJSON search area as a Python dictionary
            feature_index: Index of the feature to use (for GeoJSON FeatureCollection)
            
        Returns:
            Tuple of (final_query, overpy_result, geojson_data) or (None, None, None) if failed
        """
        final_query = query
        
        # Generate poly_string if not provided
        if not poly_string:
            if search_area_geojson:
                poly_string = self.process_search_area_from_geojson(search_area_geojson, feature_index)
            elif search_area_file:
                poly_string = self.process_search_area_from_file(search_area_file, feature_index)
            else:
                poly_string = self.process_search_area_from_file(self.search_area_path, feature_index)
                
        if not poly_string:
            logger.error("Could not generate polygon string")
            return None, None, None
            
        # If direct query contains {poly_string} placeholder, substitute it
        if final_query and "{poly_string}" in final_query:
            logger.info("Substituting poly_string in direct query")
            final_query = self.substitute_poly_string(final_query, poly_string)
        
        # If no direct query is provided, try to build one from template and polygon
        elif not final_query and query_template:
            final_query = self.substitute_poly_string(query_template, poly_string)
        
        # If we still don't have a query, try to load the template from file
        elif not final_query:
            query_template = self.load_query_template_from_file()
            
            if not query_template:
                logger.error("Could not generate query: missing template")
                return None, None, None
            
            final_query = self.substitute_poly_string(query_template, poly_string)
        
        if not final_query:
            logger.error("Could not generate final query")
            return None, None, None
        
        # Execute the query
        result, geojson_data = self.execute_query(final_query)
        
        return final_query, result, geojson_data


def main():
    """Main function to run when script is executed directly."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Process search area and generate Overpass QL query")
    parser.add_argument("--search-area", default=None, 
                      help="Path to the search area JSON file (overrides default and environment variable)")
    parser.add_argument("--query-template", default=QUERY_TEMPLATE_PATH,
                      help=f"Path to the query template JSON file (default: {QUERY_TEMPLATE_PATH})")
    parser.add_argument("--output-query", default=OUTPUT_QUERY_PATH,
                      help=f"Path to save the final query (default: {OUTPUT_QUERY_PATH})")
    parser.add_argument("--output-geojson", 
                      default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "query_result.geojson"),
                      help="Path to save the GeoJSON results")
    parser.add_argument("--feature-index", type=int, default=0,
                      help="Index of the feature to use from the GeoJSON FeatureCollection (default: 0)")
    parser.add_argument("--direct-query", default=None,
                      help="Path to a file containing a direct Overpass QL query to execute (bypasses template and search area)")
    args = parser.parse_args()
    
    # Create processor with search area and query template
    processor = OSMSearchProcessor(
        search_area_path=args.search_area,
        query_template_path=args.query_template
    )
    
    # If direct query file is provided, load it and use it
    direct_query = None
    if args.direct_query:
        try:
            with open(args.direct_query, 'r') as f:
                direct_query = f.read()
            logger.info(f"Loaded direct query from {args.direct_query}")
        except Exception as e:
            logger.error(f"Error loading direct query: {e}")
            return False
    
    # Process the query
    final_query, result, geojson_data = processor.process_query(
        query=direct_query,
        search_area_file=args.search_area,
        feature_index=args.feature_index
    )
    
    if not final_query:
        logger.error("Failed to generate final query.")
        return False
    
    # Save the final query
    processor.save_query_to_file(final_query, args.output_query)
    
    if not result or not geojson_data:
        logger.error("Failed to execute query or convert results to GeoJSON.")
        return False
    
    # Save the GeoJSON results
    processor.save_geojson_to_file(geojson_data, args.output_geojson)
    
    print("Process completed successfully!")
    return True


if __name__ == "__main__":
    success = main()
    if success:
        print("Process completed successfully!")
    else:
        print("Process completed with errors. Check the logs for details.")