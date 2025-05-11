#!/usr/bin/env python3
# Purpose: Test the drone image matcher using satellite images as simulated drone images.
# This provides a controlled test where we know the expected match result.

import sys
import os
import pathlib
import json
import argparse

# Import the DroneImageMatcher class directly from the file
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from drone_image_matcher import DroneImageMatcher

def run_controlled_test(image_dir, coordinates_file, test_image_index=0, use_holistic=True, simplify=False):
    """
    Run a controlled test using a satellite image as a simulated drone image.
    
    Args:
        image_dir (str): Directory containing satellite images
        coordinates_file (str): Path to JSON file with coordinates
        test_image_index (int): Index of the image to use as the "drone image"
        use_holistic (bool): Whether to use holistic matching (True) or contour matching (False)
        simplify (bool): If True, disable scale and rotation transformations in holistic matching
        
    Returns:
        bool: True if the test passed (best match is the expected coordinate)
    """
    # Load coordinates
    with open(coordinates_file, 'r') as f:
        coordinates = json.load(f)
    
    # Get list of images in the directory
    images = sorted([f for f in os.listdir(image_dir) if f.endswith('.png')])
    
    if not images:
        print(f"No images found in {image_dir}")
        return False
    
    # Select the test image (will be treated as our "drone image")
    test_image_path = os.path.join(image_dir, images[test_image_index])
    expected_coord = coordinates[test_image_index]
    
    print(f"Using {os.path.basename(test_image_path)} as simulated drone image")
    print(f"Expected best match: {expected_coord}")
    print(f"Matching method: {'Holistic' if use_holistic else 'Contour-based'}")
    if use_holistic and simplify:
        print("Simplify mode enabled: Scale and rotation transformations are disabled")
    
    # Create matcher and run the test
    test_output_dir = os.path.join("test_output")
    matcher = DroneImageMatcher(output_dir=test_output_dir, use_holistic=use_holistic, simplify=simplify)
    
    # Find the best match
    results = matcher.find_best_match(test_image_path, coordinates)
    
    # Check results
    best_match = results['best_match']
    
    print("\nMatching Results:")
    print(f"Best Match: {best_match['coordinates']}")
    print(f"Score: {best_match['score']}")
    
    # Print all matches
    print("\nAll Matches (sorted by score):")
    for i, match in enumerate(results['all_matches']):
        print(f"{i+1}. Coordinates: {match['coordinates']}, Score: {match['score']}")
    
    # Check if best match is the expected coordinate
    expected_lat = expected_coord['lat']
    expected_lon = expected_coord['lon']
    actual_lat = best_match['coordinates']['lat']
    actual_lon = best_match['coordinates']['lon']
    
    is_match = (expected_lat == actual_lat and expected_lon == actual_lon)
    
    print("\nTest Result:")
    if is_match:
        print("✅ SUCCESS: Best match is the expected coordinate")
    else:
        print("❌ FAILURE: Best match is not the expected coordinate")
        print(f"Expected: lat={expected_lat}, lon={expected_lon}")
        print(f"Actual: lat={actual_lat}, lon={actual_lon}")
    
    return is_match

def main():
    """Run tests with different image indices and matching methods."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test drone image matcher with satellite images.')
    parser.add_argument('--use-contour', action='store_true', help='Use contour matching instead of holistic matching')
    parser.add_argument('--compare-methods', action='store_true', help='Run tests with both matching methods')
    parser.add_argument('--simplify', action='store_true', help='Disable scale and rotation transformations in holistic matching')
    args = parser.parse_args()
    
    # Default to holistic matching
    use_holistic = not args.use_contour
    simplify = args.simplify
    
    # Function to run all tests with a specific matching method
    def run_all_tests(use_holistic_method, simplify_mode=False):
        method_name = "Holistic" if use_holistic_method else "Contour-based"
        simplify_str = " with simplify mode" if use_holistic_method and simplify_mode else ""
        print("\n" + "=" * 80)
        print(f"RUNNING ALL TESTS WITH {method_name.upper()} MATCHING{simplify_str}")
        print("=" * 80)
        
        # Test with Rickmansworth images
        print("=" * 60)
        print(f"TEST 1: Rickmansworth Park - Original reference point ({method_name}{simplify_str})")
        print("=" * 60)
        run_controlled_test("rickmansworth_images", "nearby_coordinates.json", 0, use_holistic_method, simplify_mode)
        
        # Test with a different Rickmansworth image
        print("\n" + "=" * 60)
        print(f"TEST 2: Rickmansworth Park - North side ({method_name}{simplify_str})")
        print("=" * 60)
        run_controlled_test("rickmansworth_images", "nearby_coordinates.json", 7, use_holistic_method, simplify_mode)
        
        # Test with Reading University images
        print("\n" + "=" * 60)
        print(f"TEST 3: Reading University - Original reference point ({method_name}{simplify_str})")
        print("=" * 60)
        run_controlled_test("reading_university_images", "reading_university_coordinates.json", 0, use_holistic_method, simplify_mode)
    
    # Run tests with the selected method(s)
    if args.compare_methods:
        # Run with holistic matching first (without simplify)
        run_all_tests(True, False)
        
        # Then with holistic matching with simplify enabled (if requested)
        if simplify:
            run_all_tests(True, True)
            
        # Then with contour-based matching
        run_all_tests(False, False)
    else:
        # Run with the selected method only
        run_all_tests(use_holistic, simplify)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 