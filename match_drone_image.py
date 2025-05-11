#!/usr/bin/env python3
# Purpose: Simple script to match a drone image with satellite images using simplified holistic matching

import os
import sys
import argparse
import json

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Match a drone image with satellite images using simplified holistic matching.'
    )
    parser.add_argument('--drone-image', '-d', required=True, 
                      help='Path to the drone image')
    parser.add_argument('--coordinates', '-c', required=True, 
                      help='Path to JSON file with coordinates')
    parser.add_argument('--output', '-o', default='satellite_images',
                      help='Directory to save satellite images')
    parser.add_argument('--full', action='store_true',
                      help='Use full holistic matching (slower but more robust to rotation)')
    parser.add_argument('--contour', action='store_true',
                      help='Use contour-based matching (faster but less accurate)')
    return parser.parse_args()

def main():
    """Run the drone image matcher with the specified options."""
    args = parse_args()
    
    # Validate paths
    if not os.path.exists(args.drone_image):
        print(f"Error: Drone image not found at {args.drone_image}")
        return 1
    
    if not os.path.exists(args.coordinates):
        print(f"Error: Coordinates file not found at {args.coordinates}")
        return 1
    
    # Build the command to run the matcher
    script_dir = os.path.dirname(os.path.abspath(__file__))
    matcher_path = os.path.join(
        script_dir, 
        "backend", 
        "src", 
        "components", 
        "drone-image-matcher", 
        "drone_image_matcher.py"
    )
    
    # Validate that matcher exists
    if not os.path.exists(matcher_path):
        print(f"Error: Matcher script not found at {matcher_path}")
        return 1
    
    # Add the src directory to PYTHONPATH
    src_dir = os.path.join(script_dir, "backend", "src")
    os.environ["PYTHONPATH"] = f"{os.environ.get('PYTHONPATH', '')}:{src_dir}"
    
    # Add the appropriate flags based on the user's choices
    flags = []
    if args.contour:
        flags.append("--use-contour")
    elif not args.full:
        # Use simplified holistic matching by default
        flags.append("--simplify")
    
    # Load coordinates file to display info
    try:
        with open(args.coordinates, 'r') as f:
            coordinates = json.load(f)
        print(f"Loaded {len(coordinates)} potential coordinates from {args.coordinates}")
    except json.JSONDecodeError:
        print(f"Error: Coordinates file is not valid JSON: {args.coordinates}")
        return 1
    except Exception as e:
        print(f"Error reading coordinates file: {str(e)}")
        return 1
    
    # Print matching mode
    if args.contour:
        print("Using contour-based matching (fast but less robust)")
    elif args.full:
        print("Using full holistic matching (slow but most robust)")
    else:
        print("Using simplified holistic matching (balanced speed and accuracy)")
    
    # Build the command
    cmd = [
        "python3",
        matcher_path,
        "--drone-image", args.drone_image,
        "--coordinates", args.coordinates,
        "--output", args.output
    ] + flags
    
    # Execute the command
    print("\nRunning matcher...")
    print(f"Command: {' '.join(cmd)}\n")
    os.execvp(cmd[0], cmd)  # Replace the current process
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 