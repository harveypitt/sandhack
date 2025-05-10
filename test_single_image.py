#!/usr/bin/env python3
"""
Test LLM Contextual Analyzer on a single specific image.
"""

import json
import time
import argparse
from pathlib import Path
from src.components.llm_analysis.contextual_analyzer import LLMContextualAnalyzer

def main():
    parser = argparse.ArgumentParser(description='Test LLM Contextual Analyzer on a single image')
    parser.add_argument('image_path', help='Path to the image to analyze')
    parser.add_argument('--output', '-o', default='analysis_result.json', 
                        help='Path to save results json file')
    parser.add_argument('--global-mode', '-g', action='store_true',
                       help='Use global analysis mode instead of UK-specific')
    args = parser.parse_args()
    
    image_path = Path(args.image_path)
    if not image_path.exists():
        print(f"Error: Image not found at {image_path}")
        return 1
    
    print(f"Testing image: {image_path}")
    
    # Initialize analyzer
    analyzer = LLMContextualAnalyzer(global_mode=args.global_mode)
    
    mode_str = "global" if args.global_mode else "UK-specific"
    print(f"Using {mode_str} analysis mode")
    
    # Measure processing time
    start_time = time.time()
    print(f"Processing image... (this may take up to 5 minutes with the o3 model)")
    result = analyzer.process_image(str(image_path))
    processing_time = time.time() - start_time
    
    # Check result
    if result:
        print(f"\nProcessing completed in {processing_time:.1f} seconds")
        print("\nResults:")
        print(json.dumps(result, indent=2))
        
        # Save results to file
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nResults saved to: {args.output}")
        return 0
    else:
        print(f"Analysis failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main()) 