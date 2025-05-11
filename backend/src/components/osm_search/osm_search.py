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
import requests
import time
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

# Groq API related constants
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


class OSMSearchProcessor:
    """
    Processes search areas and Overpass QL queries to retrieve OSM data.
    Can be used programmatically or via command line.
    """
    
    def __init__(self, search_area_path=None, query_template_path=None, max_retries=3):
        """
        Initialize the OSM Search Processor.
        
        Args:
            search_area_path: Path to the search area GeoJSON file (optional)
            query_template_path: Path to the query template JSON file (optional)
            max_retries: Maximum number of times to retry with broadened query (default: 3)
        """
        self.search_area_path = search_area_path or SEARCH_AREA_PATH
        self.query_template_path = query_template_path or QUERY_TEMPLATE_PATH
        self.api = overpy.Overpass()
        self.max_retries = max_retries
        
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

    def broaden_query_with_llm(self, original_query, retry_count):
        """
        Use Groq API with Llama 3.3 to rewrite and broaden the Overpass QL query.
        
        Args:
            original_query: Original Overpass QL query string
            retry_count: Current retry attempt number
            
        Returns:
            Broadened query string or None if failed
        """
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            logger.error("GROQ_API_KEY environment variable not set")
            return None
            
        logger.info(f"Attempt {retry_count}: Using Groq with Llama 3.3 to broaden query")
        
        # Construct the prompt
        prompt = f"""You are an expert in OpenStreetMap data and Overpass QL queries. 
        This Overpass QL query returned 0 results:
        
        ```
        {original_query}
        ```
        
        Please rewrite this query to be slightly broader in scope, retaining the same general search area and intent, 
        but being more inclusive of potentially relevant features. This is attempt {retry_count} of {self.max_retries}, 
        so {self.max_retries-retry_count} more attempts remain. 
        
        For attempt {retry_count}, broaden the query {'moderately' if retry_count == 1 else 'significantly' if retry_count == 2 else 'very significantly'}.
        
        Return ONLY the rewritten Overpass QL query with no other text or explanation.
        """
        
        # Try using the native Groq client if available
        try:
            import groq
            logger.info("Using native Groq client")
            client = groq.Groq(api_key=api_key)
            
            completion = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert in OpenStreetMap data and Overpass QL queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1024
            )
            
            broadened_query = completion.choices[0].message.content.strip()
            
            # Clean up the query in case it has markdown formatting
            if broadened_query.startswith("```"):
                broadened_query = broadened_query.strip("```")
                # Remove any language identifier like "overpass" after the first ```
                broadened_query = "\n".join(broadened_query.split("\n")[1:]) if "\n" in broadened_query else broadened_query
                
            if broadened_query.endswith("```"):
                broadened_query = broadened_query.strip("```")
            
            # Further cleaning
            broadened_query = broadened_query.replace("```overpass", "").replace("```", "").strip()
            
            logger.info(f"Successfully generated broadened query (attempt {retry_count}) with native Groq client")
            return broadened_query
            
        except ImportError:
            logger.info("Native Groq client not available, falling back to requests")
            # Fall back to using requests if groq is not installed
            # Create the API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            data = {
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": "You are an expert in OpenStreetMap data and Overpass QL queries."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1024
            }
            
            # Make the API request
            try:
                response = requests.post(GROQ_API_URL, headers=headers, json=data)
                response.raise_for_status()
                
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    broadened_query = result['choices'][0]['message']['content'].strip()
                    
                    # Clean up the query in case it has markdown formatting
                    if broadened_query.startswith("```"):
                        broadened_query = broadened_query.strip("```")
                        # Remove any language identifier like "overpass" after the first ```
                        broadened_query = "\n".join(broadened_query.split("\n")[1:]) if "\n" in broadened_query else broadened_query
                        
                    if broadened_query.endswith("```"):
                        broadened_query = broadened_query.strip("```")
                    
                    # Further cleaning
                    broadened_query = broadened_query.replace("```overpass", "").replace("```", "").strip()
                    
                    logger.info(f"Successfully generated broadened query (attempt {retry_count})")
                    return broadened_query
                else:
                    logger.error(f"Unexpected response format from Groq API: {result}")
                    return None
                    
            except Exception as e:
                logger.error(f"Error calling Groq API: {e}")
                return None
        except Exception as e:
            logger.error(f"Error with native Groq client: {e}, falling back to requests")
            
            # Create the API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            data = {
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": "You are an expert in OpenStreetMap data and Overpass QL queries."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1024
            }
            
            # Make the API request
            try:
                response = requests.post(GROQ_API_URL, headers=headers, json=data)
                response.raise_for_status()
                
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    broadened_query = result['choices'][0]['message']['content'].strip()
                    
                    # Clean up the query in case it has markdown formatting
                    if broadened_query.startswith("```"):
                        broadened_query = broadened_query.strip("```")
                        # Remove any language identifier like "overpass" after the first ```
                        broadened_query = "\n".join(broadened_query.split("\n")[1:]) if "\n" in broadened_query else broadened_query
                        
                    if broadened_query.endswith("```"):
                        broadened_query = broadened_query.strip("```")
                    
                    # Further cleaning
                    broadened_query = broadened_query.replace("```overpass", "").replace("```", "").strip()
                    
                    logger.info(f"Successfully generated broadened query (attempt {retry_count})")
                    return broadened_query
                else:
                    logger.error(f"Unexpected response format from Groq API: {result}")
                    return None
                    
            except Exception as e:
                logger.error(f"Error calling Groq API: {e}")
                return None

    def execute_query(self, query, retry=True):
        """
        Execute an Overpass QL query and return both the raw result and GeoJSON.
        Optionally retry with broadened queries if no results are found.
        
        Args:
            query: Overpass QL query string
            retry: Whether to retry with broadened queries if no results are found
            
        Returns:
            Tuple of (overpy_result, geojson_dict, final_query) or (None, None, None) if failed
        """
        try:
            logger.info("Executing Overpass query...")
            result = self.api.query(query)
            
            total_features = len(result.nodes) + len(result.ways) + len(result.relations)
            logger.info(f"Query executed successfully! Found {len(result.nodes)} nodes, {len(result.ways)} ways, and {len(result.relations)} relations.")
            
            # If no features were found and retry is enabled, try broadening the query
            if total_features == 0 and retry:
                logger.warning("No features found. Will attempt to broaden the query.")
                
                current_query = query
                for retry_count in range(1, self.max_retries + 1):
                    # Try to broaden the query using LLM
                    broadened_query = self.broaden_query_with_llm(current_query, retry_count)
                    
                    if not broadened_query:
                        logger.error(f"Failed to broaden query on attempt {retry_count}")
                        continue
                        
                    # Save the broadened query for reference
                    broadened_query_path = os.path.join(
                        os.path.dirname(os.path.abspath(OUTPUT_QUERY_PATH)), 
                        f"broadened_query_attempt_{retry_count}.txt"
                    )
                    self.save_query_to_file(broadened_query, broadened_query_path)
                    
                    # Execute the broadened query
                    logger.info(f"Executing broadened query (attempt {retry_count})...")
                    
                    try:
                        new_result = self.api.query(broadened_query)
                        new_total_features = len(new_result.nodes) + len(new_result.ways) + len(new_result.relations)
                        
                        logger.info(f"Broadened query executed successfully! Found {len(new_result.nodes)} nodes, "
                                   f"{len(new_result.ways)} ways, and {len(new_result.relations)} relations.")
                        
                        # If we found features, use this result
                        if new_total_features > 0:
                            logger.info(f"Broadened query successful on attempt {retry_count}! Found {new_total_features} features.")
                            result = new_result
                            query = broadened_query  # Update the query to the successful one
                            break
                            
                        # Update current query for next iteration
                        current_query = broadened_query
                        
                    except Exception as e:
                        logger.error(f"Error executing broadened query (attempt {retry_count}): {e}")
                        # Continue to the next retry attempt
                        
                    # Small delay between retry attempts
                    if retry_count < self.max_retries:
                        time.sleep(1)
            
            # Convert to GeoJSON
            geojson_data = self.convert_to_geojson(result)
            total_features = len(result.nodes) + len(result.ways) + len(result.relations)
            logger.info(f"Converted to GeoJSON with {len(geojson_data['features'])} features.")
            
            return result, geojson_data, query
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            print("The query could not be executed automatically.")
            print("You can copy the query and execute it manually at https://overpass-turbo.eu/")
            return None, None, None
    
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
                     search_area_geojson=None, feature_index=0, disable_retry=False):
        """
        Process and execute an Overpass QL query.
        
        Args:
            query: Direct Overpass QL query string (highest priority)
            query_template: Overpass QL query template with {poly_string} placeholder
            poly_string: Polygon string to substitute in the query template
            search_area_file: Path to the search area GeoJSON file
            search_area_geojson: GeoJSON search area as a Python dictionary
            feature_index: Index of the feature to use (for GeoJSON FeatureCollection)
            disable_retry: If True, won't retry with broadened queries if no results are found
            
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
        
        # Execute the query with retry
        result, geojson_data, used_query = self.execute_query(final_query, retry=not disable_retry)
        
        return used_query, result, geojson_data


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
    parser.add_argument("--max-retries", type=int, default=3,
                      help="Maximum number of times to retry with broadened query if no results are found (default: 3)")
    parser.add_argument("--disable-retry", action="store_true",
                      help="Disable retrying with broadened queries if no results are found")
    args = parser.parse_args()
    
    # Create processor with search area and query template
    processor = OSMSearchProcessor(
        search_area_path=args.search_area,
        query_template_path=args.query_template,
        max_retries=args.max_retries
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
        feature_index=args.feature_index,
        disable_retry=args.disable_retry
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