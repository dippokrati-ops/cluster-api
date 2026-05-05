from flask import Flask, jsonify, request
import pandas as pd
import ast
import requests
import os

app = Flask(__name__)

df = pd.read_csv("output.csv")

def parse_coordinates(val, geom_type):
    try:
        coords = ast.literal_eval(val)
        if geom_type == "MultiPolygon":
            return {"type": "MultiPolygon", "coordinates": coords}
        else:
            return {"type": "Polygon", "coordinates": coords}
    except:
        return None

df["geometry_parsed"] = df.apply(lambda r: parse_coordinates(r["coordinates"], r["geometry_type"]), axis=1)

def get_label(extra_slots):
    if extra_slots <= 50:
        return "Very Low"
    elif extra_slots <= 100:
        return "Low"
    elif extra_slots <= 150:
        return "Medium"
    else:
        return "Hot"

def point_in_polygon(point, polygon):
    px, py = point
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

def find_cluster(lat, lng):
    pt = [lng, lat]
    for _, row in df.iterrows():
        geom = row["geometry_parsed"]
        if geom is None:
            continue
        try:
            if geom["type"] == "Polygon":
                if point_in_polygon(pt, geom["coordinates"][0]):
                    return row
            elif geom["type"] == "MultiPolygon":
                for poly in geom["coordinates"]:
                    if point_in_polygon(pt, poly[0]):
                        return row
        except:
            continue
    return None

def geocode_address(address):
    url = f"https://nominatim.openstreetmap.org/search"
    params = {
        "q": address + ", Greece",
        "format": "json",
        "limit": 1,
        "countrycodes": "gr"
    }
    headers = {"User-Agent": "ClusterAPI/1.0"}
    r = requests.get(url, params=params, headers=headers)
    data = r.json()
    if data:
        return float(data[0]["lat"]), float(data[0]["lon"])
    return None, None

@app.route("/lookup")
def lookup():
    address = request.args.get("address", "")
    if not address:
        return jsonify({"error": "Missing address parameter"}), 400

    lat, lng = geocode_address(address)
    if lat is None:
        return jsonify({"error": f"Could not geocode: {address}"}), 404

    row = find_cluster(lat, lng)
    if row is None:
        return jsonify({"error": "No cluster found for this address"}), 404

    extra = float(row["extra_slots"]) if pd.notna(row["extra_slots"]) else 0.0
    label = get_label(extra)

    return jsonify({
        "cluster_name": row["cluster_name"],
        "name": row["name"],
        "municipal": row["municipal"],
        "extra_slots": extra,
        "label": label,
        "lat": lat,
        "lng": lng
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok", "clusters_loaded": len(df)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5055))
    app.run(host="0.0.0.0", port=port)
