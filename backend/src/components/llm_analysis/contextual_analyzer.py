#!/usr/bin/env python3
"""
LLM Contextual Analysis Agent

This module uses OpenAI's GPT-4o model to analyze drone images and generate structured
descriptions of the scenes, focusing on landmarks and features that can aid in relocalization.
It can also generate Overpass QL queries for OpenStreetMap based on the image analysis.

Logs are emitted both to stdout and to a file named `contextual_analyzer.log` (see LOG_LEVEL env var).
"""

import os
import json
import base64
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
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

# Direct Overpass QL generation from image prompt
DIRECT_OVERPASS_PROMPT = """
You are an expert in aerial image analysis and Overpass QL generation.

Analyze this drone image and generate an Overpass QL query to find OpenStreetMap features visible in the image.

1. First identify the key visible features like:
   - Road types (residential, primary, footway)
   - Buildings (houses, shops, schools)
   - Natural features (parks, water bodies, forests)
   - Landmarks and amenities

2. Then create an Overpass QL query with the following structure:
   [out:json][timeout:60];
   
   /* 1) First feature type */
   way["key"="value"](poly:"{poly_string}")->.set1;
   
   /* 2) Second feature type */
   way["key"~"^(value1|value2)$"](poly:"{poly_string}")->.set2;
   
   /* Add more feature queries as needed */
   
   /* Return full geometry */
   out body geom;

Guidelines:
- Include at least 3-5 distinct feature queries
- Prioritize the most distinctive and visible elements in the image
- Use descriptive comments to explain each query section
- Use set operations where appropriate (e.g., node(w.roads)(w.paths) for intersections)

Return ONLY the Overpass QL query, no explanation or other text.
"""

# For backward compatibility, keep original prompt name pointing to UK version
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
    
    def __init__(self, global_mode=False):
        """
        Initialize the analyzer with API key and configurations.
        
        Args:
            global_mode: When True, uses the global analysis prompt 
                         rather than the UK-specific one (default: False)
        """
        self.api_key = OPENAI_API_KEY
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        # Store token usage statistics per request type
        self.usage_stats: Dict[str, Dict[str, int]] = {}
        # Set the prompt based on the mode
        self.global_mode = global_mode
        mode_str = "global" if global_mode else "UK-specific"
        logger.info(f"LLM Contextual Analyzer initialized in {mode_str} mode")
    
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
    
    def direct_overpass_query(self, image_path: str, poly_string: str = "{poly_string}", timeout: int = 300) -> Optional[str]:
        """
        Generate an Overpass QL query directly from an image in a single request.
        
        Args:
            image_path: Path to the drone image
            poly_string: The polygon string for the Overpass QL query, default is a placeholder
            timeout: API request timeout in seconds (default: 5 minutes)
            
        Returns:
            Overpass QL query string or None if failed
        """
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None
        
        try:
            base64_image = self.encode_image(image_path)
            
            # Replace placeholder in the prompt
            prompt = DIRECT_OVERPASS_PROMPT.replace("{poly_string}", poly_string)
            
            payload = {
                "model": VISION_MODEL,
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are an expert in OSINT Analyst with expertise in aerial image analysis and Overpass QL generation."
                                   "You are given a drone image and a prompt to generate an Overpass QL query to find OpenStreetMap features visible in the image."
                                   "You must generate a valid Overpass QL query that can be used to find the features in the image."
                                   "You focus on the unique features visible in the image that uniquely identify the location."
                                   "The query should return the nodes that help to identfiy the location."
                                   "At the end of your Overpass QL, include a numbered “intersection” step that returns only the nodes belonging to the sets so you identify a few key locations only."
                                   "Do not return more than 10 nodes."
                                   "include a {poly_string} placeholderin the query to ensure the query is constrained to the correct area."
                                   "At the end of the script, include exactly one “intersection” step that returns only the nodes belonging to both your two chosen sets, then immediately terminate with out body geom;"
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
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
            
            logger.info(f"Sending direct Overpass QL generation request for: {Path(image_path).name}")
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
                self.usage_stats["direct_overpass"] = response_data["usage"]

            overpass_query = response_data["choices"][0]["message"]["content"]

            # Clean up code fences if present
            if "```" in overpass_query:
                blocks = overpass_query.split("```")
                for block in blocks:
                    if block.strip() and not block.strip().startswith("overpass"):
                        overpass_query = block.strip()
                        break
                    elif block.strip().startswith("overpass"):
                        overpass_query = block.replace("overpass", "", 1).strip()
                        break

            return overpass_query.strip()
                
        except Exception as e:
            logger.error(f"Error generating direct Overpass QL query: {e}")
            return None
    
    def process_image(self, image_path: str, image_id: str = None, generate_overpass: bool = False, 
                      poly_string: str = "{poly_string}", overpass_output_file: str = None,
                      direct_overpass: bool = False) -> Optional[Dict]:
        """
        Full pipeline: analyze image and structure the output.
        
        Args:
            image_path: Path to the drone image
            image_id: Optional identifier for the image
            generate_overpass: Whether to generate an Overpass QL query
            poly_string: The polygon string for the Overpass QL query
            overpass_output_file: Path to write the Overpass QL query to as JSON
            direct_overpass: Whether to generate the Overpass QL query directly (single request)
            
        Returns:
            Structured JSON with image_id, description, features, and optionally an Overpass QL query
        """
        # Use filename as image_id if not provided
        if image_id is None:
            image_id = Path(image_path).stem
        
        # Reset usage statistics for this run
        self.usage_stats = {}

        result = {}
        
        # If direct Overpass query is requested, skip the analysis step
        if direct_overpass:
            overpass_query = self.direct_overpass_query(image_path, poly_string)
            if overpass_query:
                result = {
                    "image_id": image_id,
                    "overpass_query": overpass_query
                }
                logger.info("Direct Overpass QL query generated successfully")
                
                # Write to output file if specified
                if overpass_output_file:
                    try:
                        os.makedirs(os.path.dirname(overpass_output_file), exist_ok=True)
                        with open(overpass_output_file, 'w') as f:
                            json.dump({"query": overpass_query}, f, indent=2)
                        logger.info(f"Overpass QL query written to {overpass_output_file}")
                    except Exception as e:
                        logger.error(f"Error writing Overpass QL query to file: {e}")
                
                if self.usage_stats:
                    result["usage"] = self.usage_stats
                
                return result
            else:
                logger.error("Failed to generate direct Overpass QL query")
                return None
        
        # Step 1: Analyze image and receive structured data
        structured_data = self.analyze_image(image_path)
        if not structured_data:
            logger.error(f"Failed to analyze image: {image_path}")
            return None

        logger.info(f"Structured data from vision model: {structured_data}")

        # Step 2: Add image_id and token usage
        structured_data["image_id"] = image_id
        if self.usage_stats:
            structured_data["usage"] = self.usage_stats

        # Step 3: Generate Overpass QL query if requested
        if generate_overpass:
            # Use direct method for a second call
            overpass_query = self.direct_overpass_query(image_path, poly_string)
            if overpass_query:
                structured_data["overpass_query"] = overpass_query
                logger.info("Overpass QL query generated successfully")
                
                # Write to output file if specified
                if overpass_output_file:
                    try:
                        os.makedirs(os.path.dirname(overpass_output_file), exist_ok=True)
                        with open(overpass_output_file, 'w') as f:
                            json.dump({"query": overpass_query}, f, indent=2)
                        logger.info(f"Overpass QL query written to {overpass_output_file}")
                    except Exception as e:
                        logger.error(f"Error writing Overpass QL query to file: {e}")
            else:
                logger.warning("Failed to generate Overpass QL query")

        return structured_data


# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze drone images using the o3 vision model")
    parser.add_argument("image_path", help="Path to the drone image")
    parser.add_argument("--id", help="Optional image identifier")
    parser.add_argument("--global-mode", action="store_true", help="Use global analysis prompt")
    parser.add_argument("--generate-overpass", action="store_true", help="Generate an Overpass QL query")
    parser.add_argument("--direct-overpass", action="store_true", help="Generate only the Overpass QL query directly in one step")
    parser.add_argument("--poly-string", default="{poly_string}", help="Polygon string for Overpass QL query, default is a placeholder")
    parser.add_argument("--overpass-output", 
                        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "osm_search", "osm_search.json"), 
                        help="Path to write the Overpass QL query to as JSON")
    args = parser.parse_args()
    
    # Ensure the output directory exists
    if args.overpass_output:
        os.makedirs(os.path.dirname(args.overpass_output), exist_ok=True)
    
    analyzer = LLMContextualAnalyzer(args.global_mode)
    
    # Default to direct Overpass query generation
    direct_overpass = args.direct_overpass or not args.generate_overpass
    
    result = analyzer.process_image(
        args.image_path, 
        args.id, 
        not direct_overpass,  # Only do regular analysis if direct_overpass is False
        args.poly_string,
        args.overpass_output,
        direct_overpass
    )
    
    if result:
        print(json.dumps(result, indent=2))
    else:
        print("Analysis failed. Check logs for details.") 