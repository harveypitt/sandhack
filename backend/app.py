#!/usr/bin/env python3
"""
FastAPI Backend for Location Estimation Service

This module provides API endpoints to process images and return location estimations.
"""

import os
import json
from pathlib import Path
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import Optional, List
import base64

from src.components.llm_analysis.contextual_analyzer import LLMContextualAnalyzer
# Import contour components
from src.components.contour_extractor.contour_extractor import ContourExtractor
from src.components.contour_matcher.contour_matcher import ContourMatcher
# Import drone image matcher components
from src.components.drone_image_matcher.drone_image_matcher import DroneImageMatcher

# Initialize the app
app = FastAPI(title="Location Estimation API",
              description="API for estimating locations from images using computer vision and LLM analysis")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Create routers with tags
llm_router = APIRouter(prefix="/llm-analysis", tags=["LLM_Analysis"])
contour_extractor_router = APIRouter(prefix="/contour", tags=["Contour_Extractor"])
contour_matcher_router = APIRouter(prefix="/contour", tags=["Contour_Matcher"])
drone_matcher_router = APIRouter(prefix="/drone-matcher", tags=["Drone_Image_Matcher"])

# Initialize components
analyzer = LLMContextualAnalyzer(global_mode=False)
contour_extractor = ContourExtractor()
contour_matcher = ContourMatcher()

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Location Estimation API is running"}

# Debug endpoint to check the router
@app.get("/llm-analysis", tags=["Debug"])
async def debug_llm_route():
    """Debug endpoint to check llm-analysis route"""
    return {"status": "ok", "message": "LLM Analysis router is available"}

@llm_router.post("/analyze")
async def analyze_image(file: UploadFile = File(..., description="Image file to analyze (max 20MB)"), global_mode: Optional[bool] = False):
    """
    Analyze an uploaded image and return location estimation using LLM analysis
    
    Args:
        file: The image file to analyze
        global_mode: Whether to use global analysis mode (default: False for UK-specific)
    
    Returns:
        JSON response with analysis results
    """
    # Check if the file is an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save the uploaded file temporarily
    temp_file = Path(f"/tmp/{file.filename}")
    try:
        with open(temp_file, "wb") as f:
            # Read in chunks to handle large files
            content = await file.read(1024 * 1024)
            while content:
                f.write(content)
                content = await file.read(1024 * 1024)
        
        # Process the image
        result = analyzer.process_image(str(temp_file))
        
        if not result:
            raise HTTPException(status_code=500, detail="Analysis failed")
        
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up the temporary file
        if temp_file.exists():
            temp_file.unlink()

# Keep the old endpoint for backward compatibility
@app.post("/analyze", tags=["LLM_Analysis"], deprecated=True)
async def analyze_image_legacy(file: UploadFile = File(..., description="Image file to analyze (max 20MB)"), global_mode: Optional[bool] = False):
    """
    Legacy endpoint - use /llm-analysis/analyze instead
    """
    return await analyze_image(file, global_mode)

# Contour Extractor Endpoints
@contour_extractor_router.post("/extract")
async def extract_contours(
    file: UploadFile = File(..., description="Image file to extract contours from (max 20MB)"),
    threshold: int = Form(50, description="Contour detection threshold (0-100)")
):
    """
    Extract contours from an uploaded image
    
    Args:
        file: The image file to extract contours from
        threshold: Detection threshold value (0-100). Lower values detect fewer but stronger contours.
    
    Returns:
        JSON response with extracted contours and visualization
    """
    # Check if the file is an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Validate threshold
    if threshold < 0 or threshold > 100:
        raise HTTPException(status_code=400, detail="Threshold must be between 0 and 100")
    
    # Save the uploaded file temporarily
    temp_file = Path(f"/tmp/{file.filename}")
    try:
        with open(temp_file, "wb") as f:
            # Read in chunks to handle large files
            content = await file.read(1024 * 1024)
            while content:
                f.write(content)
                content = await file.read(1024 * 1024)
        
        # Process the image with the specified threshold
        result = contour_extractor.extract_contours(str(temp_file), threshold)
        
        if not result:
            raise HTTPException(status_code=500, detail="Contour extraction failed")
        
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up the temporary file
        if temp_file.exists():
            temp_file.unlink()

# Contour Matcher Endpoints
@contour_matcher_router.post("/match")
async def match_contours(
    drone_image: UploadFile = File(..., description="Drone image to match (max 100MB)"),
    satellite_images: List[UploadFile] = File(..., description="Satellite images to match against (max 4 images, 100MB total)"),
    threshold: int = Form(50, description="Contour detection threshold (0-100)")
):
    """
    Match contours between a drone image and satellite images
    
    Args:
        drone_image: The drone image file
        satellite_images: List of satellite image files to match against (up to 4)
        threshold: Detection threshold value (0-100). Lower values detect fewer but stronger contours.
    
    Returns:
        JSON response with matching results and visualization
    """
    # Check if files are images
    if not drone_image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Drone file must be an image")
    
    # Check satellite images count
    if len(satellite_images) > 4:
        raise HTTPException(status_code=400, detail="Maximum 4 satellite images allowed")
    
    for img in satellite_images:
        if not img.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="All satellite files must be images")
    
    # Validate threshold
    if threshold < 0 or threshold > 100:
        raise HTTPException(status_code=400, detail="Threshold must be between 0 and 100")
    
    try:
        # Save drone image temporarily
        drone_temp_file = Path(f"/tmp/{drone_image.filename}")
        with open(drone_temp_file, "wb") as f:
            # Read in larger chunks for big files (4MB chunks)
            content = await drone_image.read(4 * 1024 * 1024)
            while content:
                f.write(content)
                content = await drone_image.read(4 * 1024 * 1024)
        
        # Save satellite images temporarily
        satellite_temp_files = []
        for img in satellite_images:
            satellite_temp_file = Path(f"/tmp/{img.filename}")
            satellite_temp_files.append(satellite_temp_file)
            with open(satellite_temp_file, "wb") as f:
                # Read in larger chunks for big files (4MB chunks)
                content = await img.read(4 * 1024 * 1024)
                while content:
                    f.write(content)
                    content = await img.read(4 * 1024 * 1024)
        
        # Match contours with the specified threshold
        result = contour_matcher.match_contours(
            str(drone_temp_file),
            [str(f) for f in satellite_temp_files],
            threshold
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Contour matching failed")
        
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up temporary files
        if 'drone_temp_file' in locals() and drone_temp_file.exists():
            drone_temp_file.unlink()
        
        if 'satellite_temp_files' in locals():
            for f in satellite_temp_files:
                if f.exists():
                    f.unlink()

# Drone Image Matcher Endpoints
@drone_matcher_router.post("/match-location")
async def match_drone_location(
    drone_image: UploadFile = File(..., description="Drone image to match (max 100MB)"),
    coordinates_file: UploadFile = File(..., description="JSON file with coordinates to test"),
    simplify: bool = Form(True, description="Whether to use simplified holistic matching"),
    use_contour: bool = Form(False, description="Whether to use contour-based matching instead of holistic")
):
    """
    Match a drone image with satellite images from coordinates to find its location
    
    Args:
        drone_image: The drone image file to find the location of
        coordinates_file: JSON file with potential coordinates to check
        simplify: Whether to use simplified holistic matching (faster)
        use_contour: Whether to use contour matching instead of holistic matching
        
    Returns:
        JSON response with matching results including best match coordinates and score
    """
    # Check if file is an image
    if not drone_image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Drone file must be an image")
    
    # Check if coordinates file is JSON
    if not coordinates_file.content_type == "application/json":
        raise HTTPException(status_code=400, detail="Coordinates file must be JSON")
    
    try:
        # Create temporary files
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_drone:
            # Save drone image
            content = await drone_image.read()
            tmp_drone.write(content)
            drone_path = tmp_drone.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_coords:
            # Save coordinates file
            content = await coordinates_file.read()
            tmp_coords.write(content)
            coords_path = tmp_coords.name
            
            # Parse coordinates to validate
            try:
                coordinates = json.loads(content.decode('utf-8'))
                if not isinstance(coordinates, list):
                    raise HTTPException(status_code=400, detail="Coordinates must be a JSON array")
                
                # Check if coordinates have required fields
                for coord in coordinates:
                    if "lat" not in coord or "lon" not in coord:
                        raise HTTPException(status_code=400, detail="Each coordinate must have 'lat' and 'lon' fields")
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON format in coordinates file")
        
        # Create a temp directory for output files
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create the DroneImageMatcher with our parameters
            matcher = DroneImageMatcher(
                output_dir=tmp_dir,
                use_holistic=not use_contour,
                simplify=simplify
            )
            
            # Find the best match
            result = matcher.find_best_match(drone_path, coordinates)
            
            # Log detailed info for debugging
            print(f"Drone image path: {drone_path}")
            print(f"Best match coordinates: {result['best_match']['coordinates']}")
            print(f"Best match score: {result['best_match']['score']}")
            if 'satellite_image' in result['best_match']:
                print(f"Best match satellite image path: {result['best_match']['satellite_image']}")
                print(f"Satellite image exists: {os.path.exists(result['best_match']['satellite_image'])}")
            
            # Process results to make them serializable
            processed_result = {
                'drone_image': drone_image.filename,
                'best_match': {
                    'coordinates': result['best_match']['coordinates'],
                    'score': float(result['best_match']['score']),
                },
                'all_matches': []
            }
            
            # Add satellite image if available
            if 'satellite_image' in result['best_match'] and os.path.exists(result['best_match']['satellite_image']):
                # Read the image file and encode as base64
                try:
                    with open(result['best_match']['satellite_image'], 'rb') as img_file:
                        img_data = img_file.read()
                        encoded_img = base64.b64encode(img_data).decode('utf-8')
                        processed_result['best_match']['satellite_image'] = encoded_img
                        print(f"Successfully encoded satellite image (length: {len(encoded_img)})")
                except Exception as e:
                    print(f"Error encoding satellite image: {str(e)}")
            else:
                print(f"Satellite image not available or path doesn't exist")
            
            # Process all matches
            for match in result['all_matches']:
                match_data = {
                    'coordinates': match['coordinates'],
                    'score': float(match['score']),
                }
                # Add satellite image if available for this match
                if 'satellite_image' in match and os.path.exists(match['satellite_image']):
                    # Only add if we haven't already added it for the best match (to save bandwidth)
                    if not (match is result['best_match'] and 'satellite_image' in processed_result['best_match']):
                        with open(match['satellite_image'], 'rb') as img_file:
                            img_data = img_file.read()
                            match_data['satellite_image'] = base64.b64encode(img_data).decode('utf-8')
                
                processed_result['all_matches'].append(match_data)
            
            return JSONResponse(content=processed_result)
    
    except Exception as e:
        import traceback
        error_detail = f"Error: {str(e)}\n\nTraceback: {traceback.format_exc()}"
        print(f"Drone matcher error: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)
    
    finally:
        # Clean up temporary files
        if 'drone_path' in locals() and os.path.exists(drone_path):
            os.unlink(drone_path)
        if 'coords_path' in locals() and os.path.exists(coords_path):
            os.unlink(coords_path)

# Include the routers
app.include_router(llm_router)
app.include_router(contour_extractor_router)
app.include_router(contour_matcher_router)
app.include_router(drone_matcher_router)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 