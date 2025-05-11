/**
 * Drone Image Matcher API Client
 * 
 * API client functions for matching drone images with satellite images.
 * Provides functions to communicate with the backend drone image matcher endpoints.
 * 
 * @module droneMatcherApi
 */
import axios from 'axios';

// API base URL - use a relative path
const API_URL = '/api';

/**
 * Interface for the best match result
 */
export interface BestMatch {
  coordinates: {
    lat: number;
    lon: number;
    description?: string;
  };
  score: number;
  satellite_image?: string; // Base64 encoded satellite image
}

/**
 * Interface for all match results
 */
export interface MatchResult {
  drone_image: string;
  best_match: BestMatch;
  all_matches: BestMatch[];
}

/**
 * Match a drone image with satellite images from coordinates
 * 
 * Sends a drone image and coordinates file to the backend for location matching.
 * The backend will download satellite images for the coordinates, extract features,
 * and find the best match using the specified matching algorithm.
 * 
 * @param formData - FormData containing:
 *   - drone_image: The drone image file to match
 *   - coordinates_file: JSON file with coordinates to check
 *   - simplify: Whether to use simplified holistic matching (default: true)
 *   - use_contour: Whether to use contour matching instead of holistic (default: false)
 * 
 * @returns Promise with matching results containing:
 *   - drone_image: Name of the uploaded drone image
 *   - best_match: Object with coordinates and score of the best match
 *   - all_matches: Array of all matches with coordinates and scores
 * 
 * @throws Error if the matching fails
 */
export const matchDroneLocation = async (formData: FormData): Promise<MatchResult> => {
  try {
    // Get the coordinates file and create a new one with the correct content type
    const coordsFile = formData.get('coordinates_file') as File;
    if (coordsFile) {
      // Remove the original file
      formData.delete('coordinates_file');
      
      // Create a new file with explicit content type
      const coordsWithType = new File(
        [coordsFile], 
        coordsFile.name, 
        { type: 'application/json' }
      );
      
      // Add it back to the form
      formData.append('coordinates_file', coordsWithType);
    }
    
    const response = await axios.post(`${API_URL}/drone-matcher/match-location`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      // Set timeout to 5 minutes for downloading and processing images
      timeout: 300000,
    });
    
    return response.data;
  } catch (error) {
    console.error('Error matching drone location:', error);
    throw error;
  }
};

export default {
  matchDroneLocation,
}; 