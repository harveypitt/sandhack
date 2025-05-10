#!/usr/bin/env python3
"""
Batch Test for LLM Contextual Analyzer

This script tests the LLM Contextual Analyzer with all images in the Competition Release folder,
checking if the estimated location matches the expected location from the filename.
"""

import os
import json
import time
import argparse
from pathlib import Path
from tabulate import tabulate
from src.components.llm_analysis.contextual_analyzer import LLMContextualAnalyzer

# Set up logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('batch_test_results.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def check_location_match(estimated_location, expected_location):
    """Check if the estimated location matches the expected location."""
    if not estimated_location:
        return False
    # Case-insensitive search
    return expected_location.lower() in estimated_location.lower()

def main():
    parser = argparse.ArgumentParser(description='Batch test LLM Contextual Analyzer')
    parser.add_argument('--output', '-o', default='batch_results.json', 
                        help='Path to save results json file')
    parser.add_argument('--dir', '-d', default='Competition Release',
                        help='Directory containing the images')
    parser.add_argument('--global-mode', '-g', action='store_true',
                       help='Use global analysis mode instead of UK-specific')
    args = parser.parse_args()
    
    # Find all jpg files in the Competition Release directory
    images_dir = Path(args.dir)
    image_files = list(images_dir.glob('*.jpg'))
    
    if not image_files:
        logger.error(f"No .jpg files found in {images_dir}")
        return 1
    
    logger.info(f"Found {len(image_files)} images to process")
    
    # Initialize analyzer
    analyzer = LLMContextualAnalyzer(global_mode=args.global_mode)
    
    mode_str = "global" if args.global_mode else "UK-specific"
    logger.info(f"Using {mode_str} analysis mode")
    
    # Results containers
    results = []
    summary = {
        'total_images': len(image_files),
        'successful_analyses': 0,
        'location_matches': 0,
        'location_mismatches': 0,
        'analysis_failures': 0
    }
    
    # Table results for nice display
    table_results = []
    
    # Process each image
    for idx, image_path in enumerate(sorted(image_files), 1):
        filename = image_path.name
        logger.info(f"[{idx}/{len(image_files)}] Processing {filename}")
        
        # Extract expected location from filename (either "Reading" or "Rickmansworth")
        expected_location = filename.split('_')[0]
        logger.info(f"Expected location: {expected_location}")
        
        # Measure processing time
        start_time = time.time()
        result = analyzer.process_image(str(image_path))
        processing_time = time.time() - start_time
        
        # Check result
        if result:
            summary['successful_analyses'] += 1
            estimated_location = result.get('estimated-location', '')
            confidence = result.get('confidence', 0)
            
            # Check if the estimated location contains the expected location name
            location_match = check_location_match(estimated_location, expected_location)
            
            if location_match:
                summary['location_matches'] += 1
                match_status = "✓"
            else:
                summary['location_mismatches'] += 1
                match_status = "✗"
            
            # Add to table data
            table_results.append([
                filename, 
                expected_location,
                estimated_location,
                confidence,
                f"{processing_time:.1f}s",
                match_status
            ])
            
            # Add to detailed results
            result_entry = {
                'filename': filename,
                'expected_location': expected_location,
                'estimated_location': estimated_location,
                'confidence': confidence,
                'processing_time': processing_time,
                'location_match': location_match,
                'full_result': result
            }
            results.append(result_entry)
            
            logger.info(f"Estimated location: {estimated_location} (confidence: {confidence})")
            logger.info(f"Location match: {location_match}")
        else:
            summary['analysis_failures'] += 1
            table_results.append([
                filename, 
                expected_location,
                "ANALYSIS FAILED",
                "-",
                f"{processing_time:.1f}s",
                "!"
            ])
            results.append({
                'filename': filename,
                'expected_location': expected_location,
                'analysis_failed': True,
                'processing_time': processing_time
            })
            logger.error(f"Analysis failed for {filename}")
        
        logger.info(f"Processing time: {processing_time:.1f} seconds")
        logger.info("-" * 50)
    
    # Save detailed results as JSON
    with open(args.output, 'w') as f:
        json.dump({
            'summary': summary,
            'results': results
        }, f, indent=2)
    
    # Print summary
    logger.info("\nBatch Test Results:")
    logger.info(f"Total images: {summary['total_images']}")
    logger.info(f"Successful analyses: {summary['successful_analyses']}")
    logger.info(f"Location matches: {summary['location_matches']}")
    logger.info(f"Location mismatches: {summary['location_mismatches']}")
    logger.info(f"Analysis failures: {summary['analysis_failures']}")
    
    match_rate = (summary['location_matches'] / summary['total_images']) * 100 if summary['total_images'] > 0 else 0
    logger.info(f"Match rate: {match_rate:.1f}%")
    
    # Print table of results
    table_headers = ["Filename", "Expected", "Estimated", "Confidence", "Time", "Match"]
    print("\nDetailed Results:")
    print(tabulate(table_results, headers=table_headers, tablefmt="grid"))
    
    # Also save table to log
    logger.info("\nDetailed Results:\n" + tabulate(table_results, headers=table_headers, tablefmt="grid"))
    
    logger.info(f"\nDetailed results saved to {args.output}")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main()) 