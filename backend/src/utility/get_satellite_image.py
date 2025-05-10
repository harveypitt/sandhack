import requests
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt
from src.utility.bounding_box import BoundingBox, Projection

# High res 2021 satellite imagery from Copernicus
url = "https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLand/VHR_2021_LAEA/ImageServer/exportImage"

example_bbox = BoundingBox(
    min_lat=3220365,
    max_lat=3226152,
    min_lon=3594402,
    max_lon=3602683,
    projection=Projection.EPSG_3035
)

# Bounding box is in EPSG:3035 (since it's LAEA projection)
params = {
    "bbox": example_bbox.to_query_string(),
    "bboxSR": "3035",
    "size": "512,512",
    "imageSR": "3035",
    "format": "png",  # can also be "tiff"
    "f": "image",
}

response = requests.get(url, params=params)

try:
    response.raise_for_status()
    image = Image.open(BytesIO(response.content))
    plt.imshow(image) # type: ignore
    plt.axis('off') # type: ignore
    plt.show() # type: ignore

except requests.exceptions.HTTPError as err:
    print(f"HTTP error occurred: {err}")
    print("Response content:", response.content)
    
