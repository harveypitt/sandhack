# Example Drone Images

Place your drone images in this directory for testing the drone image matcher.

## Recommended Image Characteristics

For best matching results, drone images should:

1. Be taken from approximately 120m altitude
2. Have clear visibility (minimal fog, clouds, or haze)
3. Include distinctive features like roads, buildings, rivers, or unique landscape elements
4. Be in standard image formats (JPG, PNG)
5. Have reasonable resolution (1000x1000 pixels or higher recommended)

## Testing Process

To test with your drone images:

1. Add your drone image to this directory
2. Run the matcher with the example coordinates:

```bash
python ../drone_image_matcher.py --drone-image examples/YOUR_DRONE_IMAGE.jpg --coordinates ../example_coordinates.json --output ./output
```

3. Review the results to see which location best matches your drone image

## Example Sources

Good sources for aerial/drone imagery:
- Your own drone photography 
- Public drone footage repositories
- Aerial photography collections
- Google Earth screenshots (only for testing, not for commercial use)

Remember that Google's Terms of Service restrict the use of Google Maps/Earth imagery. For testing purposes only, you could use screenshots from Google Earth at a similar altitude to a drone.

## Privacy and Legal Considerations

Ensure you have the rights to use any images you place in this directory. Do not include images of private property without permission or images that may contain personally identifiable information. 