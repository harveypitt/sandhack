#!/usr/bin/env python3
# Purpose: Example demonstrating the simplified holistic matching functionality
# with a sample drone image and predefined coordinates.
#
# NOTE: This example requires a drone image to be provided via the --drone-image parameter
# as there are no sample images included in this repository. You can use any aerial image,
# ideally taken from directly above (nadir view).
#
# Example usage:
# python examples/simplified_matching_example.py --drone-image path/to/your/drone_image.jpg

import os
import sys
import json
import argparse
from pathlib import Path

# Add parent directory to path to make imports work
script_dir = Path(__file__).parent.absolute()
parent_dir = script_dir.parent
sys.path.append(str(parent_dir))

# Import the DroneImageMatcher directly 
from backend.src.components.drone-image-matcher.drone_image_matcher import DroneImageMatcher

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Example of simplified holistic matching with a drone image.'
    )
    parser.add_argument('--drone-image', '-d', required=True,
                      help='Path to the drone image (required)')
    parser.add_argument('--output', '-o', default='example_output',
                      help='Directory to save satellite images')
    return parser.parse_args()

def main():
    """Run the simplified holistic matching example."""
    args = parse_args()
    
    # Create sample coordinates.json if not already present
    sample_coordinates_path = script_dir / 'sample_coordinates.json'
    if not sample_coordinates_path.exists():
        print("Creating sample coordinates file...")
        # Sample coordinates for famous landmarks 
        # (Note: For an actual drone image, you'd want coordinates close to where it was taken)
        sample_coordinates = [
            {"lat": 48.8584, "lon": 2.2945, "description": "Eiffel Tower, Paris"},
            {"lat": 40.6892, "lon": -74.0445, "description": "Statue of Liberty, New York"},
            {"lat": 29.9792, "lon": 31.1342, "description": "Great Pyramids, Giza"},
            {"lat": 27.1751, "lon": 78.0421, "description": "Taj Mahal, India"},
            {"lat": 38.8977, "lon": -77.0365, "description": "White House, Washington DC"}
        ]
        with open(sample_coordinates_path, 'w') as f:
            json.dump(sample_coordinates, f, indent=2)
        print(f"Sample coordinates file created at {sample_coordinates_path}")
        print("NOTE: These coordinates are for demonstration only. For actual matching,")
        print("provide coordinates near where your drone image was captured.")

    # Use the provided drone image
    drone_image_path = args.drone_image
    if not os.path.exists(drone_image_path):
        print(f"Error: The specified drone image does not exist: {drone_image_path}")
        print("Please provide a valid path to a drone image.")
        return 1
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    print(f"Using drone image: {drone_image_path}")
    print(f"Using coordinates from: {sample_coordinates_path}")
    print(f"Saving output to: {output_dir}")
    
    # Load coordinates
    with open(sample_coordinates_path, 'r') as f:
        coordinates = json.load(f)
    
    print(f"\nRunning matching with {len(coordinates)} potential locations...")
    print("Using simplified holistic matching (translations only, no rotation/scale)...")
    
    # Create the matcher with simplified holistic matching
    matcher = DroneImageMatcher(
        output_dir=str(output_dir),
        use_holistic=True,  # Use holistic matching
        simplify=True       # Use simplified approach (translations only)
    )
    
    # Start timing
    import time
    start_time = time.time()
    
    # Find the best match for the drone image
    result = matcher.find_best_match(drone_image_path, coordinates)
    
    # End timing
    end_time = time.time()
    elapsed = end_time - start_time
    
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
    
    print(f"\nTotal processing time: {elapsed:.2f} seconds")
    
    # Compare with full holistic matching if requested
    should_compare = input("\nWould you like to compare with full holistic matching? (y/n): ")
    if should_compare.lower() == 'y':
        print("\nRunning with full holistic matching (testing rotations and scales)...")
        
        # Create a new matcher with full holistic matching
        full_matcher = DroneImageMatcher(
            output_dir=str(output_dir / "full_holistic"),
            use_holistic=True,
            simplify=False  # Use full holistic matching
        )
        
        # Start timing
        start_time = time.time()
        
        # Find the best match
        full_result = full_matcher.find_best_match(drone_image_path, coordinates)
        
        # End timing
        end_time = time.time()
        full_elapsed = end_time - start_time
        
        # Print comparison
        print("\nComparison Results:")
        print(f"Simplified holistic matching time: {elapsed:.2f} seconds")
        print(f"Full holistic matching time: {full_elapsed:.2f} seconds")
        print(f"Speed improvement: {full_elapsed/elapsed:.1f}x faster")
        
        print("\nSimplified best match:", result['best_match']['coordinates'])
        print("Full holistic best match:", full_result['best_match']['coordinates'])
        
        if result['best_match']['coordinates'] == full_result['best_match']['coordinates']:
            print("\nBoth methods found the same best match! ✓")
        else:
            print("\nThe methods found different best matches.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 