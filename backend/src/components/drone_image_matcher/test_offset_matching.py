#!/usr/bin/env python3
# Purpose: Test the drone image matcher with offset coordinates to evaluate robustness
# This tests how well the system can match a drone image when it's taken from a slightly
# different position than any of the satellite image coordinates.

import sys
import os
import pathlib
import json
import argparse
import requests
import time
from drone_image_matcher import DroneImageMatcher, extract_contours

def download_satellite_images(coordinates, output_dir):
    """
    Download satellite images for all coordinates.
    
    Args:
        coordinates (list): List of coordinate dictionaries
        output_dir (str): Directory to save images
        
    Returns:
        list: List of paths to downloaded images
    """
    # Make sure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Import static_map_url from the same way DroneImageMatcher does
    script_dir = pathlib.Path(__file__).parent
    parent_dir = script_dir.parent
    sys.path.append(str(parent_dir / "get-map-image"))
    from get_map_image import static_map_url
    
    print(f"Downloading {len(coordinates)} satellite images to {output_dir}...")
    
    image_paths = []
    for i, coord in enumerate(coordinates):
        lat, lon = coord['lat'], coord['lon']
        url = static_map_url(lat, lon)
        
        img_path = os.path.join(output_dir, f"satellite_{i+1}.png")
        # Skip if file already exists
        if os.path.exists(img_path):
            print(f"Image {i+1}/{len(coordinates)} already exists, skipping")
            image_paths.append(img_path)
            continue
            
        response = requests.get(url)
        response.raise_for_status()
        
        with open(img_path, "wb") as f:
            f.write(response.content)
        
        image_paths.append(img_path)
        print(f"Downloaded image {i+1}/{len(coordinates)} for {coord.get('description', '')}")
        # Avoid rate limiting
        time.sleep(0.5)
            
    return image_paths

def test_offset_matching():
    """
    Test how well the matching works with offset coordinates.
    Compare both contour-based and holistic matching approaches.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test drone image matching with offset coordinates.')
    parser.add_argument('--coordinate-file', default='offset_coordinates.json', 
                      help='JSON file with offset coordinates')
    parser.add_argument('--test-image-dir', default='test_data', 
                      help='Directory to store downloaded test images')
    parser.add_argument('--use-contour', action='store_true',
                      help='Use contour matching instead of holistic matching')
    parser.add_argument('--compare-methods', action='store_true',
                      help='Run tests with both matching methods')
    parser.add_argument('--simplify', action='store_true',
                      help='Disable scale and rotation transformations in holistic matching')
    
    args = parser.parse_args()
    
    # Load coordinates
    with open(args.coordinate_file, 'r') as f:
        coordinates = json.load(f)
    
    # Download satellite images if not already downloaded
    test_dir = args.test_image_dir
    image_paths = download_satellite_images(coordinates, test_dir)
    
    # Function to test a specific reference image with both matching methods
    def test_reference_image(ref_image_index, use_holistic, simplify=False):
        ref_img_path = image_paths[ref_image_index]
        ref_coord = coordinates[ref_image_index]
        
        method = "Holistic" if use_holistic else "Contour-based"
        simplify_str = " with simplify mode" if use_holistic and simplify else ""
        print("\n" + "=" * 70)
        print(f"TESTING WITH REFERENCE IMAGE {ref_image_index}: {ref_coord.get('description', '')}")
        print(f"USING {method.upper()} MATCHING{simplify_str}")
        print("=" * 70)
        
        # Create matcher
        matcher = DroneImageMatcher(
            output_dir=os.path.join(test_dir, "match_output"), 
            use_holistic=use_holistic,
            simplify=simplify
        )
        
        # Use the reference image as the "drone image"
        result = matcher.find_best_match(ref_img_path, coordinates)
        
        # Print results
        print("\nMatching Results:")
        print(f"Reference image: {ref_coord.get('description', '')}")
        print(f"Best Match: {result['best_match']['coordinates']}")
        print(f"Score: {result['best_match']['score']:.2f}")
        
        # Print all matches
        print("\nAll Matches (sorted by score):")
        for i, match in enumerate(result['all_matches']):
            desc = next((c.get('description', '') for c in coordinates if 
                        c['lat'] == match['coordinates']['lat'] and 
                        c['lon'] == match['coordinates']['lon']), '')
            print(f"{i+1}. {desc}")
            print(f"   Coordinates: {match['coordinates']}")
            print(f"   Score: {match['score']:.2f}")
        
        # Check if best match is the reference coordinate
        expected_lat = ref_coord['lat']
        expected_lon = ref_coord['lon']
        actual_lat = result['best_match']['coordinates']['lat']
        actual_lon = result['best_match']['coordinates']['lon']
        
        is_match = (expected_lat == actual_lat and expected_lon == actual_lon)
        
        print("\nTest Result:")
        if is_match:
            print("✅ SUCCESS: Best match is the reference coordinate")
        else:
            # Find the rank of the reference coordinate
            rank = next((i+1 for i, match in enumerate(result['all_matches']) if
                       match['coordinates']['lat'] == expected_lat and
                       match['coordinates']['lon'] == expected_lon), None)
            
            if rank:
                print(f"📊 INTERESTING: Reference coordinate ranked #{rank}")
            else:
                print("❌ FAILURE: Reference coordinate not in matches")
                
        return result
    
    # Test both the original and offset images
    test_indices = [0, 1, 2, 5, 8]  # Original, 10m East, 10m North, 50m SE, 100m SE
    
    # Run tests with the selected method(s)
    if args.compare_methods:
        # Test each reference with both methods
        for idx in test_indices:
            # First with holistic matching (full transformations)
            holistic_result = test_reference_image(idx, True, False)
            
            # Then with holistic matching with simplify enabled (if requested)
            if args.simplify:
                holistic_simplify_result = test_reference_image(idx, True, True)
            
            # Then with contour-based matching
            contour_result = test_reference_image(idx, False)
            
            # Compare results
            h_score = holistic_result['best_match']['score']
            c_score = contour_result['best_match']['score']
            
            print("\n" + "-" * 70)
            print(f"COMPARISON FOR IMAGE {idx}: {coordinates[idx].get('description', '')}")
            print(f"Holistic matching best score: {h_score:.2f}")
            if args.simplify:
                h_simplify_score = holistic_simplify_result['best_match']['score']
                print(f"Holistic matching (simplified) best score: {h_simplify_score:.2f}")
            print(f"Contour-based matching best score: {c_score:.2f}")
            
            print(f"Difference (holistic vs contour): {h_score - c_score:.2f}")
            if args.simplify:
                print(f"Difference (simplified vs full holistic): {h_simplify_score - h_score:.2f}")
                
            if h_score > c_score:
                print("Holistic matching performed better than contour-based")
            elif c_score > h_score:
                print("Contour-based matching performed better than holistic")
            else:
                print("Both methods performed the same")
                
            if args.simplify and h_simplify_score > h_score:
                print("Simplified holistic matching performed better than full holistic matching")
            elif args.simplify and h_score > h_simplify_score:
                print("Full holistic matching performed better than simplified")
    else:
        # Run with the selected method only
        use_holistic = not args.use_contour
        simplify = args.simplify
        for idx in test_indices:
            test_reference_image(idx, use_holistic, simplify)
    
    return 0

if __name__ == "__main__":
    sys.exit(test_offset_matching()) 