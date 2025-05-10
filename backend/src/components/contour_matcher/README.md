# Contour Matcher Component

This component provides tools for matching contours between drone and satellite images. It includes both individual contour matching and holistic contour matching approaches.

## Approaches

### 1. Individual Contour Matching (`basic_test.py`)

The individual approach compares each drone contour against each satellite contour to find the best match for each drone contour based on the Intersection over Union (IoU) similarity metric.

- **Pros**: Fast, works well for identifiable individual features
- **Cons**: Doesn't consider spatial relationships between contours, may miss the overall pattern

### 2. Holistic Contour Matching (`holistic_matcher.py`)

The holistic approach treats all contours as a single pattern, creating composite images with all contours from both drone and satellite images. It then finds the optimal transformation (scale, rotation, translation) to align the entire pattern.

- **Pros**: Considers spatial relationships between contours, better for overall image alignment
- **Cons**: More computationally intensive, requires optimizing multiple transformation parameters

## Usage

### Individual Matching

```bash
python basic_test.py --input-json path/to/contours.json --output-dir output_folder
```

Options:
- `--min-score 0.2`: Minimum IoU score (0-1) to consider a match
- `--num-visualizations 5`: Number of match visualizations to generate
- `--debug`: Enable detailed debugging output

### Holistic Matching

For full control:
```bash
python holistic_matcher.py --input-json path/to/contours.json --output-dir output_folder
```

Options:
- `--min-score 0.15`: Minimum similarity score (0-1)
- `--min-scale 0.5`: Minimum scale factor to try
- `--max-scale 2.0`: Maximum scale factor to try
