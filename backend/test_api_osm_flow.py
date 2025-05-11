#!/usr/bin/env python3
"""
Test script for the OSM API Flow

This script tests the complete OSM API flow by:
1. Calling the /osm/generate-query endpoint with an image to generate an Overpass QL query
2. Calling the /osm/search endpoint with the query and a search area to get OSM nodes

Usage:
    python test_api_osm_flow.py --image path/to/image.jpg --search-area path/to/search_area.json

Example:
    python test_api_osm_flow.py --image "../Competition Release/Reading_1_cleaned.jpg" \
                                --search-area "../Competition Release/Reading_1_cleaned_search_area.json" \
                                --output-dir "./osm_api_results"
"""

import os
import sys
import json
import argparse
import logging
import time
import requests
from pathlib import Path
from typing import Dict, Optional, Union, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OSMAPITester:
    """
    Tests the complete OSM API flow by calling endpoints sequentially.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", output_dir: Optional[str] = None):
        """
        Initialize the API tester.
        
        Args:
            base_url: Base URL of the API (default: http://localhost:8000)
            output_dir: Directory to store output files (default: ./osm_api_results)
        """
        self.base_url = base_url
        self.output_dir = output_dir or os.path.join(os.getcwd(), "osm_api_results")
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(f"API tester initialized. Base URL: {self.base_url}, Output directory: {self.output_dir}")
    
    def generate_query(self, image_path: str) -> Union[str, None]:
        """
        Call the /osm/generate-query endpoint to generate an Overpass QL query from an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Generated Overpass QL query or None if failed
        """
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None
        
        logger.info(f"Generating query from image: {image_path}")
        
        try:
            # Prepare the image file
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            files = {
                'image': (os.path.basename(image_path), image_data, 'image/jpeg')
            }
            
            # Make the API request
            endpoint = f"{self.base_url}/osm/generate-query"
            logger.info(f"Calling endpoint: {endpoint}")
            
            response = requests.post(endpoint, files=files)
            response.raise_for_status()
            
            result = response.json()
            
            if 'query' not in result:
                logger.error("No query in response")
                return None
            
            query = result['query']
            logger.info(f"Generated query ({len(query)} chars)")
            
            # Save the query to a file
            query_path = os.path.join(self.output_dir, "generated_query.txt")
            with open(query_path, 'w') as f:
                f.write(query)
            logger.info(f"Saved query to: {query_path}")
            
            # Save the full API response to a file
            response_path = os.path.join(self.output_dir, "generate_query_response.json")
            with open(response_path, 'w') as f:
                json.dump(result, f, indent=2)
            logger.info(f"Saved full response to: {response_path}")
            
            return query
            
        except Exception as e:
            logger.error(f"Error generating query: {e}")
            return None
    
    def search_with_query(self, search_area_path: str, query: str, feature_index: int = 0) -> Dict:
        """
        Call the /osm/search endpoint to get OSM nodes based on a query and search area.
        
        Args:
            search_area_path: Path to the search area GeoJSON file
            query: Overpass QL query to use
            feature_index: Index of the feature to use from GeoJSON FeatureCollection
            
        Returns:
            API response as a dictionary or None if failed
        """
        if not os.path.exists(search_area_path):
            logger.error(f"Search area file not found: {search_area_path}")
            return None
        
        logger.info(f"Searching with query and search area: {search_area_path}")
        
        try:
            # Prepare the search area file
            with open(search_area_path, 'rb') as f:
                search_area_data = f.read()
            
            files = {
                'search_area': (os.path.basename(search_area_path), search_area_data, 'application/json')
            }
            
            # Prepare form data with query and feature_index
            data = {
                'query': query,
                'feature_index': feature_index
            }
            
            # Make the API request
            endpoint = f"{self.base_url}/osm/search"
            logger.info(f"Calling endpoint: {endpoint}")
            
            response = requests.post(endpoint, files=files, data=data)
            response.raise_for_status()
            
            result = response.json()
            
            if 'geojson' not in result:
                logger.error("No GeoJSON in response")
                return None
            
            # Save the GeoJSON to a file
            geojson_path = os.path.join(self.output_dir, "search_results.geojson")
            with open(geojson_path, 'w') as f:
                json.dump(result['geojson'], f, indent=2)
            logger.info(f"Saved GeoJSON results to: {geojson_path}")
            
            # Save the full API response to a file
            response_path = os.path.join(self.output_dir, "search_response.json")
            with open(response_path, 'w') as f:
                json.dump(result, f, indent=2)
            logger.info(f"Saved full response to: {response_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error searching with query: {e}")
            return None
    
    def run_complete_flow(self, image_path: str, search_area_path: str, feature_index: int = 0) -> bool:
        """
        Run the complete OSM API flow:
        1. Generate query from image
        2. Search with query and search area
        
        Args:
            image_path: Path to the image file
            search_area_path: Path to the search area GeoJSON file
            feature_index: Index of the feature to use from GeoJSON FeatureCollection
            
        Returns:
            True if successful, False otherwise
        """
        print(f"\n=== Running complete OSM API flow ===")
        print(f"Image: {image_path}")
        print(f"Search Area: {search_area_path}")
        print(f"Feature Index: {feature_index}")
        print(f"Base URL: {self.base_url}")
        print(f"Output Directory: {self.output_dir}")
        print()
        
        # Step 1: Generate query from image
        start_time = time.time()
        query = self.generate_query(image_path)
        query_time = time.time() - start_time
        
        if not query:
            print(f"\n❌ Failed to generate query from image")
            return False
        
        print(f"\n✓ Generated Overpass QL query ({len(query)} chars) in {query_time:.2f} seconds")
        
        # Step 2: Search with query and search area
        start_time = time.time()
        result = self.search_with_query(search_area_path, query, feature_index)
        search_time = time.time() - start_time
        
        if not result:
            print(f"\n❌ Failed to search with query and search area")
            return False
        
        # Print results summary
        if 'stats' in result:
            stats = result['stats']
            print(f"\n✓ Search completed in {search_time:.2f} seconds!")
            print(f"Found {stats.get('nodes', 0)} nodes, {stats.get('ways', 0)} ways, and {stats.get('relations', 0)} relations")
            print(f"Generated GeoJSON with {stats.get('features', 0)} features")
        else:
            print(f"\n✓ Search completed in {search_time:.2f} seconds!")
        
        print(f"\nTotal flow time: {query_time + search_time:.2f} seconds")
        
        # Print output file locations
        print(f"\nOutput files:")
        print(f"  Query: {os.path.join(self.output_dir, 'generated_query.txt')}")
        print(f"  Query Response: {os.path.join(self.output_dir, 'generate_query_response.json')}")
        print(f"  GeoJSON Results: {os.path.join(self.output_dir, 'search_results.geojson')}")
        print(f"  Search Response: {os.path.join(self.output_dir, 'search_response.json')}")
        
        return True

def main():
    """Main function to run the test script."""
    parser = argparse.ArgumentParser(description="Test the OSM API flow")
    parser.add_argument("--image", required=True, help="Path to the image file")
    parser.add_argument("--search-area", required=True, help="Path to the search area GeoJSON file")
    parser.add_argument("--feature-index", type=int, default=0, 
                      help="Index of the feature to use from GeoJSON FeatureCollection (default: 0)")
    parser.add_argument("--base-url", default="http://localhost:8000", 
                      help="Base URL of the API (default: http://localhost:8000)")
    parser.add_argument("--output-dir", help="Directory to store output files")
    args = parser.parse_args()
    
    # Create the API tester
    tester = OSMAPITester(args.base_url, args.output_dir)
    
    # Run the complete flow
    success = tester.run_complete_flow(args.image, args.search_area, args.feature_index)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 