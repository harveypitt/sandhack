# LLM Contextual Analyzer - Usage Guide

This guide explains how to use the LLM Contextual Analyzer to process drone images and generate structured descriptions, features, and location estimates.

## Prerequisites

- Python 3.8+
- OpenAI API key set in the environment (`OPENAI_API_KEY`)
- Required libraries:
  ```bash
  python3 -m pip install requests python-dotenv tabulate
  ```

## Basic Usage

### Analyzing a Single Image

To analyze a single drone image:

```bash
python3 src/components/llm_analysis/contextual_analyzer.py path/to/image.jpg
```

For a more detailed output with timing information:

```bash
python3 test_single_image.py path/to/image.jpg
```

### Output Format

The analyzer returns a JSON object with:
- `description`: A concise scene description
- `features`: List of visual features/landmarks
- `estimated-location`: Best guess of the location
- `confidence`: Confidence level (0-100)
- `image_id`: Identifier (filename by default)
- `usage`: Token usage statistics

## UK vs. Global Mode

The analyzer supports two modes:

### UK Mode (Default)

Optimized for UK locations like Reading or Rickmansworth.

```bash
python3 test_single_image.py path/to/image.jpg
```

### Global Mode

For analyzing images from anywhere in the world with precise location identification:

```bash
python3 test_single_image.py path/to/image.jpg --global-mode
```

Example: The Shahristan image is identified in global mode as "Shahristan, Daykundi Province, Afghanistan" with higher confidence versus the UK mode which incorrectly guesses "Upper Teesdale, County Durham, UK" with only 15% confidence.

The global mode has been enhanced to provide:
1. Town/settlement level precision where possible
2. Standardized location format: "[Town/District], [Province/Region], [Country]"
3. More accurate confidence scores based on architectural and geographical features

## Batch Testing

To analyze multiple images at once:

```bash
python3 batch_test_analyzer.py
```

### Batch Options

```bash
# Process images in a specific directory
python3 batch_test_analyzer.py --dir path/to/images

# Process global images
python3 batch_test_analyzer.py --global-mode

# Specify output file
python3 batch_test_analyzer.py --output results.json
```

## Advanced Options

### Setting Logging Level

```bash
LOG_LEVEL=DEBUG python3 test_single_image.py path/to/image.jpg
```

Available levels: DEBUG, INFO, WARNING, ERROR

### Output Files

- `analysis_result.json`: Results from single image test
- `batch_results.json`: Results from batch testing
- `batch_test_results.log`: Detailed log of batch processing
- `contextual_analyzer.log`: General analyzer log

## Example Test Cases

### UK Location Tests
```bash
python3 test_single_image.py "Competition Release/Reading_1_cleaned.jpg"
python3 test_single_image.py "Competition Release/Rickmansworth_2_cleaned.jpg"
```

### Global Location Tests
```bash
python3 test_single_image.py "Competition Release/Sharharistan.jpg" --global-mode
```

The Afghanistan example shows the importance of using global mode for non-UK locations. When using global mode, the analyzer attempts to identify not just the country but the specific town and region (the actual location is Shahristan, Daykundi Province, Afghanistan).

## Batch Evaluation

To evaluate how well the analyzer performs across a set of images:

```bash
python3 batch_test_analyzer.py --dir "Competition Release"
```

This generates a summary showing:
- Success rate of analyses
- Match rate for locations
- Processing time per image
- Detailed table of results

## Help Commands

For more information on command options:

```bash
python3 test_single_image.py --help
python3 batch_test_analyzer.py --help
``` 