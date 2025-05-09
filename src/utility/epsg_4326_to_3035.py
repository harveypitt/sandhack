import json
from src.utility.bounding_box  import BoundingBox, Projection
from shapely.geometry import shape
from pyproj import Transformer



def geojson_to_3035_bboxes(filepath: str) -> list[BoundingBox]:
    # Load GeoJSON file
    with open(filepath, 'r') as f:
        data = json.load(f)

    transformer = Transformer.from_crs(Projection.EPSG_4326._value_, Projection.EPSG_3035._value_, always_xy=True)

    bboxes_3035: list[BoundingBox] = []

    for feature in data['features']:
        geom = shape(feature['geometry'])

        # Get bounding box in EPSG:4326
        min_lon, min_lat, max_lon, max_lat = geom.bounds

        # Transform to EPSG:3035
        min_lon_3035, min_lat_3035 = transformer.transform(min_lon, min_lat)
        max_lon_3035, max_lat_3035 = transformer.transform(max_lon, max_lat)

        bbox = BoundingBox(
            min_lat=min_lat_3035,
            max_lat=max_lat_3035,
            min_lon=min_lon_3035,
            max_lon=max_lon_3035,
            projection=Projection.EPSG_3035
        )
        bboxes_3035.append(bbox)

    return bboxes_3035

if __name__ == "__main__":
    path_to_geojson = "data/example/images/rickmansworth_example_search_area.json"  # Replace with your actual path
    bboxes = geojson_to_3035_bboxes(path_to_geojson)
    for i, bbox in enumerate(bboxes):
        print(f"Feature {i+1} BBOX (EPSG:3035): {bbox}")
        print(f"{bbox.to_query_string()}")
