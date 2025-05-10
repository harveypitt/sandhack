#!/usr/bin/env python3
"""
Test script for LLM Contextual Analyzer

This script tests the LLM Contextual Analyzer with the example image from the data directory.
"""

import os
import json
from pathlib import Path
from contextual_analyzer import LLMContextualAnalyzer

# Get the absolute path to the repository root
REPO_ROOT = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent.parent
DATA_DIR = REPO_ROOT / "data" / "example" / "images"

def main():
    # Example image path
    image_path = DATA_DIR / "rickmansworth_example.jpg"
    
    if not image_path.exists():
        print(f"Example image not found at: {image_path}")
        return
    
    print(f"Testing with image: {image_path}")
    
    # Initialize the analyzer
    analyzer = LLMContextualAnalyzer()
    
    # Process the image
    result = analyzer.process_image(str(image_path))
    
    if result:
        print("\nResults:")
        print(json.dumps(result, indent=2))
        
        # Save results to file
        output_path = Path("analysis_results.json")
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nResults saved to: {output_path.absolute()}")
    else:
        print("Analysis failed. Check logs for details.")

if __name__ == "__main__":
    main() 