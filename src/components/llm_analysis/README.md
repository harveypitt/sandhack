# LLM Contextual Analysis Agent

This component uses OpenAI's GPT-4o vision model to analyze drone images and GPT-3.5 Turbo to generate structured descriptions of scenes, focusing on landmarks and features that can aid in relocalization.

## Setup

1. Make sure you have Python 3.12+ installed.

2. Create a `.env` file in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

```python
from contextual_analyzer import LLMContextualAnalyzer

# Initialize the analyzer
analyzer = LLMContextualAnalyzer()

# Process an image
result = analyzer.process_image("path/to/drone_image.jpg")

if result:
    print(result)
```

### From Command Line

```bash
# Use the analyzer from the command line
python contextual_analyzer.py path/to/drone_image.jpg --id optional_image_id

# Run the test script with the example image
python test_analyzer.py
```

## Component Structure

- `contextual_analyzer.py`: Main implementation of the LLM Contextual Analysis Agent
- `test_analyzer.py`: Test script for the example image
- `requirements.txt`: Required Python packages
- `README.md`: This documentation file

## Model Usage

The component uses two different OpenAI models for efficiency:
- **GPT-4o** (`gpt-4o`): For vision/image analysis
- **GPT-3.5 Turbo** (`gpt-3.5-turbo`): For structuring the text output into JSON

This approach provides high quality image analysis while keeping costs lower for the text processing phase.

## Expected Output

The component returns a JSON object with:
- `image_id`: Identifier for the image (filename by default)
- `description`: Concise description of the scene
- `keywords`: List of landmarks/features identified in the image

Example:
```json
{
  "image_id": "rickmansworth_example",
  "description": "Suburban street next to a park with semi-detached houses and UK road markings.",
  "keywords": ["park", "suburban street", "semi-detached houses", "UK road markings"]
}
```

## Error Handling

- The component includes robust error handling for API failures, timeout issues, and parsing errors.
- All errors are logged for debugging purposes.
- The test script includes connectivity checks to help diagnose network issues.

## Next Steps

- [ ] Fine-tune prompts for higher accuracy
- [ ] Implement caching of results to avoid redundant API calls
- [ ] Add test case coverage
- [ ] Improve keyword extraction precision

## Hackathon Considerations

This implementation is optimized for the UK Defence Hackathon, with a focus on:
- British urban/suburban settings
- Speed and accuracy over cost optimization
- Reliability during demos 