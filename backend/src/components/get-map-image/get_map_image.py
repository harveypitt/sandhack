# Purpose: Download one satellite PNG per point in a GeoJSON file,
# sized to roughly match a 120-m-altitude drone shot.
import math, urllib.parse, requests, json, pathlib

API_KEY = "AIzaSyCQGFKY2w5DZMzxDAmMNrXRBFHRQqbijI8"
OUTPUT_DIR = pathlib.Path(__file__).parent / "drone_like_imgs"
OUTPUT_DIR.mkdir(exist_ok=True)


def static_map_url(lat, lon, width_m=250, pix=640, scale=2):
    m_per_pix = width_m / (pix * scale)
    zoom = round(math.log2(math.cos(math.radians(lat))*156543.03392 / m_per_pix))
    zoom = max(0, min(21, zoom))                      # clamp
    params = dict(center=f"{lat},{lon}",
                  zoom=zoom,
                  size=f"{pix}x{pix}",
                  scale=scale,
                  maptype="satellite",
                  key=API_KEY)
    return "https://maps.googleapis.com/maps/api/staticmap?" + urllib.parse.urlencode(params)

# Only run this code if the script is executed directly, not when imported
if __name__ == "__main__":
    # loop through your GeoJSON
    # Load the entire GeoJSON structure
    geoj = json.load(open(pathlib.Path(__file__).parent / "points.geojson"))
    for i, feat in enumerate(geoj["features"], 1):
        lon, lat = feat["geometry"]["coordinates"]
        url = static_map_url(lat, lon)
        img = requests.get(url)
        img.raise_for_status() # Check for request errors
        # Save the image to the output directory
        (OUTPUT_DIR / f"point_{i}.png").write_bytes(img.content)
        print(f"saved point_{i}.png") # Print confirmation 