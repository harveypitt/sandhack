#!/usr/bin/env python3
# Purpose: Match drone images with satellite images by extracting features and finding the best match.
# This script orchestrates the process of downloading satellite images for given coordinates,
# extracting features from both satellite and drone images, and finding the best match.

import argparse
import json
import os
import sys
import pathlib
import cv2
import numpy as np
import importlib.util
from typing import List, Dict, Tuple, Any, Optional

# Add parent directory to path so we can import from sibling components
script_dir = pathlib.Path(__file__).parent
parent_dir = script_dir.parent

# Import components from directories with hyphens using importlib
def import_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import get_map_image module - fix path to ensure it exists
get_map_image_path = parent_dir / "get-map-image" / "get_map_image.py"
if not get_map_image_path.exists():
    # Try alternate path formats or search for it
    alternate_paths = [
        parent_dir / "get_map_image" / "get_map_image.py",  # Underscore version
        parent_dir / "get-map-image" / "get-map-image.py",  # Full hyphen version
    ]
    for alt_path in alternate_paths:
        if alt_path.exists():
            get_map_image_path = alt_path
            break
    else:
        # If still not found, raise informative error
        raise ImportError(f"Could not find get_map_image module. Tried paths: {get_map_image_path} and {alternate_paths}")

print(f"Using get_map_image module from path: {get_map_image_path}")
get_map_image_module = import_from_path("get_map_image", get_map_image_path)
static_map_url = get_map_image_module.static_map_url

# Import ContourExtractor from contour_extractor module
from src.components.contour_extractor.contour_extractor import ContourExtractor

# Import ContourMatcher and HolisticMatcher from contour_matcher module
from src.components.contour_matcher.contour_matcher import ContourMatcher, HolisticMatcher

# Create instances of needed classes
contour_extractor = ContourExtractor()
contour_matcher = ContourMatcher()
holistic_matcher = HolisticMatcher()

# Define a function to extract contours using the ContourExtractor instance
def extract_contours(image):
    return contour_extractor.extract_contours(image)

class DroneImageMatcher:
    """
    Class to match drone images with satellite images by comparing features.
    """
    
    def __init__(self, output_dir: str = None, api_key: str = None, use_holistic: bool = True, simplify: bool = False):
        """
        Initialize the drone image matcher.
        
        Args:
            output_dir (str): Directory to store satellite images
            api_key (str): Google Maps API key (will use from get_map_image if not provided)
            use_holistic (bool): Whether to use holistic matching (True) or contour matching (False)
            simplify (bool): If True, disable scale and rotation transformations in holistic matching
                           This makes matching simpler but less robust to differently oriented images
        """
        self.output_dir = output_dir or str(script_dir / "satellite_images")
        os.makedirs(self.output_dir, exist_ok=True)
        self.api_key = api_key
        self.use_holistic = use_holistic
        self.simplify = simplify
        print(f"Using {'holistic' if use_holistic else 'contour-based'} matching approach")
        if use_holistic and simplify:
            print("Simplify mode enabled: Scale and rotation transformations are disabled")
        
    def download_satellite_images(self, coordinates: List[Dict[str, float]]) -> List[str]:
        """
        Download satellite images for a list of coordinates.
        
        Args:
            coordinates (List[Dict]): List of coordinate dictionaries with 'lat' and 'lon' keys
            
        Returns:
            List[str]: List of paths to downloaded satellite images
        """
        import requests
        
        image_paths = []
        for i, coord in enumerate(coordinates):
            lat, lon = coord['lat'], coord['lon']
            url = static_map_url(lat, lon)
            
            img_path = os.path.join(self.output_dir, f"satellite_{i+1}.png")
            response = requests.get(url)
            response.raise_for_status()
            
            with open(img_path, "wb") as f:
                f.write(response.content)
            
            image_paths.append(img_path)
            print(f"Downloaded satellite image {i+1}/{len(coordinates)}")
            
        return image_paths
    
    def extract_features(self, image_path: str) -> Dict:
        """
        Extract features from an image using the contour extractor.
        
        Args:
            image_path (str): Path to the image
            
        Returns:
            Dict: Extracted features
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image at {image_path}")
        
        # Extract contours using the contour extractor component
        contours = extract_contours(image)
        
        return {
            'path': image_path,
            'contours': contours
        }
    
    def match_features(self, drone_features: Dict, satellite_features: List[Dict]) -> List[Tuple[int, float]]:
        """
        Match features between a drone image and multiple satellite images.
        
        Args:
            drone_features (Dict): Features extracted from the drone image. 
                                   Expected to be the output of self.extract_features.
            satellite_features (List[Dict]): List of features extracted from satellite images.
                                            Each element is an output of self.extract_features.
            
        Returns:
            List[Tuple[int, float]]: List of (index, score) tuples sorted by score (best match first)
        """
        # Get the contours from the features
        actual_drone_contours = drone_features.get('contours')
        if actual_drone_contours is None or not isinstance(actual_drone_contours, dict) or 'contours' not in actual_drone_contours:
            print(f"Warning: Drone features do not contain a valid 'contours' list. Drone features: {drone_features}")
            return [(i, 0.0) for i in range(len(satellite_features))]  # Return zero scores for all
        
        # Prepare satellite contours list
        satellite_contours_list = []
        for sat_feat_dict in satellite_features:
            actual_satellite_contours = sat_feat_dict.get('contours')
            if actual_satellite_contours is None or not isinstance(actual_satellite_contours, dict) or 'contours' not in actual_satellite_contours:
                print(f"Warning: Satellite features do not contain a valid 'contours' list.")
                satellite_contours_list.append([])  # Empty contours
            else:
                satellite_contours_list.append(actual_satellite_contours['contours'])
        
        if self.use_holistic:
            # Use holistic matching
            print("Using holistic matching for feature comparison")
            try:
                # Call the holistic matcher with the extracted contours
                return holistic_matcher.match_contours(
                    actual_drone_contours['contours'], 
                    satellite_contours_list,
                    simplify=self.simplify  # Pass the simplify flag to the holistic matcher
                )
            except Exception as e:
                print(f"Error during holistic matching: {str(e)}")
                print("Falling back to contour-based matching")
                self.use_holistic = False  # Fall back to contour matcher
        
        # Use contour-based matching
        if not self.use_holistic:
            print("Using contour-based matching for feature comparison")
            match_scores = []
            for i, sat_contours in enumerate(satellite_contours_list):
                try:
                    score = contour_matcher._compute_contour_similarity(
                        actual_drone_contours['contours'], 
                        sat_contours
                    )
                    match_scores.append((i, score))
                except Exception as e:
                    print(f"Error during contour similarity computation for satellite image {i}: {str(e)}")
                    match_scores.append((i, 0.0))
            
            # Sort by score (higher is better)
            match_scores.sort(key=lambda x: x[1], reverse=True)
            return match_scores
    
    def find_best_match(self, drone_image_path: str, coordinates: List[Dict[str, float]]) -> Dict:
        """
        Find the best matching satellite image for a drone image.
        
        Args:
            drone_image_path (str): Path to the drone image
            coordinates (List[Dict]): List of coordinate dictionaries with 'lat' and 'lon' keys
            
        Returns:
            Dict: Best match result with coordinates, score, and paths
        """
        # Download satellite images for all coordinates
        satellite_image_paths = self.download_satellite_images(coordinates)
        
        # Extract features from the drone image
        print("Extracting features from drone image...")
        drone_features = self.extract_features(drone_image_path)
        
        # Extract features from all satellite images
        print("Extracting features from satellite images...")
        satellite_features = []
        for path in satellite_image_paths:
            features = self.extract_features(path)
            satellite_features.append(features)
        
        # Match features
        print("Matching features...")
        match_scores = self.match_features(drone_features, satellite_features)
        
        # Prepare results
        results = []
        for idx, score in match_scores:
            results.append({
                'coordinates': coordinates[idx],
                'satellite_image': satellite_image_paths[idx],
                'score': score
            })
        
        return {
            'drone_image': drone_image_path,
            'best_match': results[0],
            'all_matches': results
        }

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Match drone images with satellite images.')
    parser.add_argument('--drone-image', '-d', required=True, help='Path to the drone image')
    parser.add_argument('--coordinates', '-c', required=True, help='Path to JSON file with coordinates')
    parser.add_argument('--output', '-o', help='Directory to save satellite images')
    parser.add_argument('--api-key', '-k', help='Google Maps API key')
    parser.add_argument('--use-contour', action='store_true', help='Use contour matching instead of holistic matching')
    parser.add_argument('--simplify', action='store_true', help='Disable scale and rotation transformations in holistic matching')
    return parser.parse_args()

def main():
    """Main function to run the drone image matcher."""
    args = parse_args()
    
    # Load coordinates from JSON file
    with open(args.coordinates, 'r') as f:
        coordinates = json.load(f)
    
    # Create the matcher
    matcher = DroneImageMatcher(
        output_dir=args.output, 
        api_key=args.api_key,
        use_holistic=not args.use_contour,  # Use holistic matching by default
        simplify=args.simplify  # Pass the simplify flag
    )
    
    # Find the best match
    result = matcher.find_best_match(args.drone_image, coordinates)
    
    # Print results
    print("\nMatching Results:")
    print(f"Drone Image: {result['drone_image']}")
    print(f"Best Match: {result['best_match']['coordinates']}")
    print(f"Score: {result['best_match']['score']}")
    print(f"Satellite Image: {result['best_match']['satellite_image']}")
    
    # Print all matches
    print("\nAll Matches (sorted by score):")
    for i, match in enumerate(result['all_matches']):
        print(f"{i+1}. Coordinates: {match['coordinates']}, Score: {match['score']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 