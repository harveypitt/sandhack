#!/usr/bin/env python3
"""
Contour Extractor Component - Extracts contours from drone and satellite images 
for subsequent alignment and matching by the Rotation Normalization Agent.
"""

import cv2
import numpy as np
import json
import matplotlib.pyplot as plt
import os
from typing import Dict, List, Tuple, Any, Optional

class ContourExtractor:
    """
    Extracts contours from drone and satellite images for use in image matching.
    """
    
    def __init__(self, 
                 canny_threshold1: int = 100, 
                 canny_threshold2: int = 200,
                 min_contour_length: int = 150,
                 gaussian_blur_kernel: Tuple[int, int] = (5, 5)):
        """
        Initialize the ContourExtractor with parameters for edge detection and filtering.
        
        Args:
            canny_threshold1: Lower threshold for Canny edge detector
            canny_threshold2: Upper threshold for Canny edge detector
            min_contour_length: Minimum length (in pixels) for a contour to be considered valid
            gaussian_blur_kernel: Kernel size for Gaussian blur preprocessing
        """
        self.canny_threshold1 = canny_threshold1
        self.canny_threshold2 = canny_threshold2
        self.min_contour_length = min_contour_length
        self.gaussian_blur_kernel = gaussian_blur_kernel
        
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocess an image for contour extraction.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Preprocessed image as numpy array
        """
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Could not load image from {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, self.gaussian_blur_kernel, 0)
        
        # Apply Canny edge detection
        edges = cv2.Canny(blurred, 
                          self.canny_threshold1, 
                          self.canny_threshold2)
        
        return edges
    
    def extract_contours(self, preprocessed_image: np.ndarray) -> List[np.ndarray]:
        """
        Extract contours from a preprocessed image.
        
        Args:
            preprocessed_image: Image that has been processed with edge detection
            
        Returns:
            List of contours as numpy arrays
        """
        # Find contours in the edge image
        contours, _ = cv2.findContours(
            preprocessed_image, 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Filter contours by length
        filtered_contours = []
        for contour in contours:
            if len(contour) >= self.min_contour_length:
                filtered_contours.append(contour)
        
        return filtered_contours
    
    def visualize_contours(self, 
                          image_path: str, 
                          contours: List[np.ndarray], 
                          output_path: Optional[str] = None) -> None:
        """
        Visualize contours on the original image.
        
        Args:
            image_path: Path to the original image
            contours: List of contours to visualize
            output_path: Path to save the visualization (if None, displays instead)
        """
        # Load the original image
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Could not load image from {image_path}")
        
        # Create a copy for visualization
        vis_image = image.copy()
        
        # Draw contours on the image
        cv2.drawContours(vis_image, contours, -1, (0, 255, 0), 2)
        
        # Convert from BGR to RGB for matplotlib
        vis_image_rgb = cv2.cvtColor(vis_image, cv2.COLOR_BGR2RGB)
        
        # Display or save
        plt.figure(figsize=(10, 8))
        plt.imshow(vis_image_rgb)
        plt.title(f"Contours from {os.path.basename(image_path)}")
        plt.axis('off')
        
        if output_path:
            plt.savefig(output_path, bbox_inches='tight')
            plt.close()
        else:
            plt.show()
    
    def format_contours_for_output(self, 
                                  contours: List[np.ndarray]) -> List[Dict[str, Any]]:
        """
        Format contours for JSON output.
        
        Args:
            contours: List of contours as numpy arrays
            
        Returns:
            List of contours in the expected JSON format
        """
        formatted_contours = []
        
        for contour in contours:
            # Convert to a list of [x, y] points
            points = contour.reshape(-1, 2).tolist()
            
            # Calculate contour length
            length = cv2.arcLength(contour, closed=True)
            
            formatted_contours.append({
                "points": points,
                "length": float(length)
            })
        
        return formatted_contours
    
    def process_drone_image(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Process a drone image to extract contours.
        
        Args:
            image_path: Path to the drone image
            
        Returns:
            Formatted contours from the drone image
        """
        # Preprocess the image
        preprocessed = self.preprocess_image(image_path)
        
        # Extract contours
        contours = self.extract_contours(preprocessed)
        
        # Format for output
        return self.format_contours_for_output(contours)
    
    def process_satellite_image(self, 
                               image_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a satellite image to extract contours.
        
        Args:
            image_info: Dictionary with satellite image path and metadata
            
        Returns:
            Dictionary with area ID, bounds, and formatted contours
        """
        # Extract info from the input
        area_id = image_info["area_id"]
        image_path = image_info["image_path"]
        bounds = image_info["bounds"]
        
        # Preprocess the image
        preprocessed = self.preprocess_image(image_path)
        
        # Extract contours
        contours = self.extract_contours(preprocessed)
        
        # Format for output
        return {
            "area_id": area_id,
            "contours": self.format_contours_for_output(contours),
            "bounds": bounds
        }
    
    def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input JSON data to extract contours from all images.
        
        Args:
            input_data: Input data in the expected JSON format
            
        Returns:
            Output data with extracted contours
        """
        # Extract drone image contours
        drone_contours = self.process_drone_image(input_data["drone_image_path"])
        
        # Extract satellite image contours
        satellite_contours = []
        for sat_image in input_data["satellite_images"]:
            satellite_contours.append(self.process_satellite_image(sat_image))
        
        # Format the complete output
        output = {
            "image_id": input_data["image_id"],
            "drone_contours": drone_contours,
            "satellite_contours": satellite_contours
        }
        
        return output

# Example usage
if __name__ == "__main__":
    # This is just an example - you'll need to replace with actual paths and data
    extractor = ContourExtractor()
    
    # Example input data
    input_data = {
        "image_id": "test_image_001",
        "drone_image_path": "path/to/drone/image.jpg",
        "satellite_images": [
            {
                "area_id": "area_001",
                "image_path": "path/to/satellite/image.jpg",
                "bounds": [0, 0, 1000, 1000]
            }
        ]
    }
    
    # Process the input
    try:
        output = extractor.process_input(input_data)
        print(f"Extracted {len(output['drone_contours'])} contours from drone image")
        for sat_contours in output["satellite_contours"]:
            print(f"Extracted {len(sat_contours['contours'])} contours from satellite image {sat_contours['area_id']}")
    except Exception as e:
        print(f"Error processing images: {e}") 