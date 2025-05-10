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
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))  # Two levels up from components
DEFAULT_IMAGE_PATH = os.path.join(
    PROJECT_ROOT, 
    "data", "example", "images", "rickmansworth_example.jpg"
)
DEFAULT_SEARCH_AREA_PATH = os.path.join(
    PROJECT_ROOT, 
    "data", "example", "images", "rickmansworth_example_search_area.json"
)
ANALYZER_SCRIPT = os.path.join(SCRIPT_DIR, "llm_analysis", "contextual_analyzer.py")
OSM_SEARCH_SCRIPT = os.path.join(SCRIPT_DIR, "osm_search", "osm_search.py")
FINAL_QUERY_PATH = os.path.join(SCRIPT_DIR, "osm_search", "final_query.txt")

def run_contextual_analyzer(image_path):
    """
    Run the contextual analyzer to generate an Overpass QL query with placeholder.
    
    Args:
        image_path: Path to the drone image
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Running contextual analyzer with image: {image_path}")
        
        # Ensure the output directory exists
        os.makedirs(os.path.join(SCRIPT_DIR, "osm_search"), exist_ok=True)
        
        # Run the analyzer with direct-overpass option
        result = subprocess.run(
            [
                sys.executable, 
                ANALYZER_SCRIPT, 
                image_path, 
                "--direct-overpass"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Check if the output contains the expected JSON
        try:
            output_data = json.loads(result.stdout)
            if "overpass_query" in output_data:
                logger.info("Contextual analyzer ran successfully!")
                return True
            else:
                logger.error("Contextual analyzer output doesn't contain overpass_query field")
                return False
        except json.JSONDecodeError:
            logger.error(f"Failed to parse contextual analyzer output: {result.stdout}")
            return False
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Contextual analyzer failed: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error running contextual analyzer: {e}")
        return False

def run_osm_search():
    """
    Run the OSM search script to process the search area and substitute the polygon string.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Running OSM search to process polygon and substitute into query")
        
        # Run the OSM search script
        result = subprocess.run(
            [sys.executable, OSM_SEARCH_SCRIPT],
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info("OSM search ran successfully!")
        return True
            
    except subprocess.CalledProcessError as e:
        logger.error(f"OSM search failed: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error running OSM search: {e}")
        return False

def check_final_query():
    """
    Check if the final query was generated and display it.
    
    Returns:
        True if final query exists, False otherwise
    """
    if os.path.exists(FINAL_QUERY_PATH):
        try:
            with open(FINAL_QUERY_PATH, 'r') as f:
                query = f.read()
            
            logger.info(f"Final query generated successfully! ({len(query)} chars)")
            print("\n--- Final Overpass QL Query ---")
            print(f"{query[:500]}...")
            print(f"\nFull query saved to: {FINAL_QUERY_PATH}")
            print("\nYou can execute this query at: https://overpass-turbo.eu/")
            return True
        except Exception as e:
            logger.error(f"Error reading final query: {e}")
            return False
    else:
        logger.error(f"Final query file not found at {FINAL_QUERY_PATH}")
        return False

def main():
    """Run the complete pipeline."""
    parser = argparse.ArgumentParser(description="Test the complete OSM pipeline")
    parser.add_argument("--image", default=DEFAULT_IMAGE_PATH, 
                        help=f"Path to the drone image (default: {DEFAULT_IMAGE_PATH})")
    args = parser.parse_args()
    
    print("\n=== Testing OSM Pipeline ===\n")
    
    # Step 1: Run contextual analyzer
    if not run_contextual_analyzer(args.image):
        print("\n❌ Pipeline test failed at contextual analyzer step")
        return False
    
    # Step 2: Run OSM search
    if not run_osm_search():
        print("\n❌ Pipeline test failed at OSM search step")
        return False
    
    # Step 3: Check final query
    if not check_final_query():
        print("\n❌ Pipeline test failed at final query check")
        return False
    
    print("\n✅ Pipeline test completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 