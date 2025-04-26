import json
import os
from flask import Flask, request, jsonify
from collections import defaultdict
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

LEADERBOARD_FILE = "leaderboard.json"
super_rare_counts = defaultdict(int)

# Load saved data
def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, "r") as f:
            data = json.load(f)
            for user, count in data.items():
                super_rare_counts[user] = count

# Save data to file
def save_leaderboard():
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(super_rare_counts, f)

@app.route("/pull", methods=["POST"])
def record_pull():
    data = request.get_json()
    username = data.get("username")
    rarity = data.get("rarity")

    if not username or rarity != "SUPER RARE":
        return jsonify({"error": "Invalid data"}), 400

    super_rare_counts[username] += 1
    save_leaderboard()
    return jsonify({"message": "Recorded!", "total": super_rare_counts[username]}), 200

@app.route("/leaderboard", methods=["GET"])
def get_leaderboard():
    sorted_leaderboard = sorted(super_rare_counts.items(), key=lambda x: x[1], reverse=True)
    return jsonify(sorted_leaderboard)

if __name__ == "__main__":
    load_leaderboard()
    app.run(host="0.0.0.0", port=5000, debug=True)
