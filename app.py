import json
import pandas as pd
from shapely.geometry import shape

# تحميل GeoJSON
with open("network.geojson") as f:
    data = json.load(f)

rows = []

for i, feature in enumerate(data["features"]):
    geom = shape(feature["geometry"])
    props = feature["properties"]

    rows.append({
        "id": i,
        "type": props.get("type"),
        "length": geom.length,
        "geometry": feature["geometry"]
    })

df = pd.DataFrame(rows)
