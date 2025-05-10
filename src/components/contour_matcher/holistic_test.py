#!/usr/bin/env python3
"""
Basic test script for the holistic contour matcher component.
This script provides a simple way to run the holistic matcher with default parameters.
"""

import argparse
import os
from holistic_matcher import main as holistic_main

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Simple test for holistic contour matching")
    parser.add_argument("--input-json", required=True, help="Path to input JSON file with contour data")
    parser.add_argument("--output-dir", default="holistic_output", help="Directory to save output")
    parser.add_argument("--debug", action="store_true", help="Enable detailed debugging output")
    parser.add_argument("--fast", action="store_true", help="Use faster settings (fewer scale/rotation steps)")
    return parser.parse_args()

def main():
    """Run simplified holistic contour matching test."""
    args = parse_args()
    
    # Prepare arguments for holistic matcher
    holistic_args = []
    
    # Required arguments
    holistic_args.extend(["--input-json", args.input_json])
    holistic_args.extend(["--output-dir", args.output_dir])
    
    # Use faster settings if requested
    if args.fast:
        holistic_args.extend([
            "--min-scale", "0.8",
            "--max-scale", "1.2",
            "--scale-steps", "5",
            "--angle-step", "20"
        ])
    
    # Debug mode
    if args.debug:
        holistic_args.append("--debug")
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Call holistic matcher with arguments
    import sys
    sys.argv = [sys.argv[0]] + holistic_args
    holistic_main()

if __name__ == "__main__":
    main() 