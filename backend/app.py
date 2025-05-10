#!/usr/bin/env python3
"""
FastAPI Backend for Location Estimation Service

This module provides API endpoints to process images and return location estimations.
"""

import os
import json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
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

# Initialize analyzer
analyzer = LLMContextualAnalyzer(global_mode=False)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Location Estimation API is running"}

@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...), global_mode: Optional[bool] = False):
    """
    Analyze an uploaded image and return location estimation
    
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
            f.write(await file.read())
        
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

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 