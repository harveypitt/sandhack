# 25-LDTH-Relocalisation
Repo for Arondite's Relocalisation with Multi-scale Feature Matching challenge.

## Problem
In a contested environment, GPS is not a reliable navigation method. There are several approaches to mitigate this; one is to use pre-
loaded satellite imagery to localise against the ground you can see.

We have provided you with a set of aerial photos taken by UAVs. Your challenge is to figure out the the WSG84 coordinates of 
the drone when each photo was taken. Given the difficulty of this challenge, we will provide WSG84 box area hints, in the format of FeatureCollections, alongside the 
images.

To achieve this, we suggest that you can try either classical or DL/ML based approaches (or both together) to match visual features 
present in the images with features visible in aerial images/photograpy; but we’d be delighted to see more creative solutions as well.
Contestants will be evaluated based on the error (distance calculated by Haversine) between the true and predicted WSG84 coordinates for a set of validation images.

## Setup
Run `uv sync`. If you don't have uv on your computer, you can find installation instructions [here](https://github.com/astral-sh/uv). We'd generally recommend using it for this project as it's lightweight and easy to manage! Feel free to add whatever libraries you need.

## Data
Under `data/example/images`, there's:
1. An example image, `rickmansworth_example.png`
1. The area in which to search for the image, `rickmansworth_example_search_area.json`, in GeoJSON FeatureCollection format

The test set of images will follow this format, a flat directory structure with `X.png` and `X_search_area.json`. 

**All drone images are taken from an altitude of between 110m and 120m**.

Arondite will make the full test set of drone images available at 10am on Saturday; further details on this will follow as a PR in this repo.

For satellite data, we've provided a helper function under `src/utility/get_satellite_image.py` which queries the [Copernicus VHR Image Mosaic](https://land.copernicus.eu/en/products/european-image-mosaic/very-high-resolution-image-mosaic-2021-true-colour-2m) using a bounding box in `EPSG:3035` format. We've also provided a helper function in `src/utility/epsg_4326_to_3035.py` that can read in a FeatureCollection bounds box in `EPSG:4326` format (i.e. the `_search_area.json` files) and convert it into the relevant format.

## Evaluating
If you take a look at `data/example`, you'll see two `.csv` files: `estimations.csv` and `truth.csv`. The output of your code should be an `estimations.csv` file with guesses in a simple `id | latitude | longitude` format, which is then compared against a `truth.csv` by ID.

We've provided a `run_eval.sh` script, which you can pass a directory to and compare the estimations and truth csvs within that directory. If you want to see our very simple comparison algorithm, take a look at `evaluate_estimations.py`; if you'd like to set up your testing and file structure differently, you can use this instead of `run_eval.sh`. To run it, you can run `uv run python evaluate_estimations.py`.

The final evaluation will be run in `data/eval` - so please don't put anything in here! - with a witheld set of validation images; the winning team will be the one with the lowest error. There's also a bonus award for the best-designed interface, if you want to spend time on that!

## Final Remarks
- Both the area to search and the evaluation coordinates are in WSG84/EPSG:4326 format
- Please use this repo to flag any issues you come across
- Arondite will also be present on-site for any questions you have
- Good luck!
