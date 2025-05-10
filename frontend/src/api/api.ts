/**
 * API client for interacting with the location estimation backend
 */
import axios from 'axios';

const API_URL = '/api';

// Create an axios instance with default config
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

/**
 * Upload and analyze an image to get location estimation using LLM
 * @param imageFile - The image file to analyze
 * @param globalMode - Whether to use global analysis mode
 * @returns Promise containing analysis result
 */
export const analyzeImage = async (imageFile: File, globalMode: boolean = false) => {
  const formData = new FormData();
  formData.append('file', imageFile);
  
  const response = await apiClient.post(`/llm-analysis/analyze?global_mode=${globalMode}`, formData);
  return response.data;
};

/**
 * Check if the API is running
 * @returns Promise containing API status
 */
export const checkApiStatus = async () => {
  const response = await apiClient.get('/');
  return response.data;
};

export default {
  analyzeImage,
  checkApiStatus,
}; 