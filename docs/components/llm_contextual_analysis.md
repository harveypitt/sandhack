# LLM Contextual Analysis Agent

## Overview
This component analyzes consistent-format drone images (primarily urban settings) to generate textual scene descriptions, focusing on identifying landmarks and features for relocalization. The implementation uses OpenAI's GPT-4o vision model for image analysis, with GPT-3.5 Turbo for structuring the output into a JSON schema.

## Setup
1. API Key Setup
   - Store the OpenAI API key in a `.env` file at the project root:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
   - The code will load this key using the `dotenv` package

## Feature Checklist

### Core Functionality
- [x] LLM Integration (GPT-4o)
  - [x] Set up API client for GPT-4o
  - [x] Implement image encoding (base64 or direct upload)
  - [x] Design and test prompt for urban/parkland context
  - [x] Implement response retrieval

- [x] Output Structuring (GPT-3.5 Turbo)
  - [x] Use a more cost-effective model to convert freeform output into a structured JSON schema:
    - [x] Extract location description
    - [x] Extract and categorize landmarks
    - [x] Extract confidence or certainty if available
    - [x] Output: `{ "image_id": ..., "description": ..., "keywords": [...] }`

- [x] Error Handling
  - [x] Handle API errors and timeouts
  - [x] Handle empty or ambiguous responses
  - [x] Network connectivity checks

### Urban Context Optimization
- [x] Tune prompt for urban/suburban features (e.g., parks, cul-de-sacs, road markings)
- [ ] Validate output relevance for urban settings

### Testing & Validation
- [x] Unit Tests
  - [x] API integration tests
  - [x] Response parsing/structuring tests
  - [x] Error handling tests

- [ ] Integration Tests
  - [x] End-to-end workflow tests with example images
  - [ ] Output schema validation

- [ ] Validation Metrics
  - [ ] Accuracy of landmark identification
  - [ ] Response time measurements
  - [ ] Error rate monitoring

### Documentation
- [x] API Documentation
  - [x] Input/output specifications
  - [x] Error codes and handling

- [x] Usage Examples
  - [x] Basic implementation
  - [x] Example prompt/response
  - [x] Error handling examples

## Implementation Notes

### Priority Order
1. ✅ GPT-4o integration and prompt design
2. ✅ Output structuring (JSON schema) with GPT-3.5 Turbo
3. ✅ Testing and validation
4. ✅ Documentation

### Key Considerations
- Images are consistent in format and quality; no normalization needed
- Focus on urban/suburban context
- Prioritize speed and accuracy for hackathon use
- Robust error handling for demo reliability
- Cost efficiency by using GPT-3.5 Turbo for text structuring

### Dependencies
- Python 3.12+
- OpenAI API client
- python-dotenv for environment variables
- Testing frameworks
- Logging utilities

## Progress Tracking
- [x] Phase 1: Basic Implementation
- [x] Phase 2: Testing & Validation
- [x] Phase 3: Documentation
- [ ] Phase 4: Integration & Demo 