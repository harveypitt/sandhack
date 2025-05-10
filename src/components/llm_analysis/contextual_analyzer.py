#!/usr/bin/env python3
"""
LLM Contextual Analysis Agent

This module uses OpenAI's GPT-4o model to analyze drone images and generate structured
descriptions of the scenes, focusing on landmarks and features that can aid in relocalization.

Logs are emitted both to stdout and to a file named `contextual_analyzer.log` (see LOG_LEVEL env var).
"""

import os
import json
import base64
import logging
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv
import requests
from requests.exceptions import RequestException, Timeout

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('contextual_analyzer.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("OpenAI API key not found in environment variables. Set OPENAI_API_KEY in .env file.")

# Constants
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
VISION_MODEL = "o3"  # OpenAI's vision model for image analysis
# NOTE: Only the o3 vision-capable model is used; no secondary model required.

# Prompts from documentation
# Load prompts from a file or define them here
SCENE_ANALYSIS_PROMPT = """
You are an expert in aerial image analysis. You will receive a drone image taken somewhere in the United Kingdom along with short instructions.

Your task is to respond ONLY with a valid JSON object containing **four keys**:

  "description":  A single concise sentence that summarises the visible scene (do NOT include any place-name).
  "features":     An array of 5-12 short landmark / feature phrases (e.g. "park", "cul-de-sac", "semi-detached houses", "UK road markings"). No location names.
  "estimated-location": Your best guess of the town or locality where the image was taken. This should be a short free-text phrase such as "Rickmansworth, Hertfordshire, UK". If uncertain, still provide the most likely answer – do NOT leave this blank.
  "confidence":   An integer 0-100 representing how confident you are in the estimated-location.

Guidelines:
• The description and features MUST NOT contain any place-name.  
• The estimated-location field MUST be separate.  
• Output **only** raw JSON – no markdown fences or additional commentary.
"""


class LLMContextualAnalyzer:
    """
    Uses vision models to analyze drone images and generate structured descriptions.
    """
    
    def __init__(self):
        """Initialize the analyzer with API key and configurations."""
        self.api_key = OPENAI_API_KEY
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        # Store token usage statistics per request type
        self.usage_stats: Dict[str, Dict[str, int]] = {}
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
    
    def analyze_image(self, image_path: str, timeout: int = 300) -> Optional[Dict]:
        """
        Send the image to vision model for scene analysis.
        
        Args:
            image_path: Path to the drone image
            timeout: API request timeout in seconds (default: 5 minutes)
            
        Returns:
            Structured data dictionary (description, features, estimated-location, confidence) or None if failed
        """
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None
            
        try:
            base64_image = self.encode_image(image_path)
            
            payload = {
                "model": VISION_MODEL,
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
                                "text": "Analyse this drone image and follow the instructions to produce the required JSON object."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ]
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

            if "choices" not in response_data or not response_data["choices"]:
                logger.warning(f"Unexpected response format: {response_data}")
                return None

            # Capture usage if available
            if "usage" in response_data:
                self.usage_stats["vision"] = response_data["usage"]

            json_text = response_data["choices"][0]["message"]["content"]

            # Clean up code fences
            if "```" in json_text:
                json_text = json_text.split("```")[1]
                if json_text.startswith("json"):
                    json_text = json_text[4:]

            try:
                structured_data = json.loads(json_text.strip())
                return structured_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from vision model: {e} | Raw: {json_text}")
                return None
                
        except Timeout:
            logger.error(f"Request timed out after {timeout} seconds")
            return None
        except RequestException as e:
            # Log response details if available
            response = getattr(e, 'response', None)
            if response is not None:
                logger.error(
                    "API request failed: %s | Status: %s | Response: %s",
                    e,
                    response.status_code,
                    response.text
                )
            else:
                logger.error(f"API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in image analysis: {e}")
            return None
    
    def process_image(self, image_path: str, image_id: str = None) -> Optional[Dict]:
        """
        Full pipeline: analyze image and structure the output.
        
        Args:
            image_path: Path to the drone image
            image_id: Optional identifier for the image
            
        Returns:
            Structured JSON with image_id, description, and features
        """
        # Use filename as image_id if not provided
        if image_id is None:
            image_id = Path(image_path).stem
        
        # Reset usage statistics for this run
        self.usage_stats = {}

        # Step 1: Analyze image and receive structured data directly
        structured_data = self.analyze_image(image_path)
        if not structured_data:
            logger.error(f"Failed to analyze image: {image_path}")
            return None

        logger.info(f"Structured data from vision model: {structured_data}")

        # Step 2: Add image_id and token usage
        structured_data["image_id"] = image_id
        if self.usage_stats:
            structured_data["usage"] = self.usage_stats

        return structured_data


# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze drone images using the o3 vision model")
    parser.add_argument("image_path", help="Path to the drone image")
    parser.add_argument("--id", help="Optional image identifier")
    args = parser.parse_args()
    
    analyzer = LLMContextualAnalyzer()
    result = analyzer.process_image(args.image_path, args.id)
    
    if result:
        print(json.dumps(result, indent=2))
    else:
        print("Analysis failed. Check logs for details.") 