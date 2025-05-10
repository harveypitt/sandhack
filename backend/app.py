#!/usr/bin/env python3
"""
FastAPI Backend for Location Estimation Service

This module provides API endpoints to process images and return location estimations.
"""

import os
import json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import Optional, List

from src.components.llm_analysis.contextual_analyzer import LLMContextualAnalyzer
# Import contour components
from src.components.contour_extractor.contour_extractor import ContourExtractor
from src.components.contour_matcher.contour_matcher import ContourMatcher

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

# Include the routers
app.include_router(llm_router)
app.include_router(contour_extractor_router)
app.include_router(contour_matcher_router)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 