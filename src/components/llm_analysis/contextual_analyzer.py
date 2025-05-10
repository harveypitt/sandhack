#!/usr/bin/env python3
"""
LLM Contextual Analysis Agent

This module uses OpenAI's o3 model to analyze drone images and generate structured
descriptions of the scenes, focusing on landmarks and features that can aid in relocalization.
"""

import os
import json
import base64
import logging
from pathlib import Path
from typing import Dict, List, Union, Optional
from dotenv import load_dotenv
import requests
from requests.exceptions import RequestException, Timeout

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("OpenAI API key not found in environment variables. Set OPENAI_API_KEY in .env file.")

# Constants
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
MODEL_NAME = "o3"  # OpenAI's o3 model

# Prompts from documentation
# Load prompts from a file or define them here
SCENE_ANALYSIS_PROMPT = """
You are an expert in aerial image analysis. Given a drone image taken in a British urban or suburban setting, describe the scene in detail, focusing on:
- Landmarks (e.g., parks, cul-de-sacs, road markings, housing styles)
- Notable features that could help identify the location
- Any clues about the region or town layout

Be concise but specific. Example output:
"This image shows a suburban street bordering a large park, with semi-detached houses, diagonal footpaths, and UK road markings. Likely a commuter town near London."
"""

OUTPUT_STRUCTURING_PROMPT = """
Given the following freeform description of a drone image scene, extract and return a JSON object with:
- "description": a concise summary of the scene
- "keywords": a list of key landmarks or features (e.g., "park", "cul-de-sac", "semi-detached houses", "UK road markings")

Output ONLY the JSON object, with no additional text.

Description: {description}
"""


class LLMContextualAnalyzer:
    """
    Uses o3 vision model to analyze drone images and generate structured descriptions.
    """
    
    def __init__(self):
        """Initialize the analyzer with API key and configurations."""
        self.api_key = OPENAI_API_KEY
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        logger.info("LLM Contextual Analyzer initialized")
    
    def encode_image(self, image_path: str) -> str:
        """
        Encode an image to base64 for API submission.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image: {e}")
            raise
    
    def analyze_image(self, image_path: str, timeout: int = 30) -> Optional[str]:
        """
        Send the image to o3 for scene analysis.
        
        Args:
            image_path: Path to the drone image
            timeout: API request timeout in seconds
            
        Returns:
            Raw text description of the scene or None if failed
        """
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None
            
        try:
            base64_image = self.encode_image(image_path)
            
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {
                        "role": "system", 
                        "content": SCENE_ANALYSIS_PROMPT
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyze this drone image for location features:"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 300
            }
            
            logger.info(f"Sending image analysis request for: {Path(image_path).name}")
            response = requests.post(
                OPENAI_API_URL,
                headers=self.headers,
                json=payload,
                timeout=timeout
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            if "choices" in response_data and len(response_data["choices"]) > 0:
                return response_data["choices"][0]["message"]["content"]
            else:
                logger.warning(f"Unexpected response format: {response_data}")
                return None
                
        except Timeout:
            logger.error(f"Request timed out after {timeout} seconds")
            return None
        except RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in image analysis: {e}")
            return None
    
    def structure_output(self, description: str, timeout: int = 10) -> Optional[Dict]:
        """
        Convert the freeform text description into a structured JSON format.
        
        Args:
            description: Raw text description from o3
            timeout: API request timeout in seconds
            
        Returns:
            Structured JSON with description and keywords or None if failed
        """
        try:
            prompt = OUTPUT_STRUCTURING_PROMPT.format(description=description)
            
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 300
            }
            
            logger.info("Sending request to structure output")
            response = requests.post(
                OPENAI_API_URL,
                headers=self.headers,
                json=payload,
                timeout=timeout
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            if "choices" in response_data and len(response_data["choices"]) > 0:
                json_text = response_data["choices"][0]["message"]["content"]
                
                # Clean up the response in case it contains markdown formatting or extra text
                try:
                    if "```" in json_text:
                        json_text = json_text.split("```")[1]
                        if json_text.startswith("json"):
                            json_text = json_text[4:]
                    
                    structured_data = json.loads(json_text.strip())
                    return structured_data
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}, Response was: {json_text}")
                    return None
            
            logger.warning(f"Unexpected response format: {response_data}")
            return None
            
        except Timeout:
            logger.error(f"Request timed out after {timeout} seconds")
            return None
        except RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in structuring output: {e}")
            return None
    
    def process_image(self, image_path: str, image_id: str = None) -> Optional[Dict]:
        """
        Full pipeline: analyze image and structure the output.
        
        Args:
            image_path: Path to the drone image
            image_id: Optional identifier for the image
            
        Returns:
            Structured JSON with image_id, description, and keywords
        """
        # Use filename as image_id if not provided
        if image_id is None:
            image_id = Path(image_path).stem
        
        # Step 1: Get raw description
        raw_description = self.analyze_image(image_path)
        if not raw_description:
            logger.error(f"Failed to analyze image: {image_path}")
            return None
        
        logger.info(f"Raw description: {raw_description}")
        
        # Step 2: Structure the output
        structured_data = self.structure_output(raw_description)
        if not structured_data:
            logger.error(f"Failed to structure output for image: {image_path}")
            return None
        
        # Step 3: Add image_id to the structured data
        structured_data["image_id"] = image_id
        
        return structured_data


# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze drone images using o3")
    parser.add_argument("image_path", help="Path to the drone image")
    parser.add_argument("--id", help="Optional image identifier")
    args = parser.parse_args()
    
    analyzer = LLMContextualAnalyzer()
    result = analyzer.process_image(args.image_path, args.id)
    
    if result:
        print(json.dumps(result, indent=2))
    else:
        print("Analysis failed. Check logs for details.") 