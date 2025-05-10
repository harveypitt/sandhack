#!/usr/bin/env python3
"""
Holistic Contour Matcher

Matches drone and satellite images by treating all contours as a single pattern.
Instead of comparing individual contours, this approach creates composite images 
containing all contours and finds the optimal transformation to align them.
"""

import os
import json
import argparse
import cv2
import numpy as np
import matplotlib.pyplot as plt
import time
from datetime import timedelta
from typing import List, Dict, Any, Tuple, Optional

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Holistic contour matching between drone and satellite images")
    parser.add_argument("--input-json", required=True, help="Path to input JSON file with contour data")
    parser.add_argument("--output-dir", default="holistic_matcher_output", help="Directory to save output")
    parser.add_argument("--min-score", type=float, default=0.15, help="Minimum similarity score (0-1)")
    parser.add_argument("--min-scale", type=float, default=0.5, help="Minimum scale factor to try")
    parser.add_argument("--max-scale", type=float, default=2.0, help="Maximum scale factor to try")
    parser.add_argument("--scale-steps", type=int, default=10, help="Number of scale steps to try")
    parser.add_argument("--angle-step", type=float, default=10, help="Step size for rotation angles (degrees)")
    parser.add_argument("--debug", action="store_true", help="Enable detailed debugging output")
    return parser.parse_args()

def contour_to_numpy(contour_points: List[List[float]]) -> np.ndarray:
    """Convert contour points to numpy array format for OpenCV."""
    np_contour = np.array(contour_points, dtype=np.float32)
    if len(np_contour.shape) == 2:
        np_contour = np_contour.reshape(-1, 1, 2)
    return np_contour

def create_contour_image(contours: List[np.ndarray], 
                         image_size: Tuple[int, int] = (1000, 1000), 
                         thickness: int = 1,
                         center: bool = True) -> np.ndarray:
    """Create a binary image with all contours drawn.
    
    Args:
        contours: List of contours to draw
        image_size: Size of the output image (height, width)
        thickness: Thickness of contour lines. Use -1 for filled contours.
        center: Whether to center contours in the image
        
    Returns:
        Binary image with contours drawn
    """
    height, width = image_size
    img = np.zeros((height, width), dtype=np.uint8)
    
    if not contours:
        return img
    
    # Find bounding box for all contours together if centering
    if center:
        all_points = np.vstack([c.reshape(-1, 2) for c in contours])
        min_x, min_y = np.min(all_points, axis=0)
        max_x, max_y = np.max(all_points, axis=0)
        
        center_x, center_y = (min_x + max_x) / 2, (min_y + max_y) / 2
        target_center_x, target_center_y = width / 2, height / 2
        
        # Calculate offset to center the pattern
        offset_x = int(target_center_x - center_x)
        offset_y = int(target_center_y - center_y)
        
        # Apply offset to all contours
        centered_contours = []
        for contour in contours:
            centered = contour.copy()
            centered[:, :, 0] += offset_x
            centered[:, :, 1] += offset_y
            centered_contours.append(centered)
        
        contours_to_draw = centered_contours
    else:
        contours_to_draw = contours
    
    # Draw all contours
    for contour in contours_to_draw:
        cv2.drawContours(img, [contour.astype(np.int32)], 0, 255, thickness)
    
    return img

def transform_image(img: np.ndarray, 
                   scale: float = 1.0, 
                   angle: float = 0.0,
                   tx: int = 0,
                   ty: int = 0) -> np.ndarray:
    """Apply scale, rotation and translation to an image.
    
    Args:
        img: Input image
        scale: Scale factor
        angle: Rotation angle in degrees
        tx: X translation
        ty: Y translation
        
    Returns:
        Transformed image
    """
    height, width = img.shape[:2]
    center = (width // 2, height // 2)
    
    # Get rotation matrix
    rot_mat = cv2.getRotationMatrix2D(center, angle, scale)
    
    # Add translation
    rot_mat[0, 2] += tx
    rot_mat[1, 2] += ty
    
    # Apply transformation
    transformed = cv2.warpAffine(img, rot_mat, (width, height), flags=cv2.INTER_LINEAR)
    
    return transformed

def calculate_image_similarity(img1: np.ndarray, img2: np.ndarray) -> Tuple[float, int, int, int]:
    """Calculate similarity between two binary images using IoU.
    
    Args:
        img1: First binary image
        img2: Second binary image
        
    Returns:
        Tuple of (IoU score, intersection area, area of img1, area of img2)
    """
    # Calculate areas
    area1 = cv2.countNonZero(img1)
    area2 = cv2.countNonZero(img2)
    
    # Calculate intersection
    intersection = cv2.bitwise_and(img1, img2)
    intersection_area = cv2.countNonZero(intersection)
    
    # Calculate union
    union = cv2.bitwise_or(img1, img2)
    union_area = cv2.countNonZero(union)
    
    # Calculate IoU
    iou = intersection_area / union_area if union_area > 0 else 0
    
    return iou, intersection_area, area1, area2

def find_best_transformation(drone_img: np.ndarray, 
                             satellite_img: np.ndarray,
                             min_scale: float = 0.5,
                             max_scale: float = 2.0,
                             scale_steps: int = 10,
                             angle_step: float = 10.0,
                             translation_range: int = 50,
                             translation_step: int = 10,
                             debug: bool = False) -> Tuple[float, float, float, int, int, float]:
    """Find the best transformation parameters to align drone image with satellite image.
    
    Args:
        drone_img: Binary image with drone contours
        satellite_img: Binary image with satellite contours
        min_scale: Minimum scale factor to try
        max_scale: Maximum scale factor to try
        scale_steps: Number of scale steps to try
        angle_step: Rotation angle step in degrees
        translation_range: Range for translation in pixels
        translation_step: Step size for translation in pixels
        debug: Whether to print debug information
        
    Returns:
        Tuple of (best scale, best angle, best IoU score, best tx, best ty, total comparisons)
    """
    scale_factors = np.linspace(min_scale, max_scale, scale_steps)
    angles = np.arange(0, 360, angle_step)
    tx_values = range(-translation_range, translation_range + 1, translation_step)
    ty_values = range(-translation_range, translation_range + 1, translation_step)
    
    best_iou = 0.0
    best_scale = 1.0
    best_angle = 0.0
    best_tx = 0
    best_ty = 0
    total_comparisons = 0
    
    # For progress tracking
    total_iterations = len(scale_factors) * len(angles) * len(tx_values) * len(ty_values)
    iterations_done = 0
    start_time = time.time()
    
    for scale in scale_factors:
        for angle in angles:
            # Apply initial transformation (scale and rotation)
            transformed = transform_image(drone_img, scale=scale, angle=angle)
            
            # Then try different translations
            for tx in tx_values:
                for ty in ty_values:
                    # Apply translation
                    final_transformed = transform_image(transformed, tx=tx, ty=ty)
                    
                    # Calculate similarity
                    iou, _, _, _ = calculate_image_similarity(final_transformed, satellite_img)
                    total_comparisons += 1
                    
                    # Update best parameters if better
                    if iou > best_iou:
                        best_iou = iou
                        best_scale = scale
                        best_angle = angle
                        best_tx = tx
                        best_ty = ty
                        
                        if debug:
                            print(f"New best match: scale={scale:.2f}, angle={angle:.1f}°, "
                                 f"tx={tx}, ty={ty}, IoU={iou:.3f}")
                    
                    # Update progress (every 1000 iterations or on last iteration)
                    iterations_done += 1
                    if debug and (iterations_done % 1000 == 0 or iterations_done == total_iterations):
                        elapsed = time.time() - start_time
                        remaining = (elapsed / iterations_done) * (total_iterations - iterations_done)
                        progress = iterations_done / total_iterations * 100
                        print(f"Progress: {progress:.1f}% ({iterations_done}/{total_iterations}), "
                             f"Best IoU: {best_iou:.3f}, "
                             f"ETA: {format_time(remaining)}")
    
    return best_scale, best_angle, best_iou, best_tx, best_ty, total_comparisons

def visualize_alignment(drone_img: np.ndarray, 
                      satellite_img: np.ndarray, 
                      scale: float,
                      angle: float,
                      tx: int,
                      ty: int,
                      iou: float,
                      area_id: str,
                      output_path: Optional[str] = None):
    """Visualize the alignment of drone and satellite contours.
    
    Args:
        drone_img: Binary image with drone contours
        satellite_img: Binary image with satellite contours
        scale: Scale factor to apply to drone image
        angle: Rotation angle to apply to drone image
        tx: X translation to apply
        ty: Y translation to apply
        iou: IoU score
        area_id: ID of the satellite area
        output_path: Path to save the visualization, if None will display on screen
    """
    # Transform drone image
    transformed_drone = transform_image(drone_img, scale=scale, angle=angle, tx=tx, ty=ty)
    
    # Create RGB visualization
    height, width = drone_img.shape
    vis_image = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Satellite contours in blue
    vis_image[satellite_img > 0] = [255, 0, 0]  # Blue
    
    # Drone contours in green
    vis_image[transformed_drone > 0] = [0, 255, 0]  # Green
    
    # Intersection in yellow
    intersection = cv2.bitwise_and(transformed_drone, satellite_img)
    vis_image[intersection > 0] = [0, 255, 255]  # Yellow
    
    # Add text with match information
    cv2.putText(
        vis_image, 
        f"IoU: {iou:.3f}, Scale: {scale:.2f}, Angle: {angle:.1f}°", 
        (10, 30), 
        cv2.FONT_HERSHEY_SIMPLEX, 
        1, 
        (255, 255, 255), 
        2
    )
    
    # Display or save
    plt.figure(figsize=(10, 8))
    plt.imshow(vis_image)
    plt.title(f"Holistic Match for area {area_id}")
    plt.axis('off')
    
    if output_path:
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
    else:
        plt.show()

def format_time(seconds):
    """Format time in seconds to a more readable format."""
    return str(timedelta(seconds=int(seconds)))

def main():
    """Run the holistic contour matching."""
    args = parse_args()
    debug = args.debug
    
    # Start timer
    start_time = time.time()
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"Loading contour data from: {args.input_json}")
    with open(args.input_json, 'r') as f:
        input_data = json.load(f)
    
    image_id = input_data["image_id"]
    drone_contours_data = input_data["drone_contours"]
    satellite_areas = input_data["satellite_contours"]
    
    # Convert drone contours to numpy arrays
    drone_np_contours = []
    for contour_data in drone_contours_data:
        points = contour_data["points"]
        np_contour = contour_to_numpy(points)
        drone_np_contours.append(np_contour)
    
    # Create composite image with all drone contours
    print("Creating composite image with all drone contours...")
    drone_composite = create_contour_image(drone_np_contours, thickness=1)
    
    # Save drone composite image
    drone_composite_path = os.path.join(args.output_dir, "drone_composite.png")
    cv2.imwrite(drone_composite_path, drone_composite)
    print(f"Saved drone composite image to {drone_composite_path}")
    
    # Process each satellite area
    best_matches = []
    
    print(f"\nProcessing {len(satellite_areas)} satellite areas with holistic matching...")
    
    for area_idx, sat_area in enumerate(satellite_areas):
        area_id = sat_area["area_id"]
        area_start_time = time.time()
        
        print(f"Processing area {area_id} ({area_idx+1}/{len(satellite_areas)})")
        
        # Convert satellite contours to numpy arrays
        sat_np_contours = []
        for contour_data in sat_area["contours"]:
            points = contour_data["points"]
            np_contour = contour_to_numpy(points)
            sat_np_contours.append(np_contour)
        
        # Create composite image with all satellite contours
        satellite_composite = create_contour_image(sat_np_contours, thickness=1)
        
        # Save satellite composite image
        sat_composite_path = os.path.join(args.output_dir, f"satellite_composite_{area_id}.png")
        cv2.imwrite(sat_composite_path, satellite_composite)
        print(f"  Saved satellite composite image to {sat_composite_path}")
        
        # Find the best transformation to align the images
        print(f"  Finding optimal alignment for area {area_id}...")
        best_scale, best_angle, best_iou, best_tx, best_ty, total_comparisons = find_best_transformation(
            drone_composite, 
            satellite_composite,
            min_scale=args.min_scale,
            max_scale=args.max_scale,
            scale_steps=args.scale_steps,
            angle_step=args.angle_step,
            debug=debug
        )
        
        # Only consider as a match if above threshold
        if best_iou >= args.min_score:
            best_matches.append({
                "area_id": area_id,
                "similarity_score": float(best_iou),
                "scale_factor": float(best_scale),
                "rotation_angle": float(best_angle),
                "translation_x": int(best_tx),
                "translation_y": int(best_ty)
            })
            
            # Create visualization of the alignment
            vis_path = os.path.join(args.output_dir, f"holistic_match_{area_id}.png")
            visualize_alignment(
                drone_composite, 
                satellite_composite, 
                best_scale, 
                best_angle,
                best_tx,
                best_ty,
                best_iou,
                area_id,
                vis_path
            )
            print(f"  Created visualization at {vis_path}")
        
        area_time = time.time() - area_start_time
        print(f"  Area {area_id}: Best match has IoU={best_iou:.3f}, scale={best_scale:.2f}, "
              f"angle={best_angle:.1f}°, tx={best_tx}, ty={best_ty}")
        print(f"  Completed {total_comparisons} comparisons in {area_time:.2f}s")
    
    # Sort results by similarity score
    best_matches.sort(key=lambda x: x["similarity_score"], reverse=True)
    
    # Format the output
    output = {
        "image_id": image_id,
        "holistic_match_results": best_matches
    }
    
    # Save match results to JSON
    output_json_path = os.path.join(args.output_dir, "holistic_match_results.json")
    with open(output_json_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"Saved match results to {output_json_path}")
    
    # Print summary of matches
    match_count = len(best_matches)
    print(f"\nFound matches for {match_count}/{len(satellite_areas)} satellite areas")
    
    if match_count > 0:
        # Print top matches
        print("\nTop matches:")
        for i, match in enumerate(best_matches):
            print(f"  {i+1}. Area {match['area_id']} with score {match['similarity_score']:.3f}, "
                 f"scale={match['scale_factor']:.2f}, angle={match['rotation_angle']:.1f}°")
    
    # Calculate and display total runtime
    total_time = time.time() - start_time
    print(f"\nHolistic matching completed successfully in {format_time(total_time)} ({total_time:.2f}s)")

if __name__ == "__main__":
    main() 