#!/usr/bin/env python3
"""
Test script for LLM Contextual Analyzer

This script tests the LLM Contextual Analyzer with the example image from the data directory.
"""

import os
import json
import sys
from pathlib import Path
from contextual_analyzer import LLMContextualAnalyzer

# Get the absolute path to the repository root
REPO_ROOT = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent.parent
DATA_DIR = REPO_ROOT / "data" / "example" / "images"

def main():
    # Check for both jpg and png versions of the example image
    possible_image_paths = [
        DATA_DIR / "rickmansworth_example.jpg",
        DATA_DIR / "rickmansworth_example.png"
    ]
    
    # Find first existing image
    image_path = None
    for path in possible_image_paths:
        if path.exists():
            image_path = path
            break
    
    if not image_path:
        print(f"Error: Example image not found at either of these locations:")
        for path in possible_image_paths:
            print(f"  - {path}")
        return 1
    
    print(f"Testing with image: {image_path}")
    
    # Check connectivity to OpenAI API
    import socket
    try:
        # Try to resolve the OpenAI API hostname
        socket.gethostbyname('api.openai.com')
        print("✓ Network connectivity to OpenAI API confirmed")
    except socket.gaierror:
        print("⚠️ Warning: Cannot resolve api.openai.com - Check your internet connection")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return 1
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ Warning: OPENAI_API_KEY environment variable not found")
        print("  Make sure you have a .env file in the project root with your API key")
        return 1
    
    # Initialize the analyzer
    print("Initializing LLM Contextual Analyzer...")
    analyzer = LLMContextualAnalyzer()
    
    # Process the image
    print(f"Processing image... (this may take up to 5 minutes with the o3 model)")
    result = analyzer.process_image(str(image_path))
    
    if result:
        print("\nResults:")
        print(json.dumps(result, indent=2))
        
        if "usage" in result:
            print("\nToken usage:")
            print(json.dumps(result["usage"], indent=2))
        
        # Save results to file
        output_path = Path("analysis_results.json")
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nResults saved to: {output_path.absolute()}")
        return 0
    else:
        print("Analysis failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 