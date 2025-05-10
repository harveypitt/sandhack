#!/usr/bin/env python3
"""
FastAPI Backend for Location Estimation Service

This module provides API endpoints to process images and return location estimations.
"""

import os
import json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import Optional

from src.components.llm_analysis.contextual_analyzer import LLMContextualAnalyzer

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

# Create router with tag
llm_router = APIRouter(prefix="/llm-analysis", tags=["LLM_Analysis"])

# Initialize analyzer
analyzer = LLMContextualAnalyzer(global_mode=False)

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

# Include the router - make sure this is called!
app.include_router(llm_router)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 