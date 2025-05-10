# OSM Search: Processing Search Areas and Executing Overpass QL Queries

This document provides a comprehensive guide on how to use the OSM Search functionality in this project, including both standalone usage and integration with the contextual analyzer.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
  - [Command-Line Interface](#command-line-interface)
  - [Programmatic Usage](#programmatic-usage)
- [Integration with Contextual Analyzer](#integration-with-contextual-analyzer)
- [Running the Complete Pipeline](#running-the-complete-pipeline)
- [Understanding Polygon Strings](#understanding-polygon-strings)
- [Advanced Configuration](#advanced-configuration)
- [Troubleshooting](#troubleshooting)

## Overview

The OSM Search module provides functionality to:

1. Load search area coordinates from GeoJSON files
2. Convert coordinates into Overpass QL polygon format
3. Substitute polygon strings into Overpass QL queries
4. Execute queries against the Overpass API
5. Convert results back to GeoJSON

This enables you to identify and retrieve OpenStreetMap features within specific geographic boundaries.

## Installation

The OSM Search module requires the following dependencies:

```bash
pip install overpy geojson
```

You may need additional dependencies for the contextual analyzer integration:

```bash
pip install python-dotenv requests
```

## Basic Usage

### Command-Line Interface

The simplest way to use the OSM Search module is through the command-line interface:

```bash
# From the root directory of the project
python src/components/osm_search/osm_search.py --search-area "path/to/search_area.json" --output-geojson "path/to/results.geojson"
```

Common options:

- `--search-area`: Path to the GeoJSON file containing search area coordinates
- `--query-template`: Path to a JSON file containing the Overpass QL query template
- `--output-query`: Path to save the final query
- `--output-geojson`: Path to save the GeoJSON results
- `--feature-index`: Index of the feature to use from the GeoJSON FeatureCollection (default: 0)
- `--direct-query`: Path to a file containing a direct Overpass QL query to execute

### Programmatic Usage

To use the OSM Search module programmatically:

```python
from components.osm_search.osm_search import OSMSearchProcessor

# Initialize the processor
processor = OSMSearchProcessor(
    search_area_path="path/to/search_area.json",
    query_template_path="path/to/query_template.json"
)

# Process a search area and execute a query
poly_string = processor.process_search_area_from_file()
query_template = processor.load_query_template_from_file()
final_query = processor.substitute_poly_string(query_template, poly_string)
result, geojson_data = processor.execute_query(final_query)

# Or use the convenience method
final_query, result, geojson_data = processor.process_query()

# Save the results
processor.save_query_to_file(final_query, "path/to/final_query.txt")
processor.save_geojson_to_file(geojson_data, "path/to/results.geojson")
```

## Integration with Contextual Analyzer

The OSM Search module can be integrated with the contextual analyzer to generate Overpass QL queries based on drone images:

```python
from components.llm_analysis.contextual_analyzer import LLMContextualAnalyzer
from components.osm_search.osm_search import OSMSearchProcessor

# Initialize the processors
analyzer = LLMContextualAnalyzer()
osm_processor = OSMSearchProcessor()

# Generate a query from an image
result = analyzer.process_image(
    "path/to/image.jpg",
    direct_overpass=True
)

# Process the query with the search area
if "overpass_query" in result:
    final_query, overpy_result, geojson_data = osm_processor.process_query(
        query=result["overpass_query"],
        search_area_file="path/to/search_area.json"
    )
```

## Running the Complete Pipeline

For convenience, a test script is provided to run the complete pipeline:

```bash
# From the root directory of the project
python tests/test_osm_pipeline.py --location "Reading_1"
```

Or to process all available locations:

```bash
python tests/test_osm_pipeline.py --all
```

Available options:

- `--location`: Base name of the location to process (e.g., "Reading_1")
- `--all`: Process all locations in the Competition Release folder
- `--feature-index`: Index of the feature to use from GeoJSON FeatureCollection (default: 0)
- `--output-dir`: Directory to store output files
- `--list-locations`: List all available locations

## Understanding Polygon Strings

Overpass QL uses a specific format for polygon filters. The OSM Search module converts GeoJSON coordinates to this format.

GeoJSON coordinates are in the format `[longitude, latitude]`, while Overpass QL requires `latitude longitude` pairs separated by spaces.

Example GeoJSON:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [-0.4269, 51.6206],
            [-0.4269, 51.6826],
            [-0.5335, 51.6826],
            [-0.5335, 51.6206],
            [-0.4269, 51.6206]
          ]
        ]
      }
    }
  ]
}
```

Converted to Overpass QL polygon string:

```
51.6206 -0.4269 51.6826 -0.4269 51.6826 -0.5335 51.6206 -0.5335 51.6206 -0.4269
```

This string replaces the `{poly_string}` placeholder in the query template:

```
way["highway"="residential"](poly:"{poly_string}");
```

## Advanced Configuration

### Environment Variables

- `OSM_SEARCH_AREA_PATH`: Default path to the search area GeoJSON file

### Custom Query Templates

You can create custom query templates by including a `{poly_string}` placeholder:

```json
{
  "query": "[out:json][timeout:60];\nway[\"highway\"=\"residential\"](poly:\"{poly_string}\")->.roads;\n.roads out body geom;"
}
```

## Troubleshooting

### Common Issues

1. **{poly_string} not being replaced**: Make sure the query template contains the exact placeholder `{poly_string}` and that the search area file exists and can be parsed.

2. **429 Too Many Requests**: The Overpass API has rate limits. If you encounter this error, wait a few minutes before trying again.

3. **Invalid polygon**: Ensure your search area coordinates form a valid polygon. Check the GeoJSON structure.

4. **Search area file not found**: Verify the file path is correct, or set the `OSM_SEARCH_AREA_PATH` environment variable.

If you need to debug an issue, check the logs which contain detailed information about each step of the process. 