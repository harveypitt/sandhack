#!/usr/bin/env python3
"""
Test OSM Pipeline

This script tests the complete pipeline:
1. Generate Overpass QL query from an image using contextual_analyzer.py
2. Process the search area coordinates and substitute them into the query using osm_search.py
"""

import os
import sys
import json
import argparse
import logging
import time
from pathlib import Path
from dotenv import load_dotenv

# Add the src directory to the Python path so we can import our modules
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Use the absolute path to Competition Release
COMPETITION_DIR = "/Users/harveypitt/Documents/Alive Industries/Repos/sandhack/Competition Release"

# Import our modules
from backend.src.components.osm_search.osm_search import OSMSearchProcessor
from backend.src.components.llm_analysis.contextual_analyzer import LLMContextualAnalyzer

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Location mapping dictionary
LOCATIONS = {
    "Reading_1": {
        "image": os.path.join(COMPETITION_DIR, "Reading_1_cleaned.jpg"),
        "search_area": os.path.join(COMPETITION_DIR, "Reading_1_cleaned_search_area.json")
    },
    "Reading_2": {
        "image": os.path.join(COMPETITION_DIR, "Reading_2_cleaned.jpg"),
        "search_area": os.path.join(COMPETITION_DIR, "Reading_2_cleaned_search_area.json")
    },
    "Reading_3": {
        "image": os.path.join(COMPETITION_DIR, "Reading_3_cleaned.jpg"),
        "search_area": os.path.join(COMPETITION_DIR, "Reading_3_cleaned_search_area.json")
    },
    "Reading_4": {
        "image": os.path.join(COMPETITION_DIR, "Reading_4_cleaned.jpg"),
        "search_area": os.path.join(COMPETITION_DIR, "Reading_4_cleaned_search_area.json")
    },
    "Reading_5": {
        "image": os.path.join(COMPETITION_DIR, "Reading_5_cleaned.jpg"),
        "search_area": os.path.join(COMPETITION_DIR, "Reading_5_cleaned_search_area.json")
    },
    "Rickmansworth_2": {
        "image": os.path.join(COMPETITION_DIR, "Rickmansworth_2_cleaned.jpg"),
        "search_area": os.path.join(COMPETITION_DIR, "Rickmansworth_2_cleaned_search_area.json")
    },
    "Rickmansworth_3": {
        "image": os.path.join(COMPETITION_DIR, "Rickmansworth_3_cleaned.jpg"),
        "search_area": os.path.join(COMPETITION_DIR, "Rickmansworth_3_cleaned_search_area.json")
    }
}

class OSMPipelineTester:
    """
    Tests the complete OSM pipeline by integrating the contextual analyzer and OSM search.
    """
    
    def __init__(self, output_dir=None):
        """
        Initialize the pipeline tester.
        
        Args:
            output_dir: Directory to store output files (default: tests/pipeline_results)
        """
        self.output_dir = output_dir or os.path.join(SCRIPT_DIR, "pipeline_results")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize the processors
        self.contextual_analyzer = LLMContextualAnalyzer()
        self.osm_processor = OSMSearchProcessor()
        
        logger.info(f"Pipeline tester initialized. Output directory: {self.output_dir}")
    
    def check_image_file(self, image_path):
        """
        Check if the image file is valid and of a supported format.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not os.path.exists(image_path):
            return False, f"Image file not found: {image_path}"
            
        # Check file size
        file_size = os.path.getsize(image_path)
        file_size_mb = file_size / (1024 * 1024)
        
        if file_size_mb > 20:
            return False, f"Image file is too large: {file_size_mb:.2f} MB (max recommended is 20 MB)"
        
        # Check file extension
        ext = os.path.splitext(image_path)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png']:
            return False, f"Image file has unsupported extension: {ext} (supported: .jpg, .jpeg, .png)"
        
        return True, f"Image file is valid: {file_size_mb:.2f} MB"
    
    def analyze_image(self, image_path, output_id=None):
        """
        Use the contextual analyzer to generate an Overpass QL query from an image.
        
        Args:
            image_path: Path to the drone image
            output_id: Optional identifier for output files
            
        Returns:
            Generated Overpass QL query or None if failed
        """
        try:
            # Check the image file
            is_valid, msg = self.check_image_file(image_path)
            if not is_valid:
                logger.error(msg)
                return None
            
            logger.info(f"Analyzing image: {image_path}")
            
            # Generate the query using direct Overpass mode
            result = self.contextual_analyzer.process_image(
                image_path,
                image_id=output_id,
                direct_overpass=True
            )
            
            if result and "overpass_query" in result:
                query = result["overpass_query"]
                logger.info(f"Generated Overpass QL query ({len(query)} chars)")
                return query
            else:
                logger.error("Failed to generate Overpass QL query")
                return None
                
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return None
    
    def process_search_area(self, search_area_path, query, output_id=None, feature_index=0):
        """
        Process a search area and execute the Overpass QL query.
        
        Args:
            search_area_path: Path to the search area GeoJSON file
            query: Overpass QL query string
            output_id: Optional identifier for output files
            feature_index: Index of the feature to use (for GeoJSON FeatureCollection)
            
        Returns:
            Tuple of (final_query, overpy_result, geojson_data) or (None, None, None) if failed
        """
        try:
            logger.info(f"Processing search area: {search_area_path}")
            
            # Process the query using the OSMSearchProcessor
            final_query, result, geojson_data = self.osm_processor.process_query(
                query=query,
                search_area_file=search_area_path,
                feature_index=feature_index
            )
            
            if not final_query or not result or not geojson_data:
                logger.error("Failed to process query")
                return None, None, None
            
            # Save the results if output_id is provided
            if output_id:
                query_path = os.path.join(self.output_dir, f"final_query_{output_id}.txt")
                geojson_path = os.path.join(self.output_dir, f"query_result_{output_id}.geojson")
                
                self.osm_processor.save_query_to_file(final_query, query_path)
                self.osm_processor.save_geojson_to_file(geojson_data, geojson_path)
            
            return final_query, result, geojson_data
            
        except Exception as e:
            logger.error(f"Error processing search area: {e}")
            return None, None, None
    
    def process_location(self, base_name, feature_index=0):
        """
        Process a single location through the complete pipeline.
        
        Args:
            base_name: Base name of the location (e.g., "Reading_1")
            feature_index: Index of the feature to use from GeoJSON FeatureCollection
            
        Returns:
            True if successful, False otherwise
        """
        # Get the location info
        if base_name not in LOCATIONS:
            logger.error(f"Location not found: {base_name}")
            return False
        
        location_info = LOCATIONS[base_name]
        image_path = location_info["image"]
        search_area_path = location_info["search_area"]
        
        # Check if files exist
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return False
        if not os.path.exists(search_area_path):
            logger.error(f"Search area file not found: {search_area_path}")
            return False
        
        print(f"\n=== Processing {base_name} ===")
        print(f"Image: {image_path}")
        print(f"Search Area: {search_area_path}")
        print(f"Feature Index: {feature_index}")
        
        # Step 1: Generate query from image
        query = self.analyze_image(image_path, base_name)
        if not query:
            print(f"\n❌ Failed to generate query from image for {base_name}")
            return False
        
        print(f"\n✓ Generated Overpass QL query ({len(query)} chars)")
        
        # Step 2: Process search area and execute query
        final_query, result, geojson_data = self.process_search_area(
            search_area_path,
            query,
            base_name,
            feature_index
        )
        
        if not final_query or not result or not geojson_data:
            print(f"\n❌ Failed to process search area for {base_name}")
            return False
        
        # Print results summary
        feature_count = len(geojson_data["features"])
        print(f"\n✓ Query executed successfully!")
        print(f"Found {len(result.nodes)} nodes, {len(result.ways)} ways, and {len(result.relations)} relations")
        print(f"Generated GeoJSON with {feature_count} features")
        
        # Save results
        query_path = os.path.join(self.output_dir, f"final_query_{base_name}.txt")
        geojson_path = os.path.join(self.output_dir, f"query_result_{base_name}.geojson")
        
        print(f"\nResults saved to:")
        print(f"  Query: {query_path}")
        print(f"  GeoJSON: {geojson_path}")
        
        return True

def main():
    """Run the complete pipeline test."""
    parser = argparse.ArgumentParser(description="Test the complete OSM pipeline")
    parser.add_argument("--location", help="Base name of the location to process (e.g., 'Reading_1')")
    parser.add_argument("--all", action="store_true", help="Process all locations in the Competition Release folder")
    parser.add_argument("--feature-index", type=int, default=0, 
                        help="Index of the feature to use from GeoJSON FeatureCollection (default: 0)")
    parser.add_argument("--output-dir", help="Directory to store output files")
    parser.add_argument("--list-locations", action="store_true", help="List all available locations")
    args = parser.parse_args()
    
    # Create the pipeline tester
    tester = OSMPipelineTester(args.output_dir)
    
    print("\n=== Testing OSM Pipeline ===\n")
    
    # Just list available locations
    if args.list_locations:
        print("Available locations:")
        for location in sorted(LOCATIONS.keys()):
            print(f"  - {location}")
        return True
    
    # Process all locations
    if args.all:
        base_names = sorted(LOCATIONS.keys())
        print(f"Found {len(base_names)} locations: {', '.join(base_names)}")
        
        success_count = 0
        for base_name in base_names:
            if tester.process_location(base_name, args.feature_index):
                success_count += 1
        
        print(f"\n=== Completed processing {success_count}/{len(base_names)} locations ===\n")
        return success_count == len(base_names)
    
    # Process a specific location
    elif args.location:
        return tester.process_location(args.location, args.feature_index)
    
    # Default case - show usage
    else:
        print("Please specify either:")
        print("  --location NAME      Process a specific location (e.g., --location Reading_1)")
        print("  --all                Process all locations")
        print("  --feature-index N    Use the Nth feature from the GeoJSON FeatureCollection (default: 0)")
        print("  --output-dir DIR     Specify output directory for results")
        print("  --list-locations     List all available locations")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 