from flask import Flask, jsonify, request
import pandas as pd
import ast

app = Flask(__name__)

df = pd.read_csv("output.csv")

def parse_all_tk(val):
    try:
        return ast.literal_eval(val)
    except:
        return []

df["all_tk_parsed"] = df["all_tk"].apply(parse_all_tk)

def get_label(extra_slots):
    if extra_slots <= 50:
        return "Very Low"
    elif extra_slots <= 100:
        return "Low"
    elif extra_slots <= 150:
        return "Medium"
    else:
        return "Hot"

@app.route("/lookup")
def lookup():
    tk = request.args.get("tk", type=int)
    if not tk:
        return jsonify({"error": "Missing tk parameter"}), 400

    row = df[df["tk"] == tk]
    if row.empty:
        row = df[df["all_tk_parsed"].apply(lambda tks: tk in tks)]

    if row.empty:
        return jsonify({"error": f"TK {tk} not found"}), 404

    row = row.iloc[0]
    extra = float(row["extra_slots"]) if pd.notna(row["extra_slots"]) else 0.0
    label = get_label(extra)

    return jsonify({
        "tk": int(row["tk"]),
        "cluster_name": row["cluster_name"],
        "name": row["name"],
        "municipal": row["municipal"],
        "extra_slots": extra,
        "label": label
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok", "clusters_loaded": len(df)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5055)
