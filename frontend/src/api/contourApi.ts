/**
 * Contour API Client
 * 
 * API client functions for contour extraction and matching.
 * Provides functions to communicate with the backend contour analysis endpoints.
 * 
 * @module contourApi
 */
import axios from 'axios';

// API base URL - use a relative path
const API_URL = '/api';

/**
 * Extract contours from an image
 * 
 * Sends an image to the backend for contour extraction processing.
 * The backend will extract contours using computer vision algorithms
 * and return the results including visualizations.
 * 
 * @param formData - FormData containing:
 *   - file: The image file to process
 *   - threshold: Contour detection threshold (0-100)
 * 
 * @returns Promise with extraction results containing:
 *   - original_image: Base64-encoded original image
 *   - contour_visualization: Base64-encoded visualization with contours
 *   - contours: Array of contour points
 *   - contour_count: Number of contours detected
 *   - major_features: Array of identified major features
 *   - threshold_used: The threshold value that was used
 * 
 * @throws Error if the extraction fails
 */
export const extractContours = async (formData: FormData) => {
  try {
    const response = await axios.post(`${API_URL}/contour/extract`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  } catch (error) {
    console.error('Error extracting contours:', error);
    throw error;
  }
};

/**
 * Match contours between drone and satellite images
 * 
 * Sends a drone image and satellite images to the backend for contour matching.
 * The backend will extract contours from all images, compare them using shape
 * descriptors and pattern matching, and return the results with match scores
 * and visualizations.
 * 
 * @param formData - FormData containing:
 *   - drone_image: The drone image file
 *   - satellite_images: Up to 4 satellite image files
 *   - threshold: Contour detection threshold (0-100)
 * 
 * @returns Promise with matching results containing:
 *   - drone_image: Base64-encoded drone image
 *   - drone_contour_count: Number of contours in drone image
 *   - drone_contour_visualization: Base64-encoded drone contours
 *   - satellite_results: Array of results for each satellite image
 *   - best_match_index: Index of the best matching satellite image
 *   - best_match_score: Score of the best match (0-100)
 * 
 * Each satellite result includes:
 *   - image_index: Index of the satellite image
 *   - match_score: Match score (0-100)
 *   - satellite_image: Base64-encoded satellite image
 *   - visualization: Base64-encoded comparison visualization
 *   - holistic_visualization: Base64-encoded pattern visualization
 *   - contour_count: Number of contours detected
 *   - contour_visualization: Base64-encoded contour visualization
 *   - filename: Original filename of the satellite image
 * 
 * @throws Error if the matching fails
 */
export const matchContours = async (formData: FormData) => {
  try {
    const response = await axios.post(`${API_URL}/contour/match`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      // Increased timeout for processing multiple large images (2 minutes)
      timeout: 120000,
    });
    
    return response.data;
  } catch (error) {
    console.error('Error matching contours:', error);
    throw error;
  }
}; 