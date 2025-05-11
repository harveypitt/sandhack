#!/usr/bin/env python3
"""
Contour Extractor Module

This module provides functionality to extract contours from images.
It processes images to detect edges and contours of objects and features,
which can be used for pattern matching and location estimation.

Classes:
    ContourExtractor: Main class for extracting and visualizing contours from images

Functions:
    extract_contours: Extract contours from an image with configurable threshold
    _identify_major_features: Identify major features from extracted contours

Dependencies:
    - OpenCV
    - NumPy
"""

import cv2
import numpy as np
import base64
from pathlib import Path
import logging
import json
import os
import uuid

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('contour_extractor.log')
    ]
)
logger = logging.getLogger(__name__)

class ContourExtractor:
    """
    Class for extracting contours from images and visualizing them.
    
    This class provides methods to process images, extract contours
    using adaptive thresholding, and generate visualizations. It's
    particularly useful for computer vision-based location estimation.
    
    Attributes:
        temp_dir (Path): Directory for storing temporary image files
    """
    
    def __init__(self):
        """
        Initialize the ContourExtractor.
        
        Sets up a temporary directory for storing intermediate files
        during processing. The directory is created in /tmp if possible,
        or falls back to a local directory.
        """
        logger.info("Contour Extractor initialized")
        try:
            # Use a temp directory that's definitely writable for the non-root user
            self.temp_dir = Path("/tmp/contour_images")
            os.makedirs(self.temp_dir, exist_ok=True)
            logger.info(f"Created temp directory at {self.temp_dir}")
        except Exception as e:
            logger.error(f"Error creating temp directory: {str(e)}")
            # Fallback to current directory if /tmp is not writable
            self.temp_dir = Path("./contour_images")
            os.makedirs(self.temp_dir, exist_ok=True)
            logger.info(f"Created fallback temp directory at {self.temp_dir}")
    
    def extract_contours(self, image_input, threshold=50):
        """
        Extract contours from an image.
        
        Processing steps:
        1. Convert image to grayscale
        2. Apply Gaussian blur to reduce noise
        3. Apply Canny edge detection with dynamic thresholds
        4. Find and filter contours based on area
        5. Generate visualization image with contours overlaid
        
        Args:
            image_input (str or np.ndarray): Path to the input image or the image data as a NumPy array.
            threshold (int): Contour detection threshold (0-100). 
                             Lower values extract fewer but stronger contours.
            
        Returns:
            dict: A dictionary containing:
                - original_image: Base64-encoded original image (if path was provided), else None
                - contour_visualization: Base64-encoded visualization
                - contours: List of extracted contours (points)
                - contour_count: Number of contours found
                - major_features: List of identified major features
                - threshold_used: The threshold value used
                
        Raises:
            Exception: If image processing fails
        """
        try:
            img = None
            orig_base64 = None
            image_path_for_logging = None

            if isinstance(image_input, str):
                logger.info(f"Extracting contours from image path: {image_input} with threshold: {threshold}")
                image_path_for_logging = image_input
                img = cv2.imread(image_input)
                if img is None:
                    logger.error(f"Failed to read image: {image_input}")
                    return None
                with open(image_input, "rb") as img_file:
                    orig_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            elif isinstance(image_input, np.ndarray):
                logger.info(f"Extracting contours from image data (shape: {image_input.shape}) with threshold: {threshold}")
                image_path_for_logging = f"image_data_shape_{image_input.shape}"
                img = image_input
                # orig_base64 will be None as we don't have the original file path
            else:
                logger.error(f"Invalid image_input type: {type(image_input)}. Must be str or np.ndarray.")
                return None

            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Map the threshold from 0-100 to appropriate Canny thresholds
            # Lower UI threshold = fewer contours (higher canny thresholds)
            # Higher UI threshold = more contours (lower canny thresholds)
            canny_low = int(150 - threshold)  # Invert the relationship
            canny_high = int(canny_low * 2)   # Typically high is twice the low threshold
            
            # Apply Canny edge detection with dynamic thresholds
            edges = cv2.Canny(blurred, canny_low, canny_high)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Scale the minimum area based on threshold
            # Lower threshold = higher minimum area (more filtering)
            min_area = int(100 + (100 - threshold) * 2)
            filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
            
            # Create visualization image
            viz_img = img.copy()
            cv2.drawContours(viz_img, filtered_contours, -1, (0, 255, 0), 2)
            
            # Save visualization image
            viz_path = self.temp_dir / f"{uuid.uuid4()}_contour_viz.jpg"
            cv2.imwrite(str(viz_path), viz_img)
            
            # Encode original and visualization images to base64
            # Ensure orig_base64 is only set if image_input was a path and successfully read
            # The viz_base64 part is fine as viz_path is always created.
            
            with open(viz_path, "rb") as viz_file:
                viz_base64 = base64.b64encode(viz_file.read()).decode('utf-8')
            
            # Convert contours to serializable format
            serializable_contours = []
            for cnt in filtered_contours:
                # Convert each contour to a list of points
                points = cnt.reshape(-1, 2).tolist()
                serializable_contours.append(points)
            
            # Create result
            result = {
                "original_image": orig_base64,
                "contour_visualization": viz_base64,
                "contours": serializable_contours,
                "contour_count": len(filtered_contours),
                "major_features": self._identify_major_features(filtered_contours, img.shape),
                "threshold_used": threshold
            }
            
            # Clean up visualization image
            if viz_path.exists():
                viz_path.unlink()
            
            return result
        
        except Exception as e:
            logger.error(f"Error extracting contours: {str(e)}")
            return None
    
    def _identify_major_features(self, contours, img_shape):
        """
        Identify major features from contours.
        
        This method analyzes contours to identify significant features
        based on properties such as size, shape, and distribution.
        It categorizes contours into structural elements, linear features
        (like roads or rivers), and compact features (like buildings).
        
        Args:
            contours (list): List of contours extracted from the image
            img_shape (tuple): Shape of the original image (height, width, channels)
            
        Returns:
            list: List of identified major features as descriptive strings
        """
        features = []
        
        # Get image dimensions
        height, width = img_shape[:2]
        img_area = height * width
        
        # Identify large contours
        large_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > img_area * 0.05]
        if large_contours:
            features.append(f"Found {len(large_contours)} major structural elements")
        
        # Check for linear features (roads, rivers)
        linear_contours = []
        for cnt in contours:
            perimeter = cv2.arcLength(cnt, True)
            area = cv2.contourArea(cnt)
            if perimeter > 0 and area > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                if circularity < 0.2:  # Linear features have low circularity
                    linear_contours.append(cnt)
        
        if linear_contours:
            features.append(f"Found {len(linear_contours)} potential linear features (roads, rivers, etc.)")
        
        # Check for compact shapes (buildings, cars)
        compact_contours = []
        for cnt in contours:
            if cv2.contourArea(cnt) > 100:  # Minimum area threshold
                perimeter = cv2.arcLength(cnt, True)
                area = cv2.contourArea(cnt)
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    if circularity > 0.6:  # Compact features have high circularity
                        compact_contours.append(cnt)
        
        if compact_contours:
            features.append(f"Found {len(compact_contours)} potential compact features (buildings, vehicles, etc.)")
        
        return features 