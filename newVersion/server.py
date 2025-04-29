from flask import Flask, request, jsonify, render_template_string
import random
import threading
import json

app = Flask(__name__)

# === Data Structures ===
rpi_data = {}  # {rpi_id: {"light": value, "city": value, "stats": {...}}}
bird_rarity_list = ["Common", "Rare", "Super Rare"]

# Bird pools by rarity
bird_pools = {
    "Common": ["Pigeon", "Duck", "Crow"],
    "Rare": ["Flamingo", "Eagle", "Swan"],
    "Super Rare": ["Phoenix", "Golden Owl", "Mythic Crane"]
}

# Special Regional Birds
regional_birds = {
    "Los Angeles": "LA Golden Eagle",
    "New York City": "NYC Diamond Pigeon"
}

# Base odds for rarities
base_odds = {
    "Common": 0.82,
    "Rare": 0.15,
    "Super Rare": 0.03
}

DATA_FILE = "rpi_data.json"
lock = threading.Lock()

# === Helper Functions ===

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(rpi_data, f)

def load_data():
    global rpi_data
    try:
        with open(DATA_FILE, "r") as f:
            rpi_data = json.load(f)
    except FileNotFoundError:
        rpi_data = {}

def adjust_odds(light_level):
    """
    Adjust odds based on light level.
    """
    odds = base_odds.copy()

    if light_level > 80:
        odds["Super Rare"] += 0.02
        odds["Common"] -= 0.01
        odds["Rare"] -= 0.01
    elif light_level > 70:
        odds["Super Rare"] += 0.01
        odds["Rare"] -= 0.005
        odds["Common"] -= 0.005

    # Normalize
    total = sum(odds.values())
    for k in odds.keys():
        odds[k] = odds[k] / total

    return odds

def weighted_random_choice(odds_dict, city):
    """
    Choose a rarity based on odds, then pick a bird from that rarity's pool.
    """
    rarities = list(odds_dict.keys())
    weights = list(odds_dict.values())
    chosen_rarity = random.choices(rarities, weights=weights, k=1)[0]

    if chosen_rarity == "Super Rare":
        super_rare_pool = bird_pools["Super Rare"].copy()
        if city in regional_birds:
            super_rare_pool.append(regional_birds[city])
        return random.choice(super_rare_pool)

    return random.choice(bird_pools[chosen_rarity])

# === API Routes ===

@app.route('/update_light', methods=['POST'])
def update_light():
    data = request.get_json()
    rpi_id = data.get("rpi_id")
    light_value = data.get("light")
    city = data.get("city")

    if not rpi_id or light_value is None or not city:
        return jsonify({"error": "Missing rpi_id, light, or city"}), 400

    with lock:
        if rpi_id not in rpi_data:
            rpi_data[rpi_id] = {
                "light": light_value,
                "city": city,
                "stats": {
                    "super_rares": 0,
                    "rarest_bird": "Common",
                    "last_bird": "",
                    "all_birds": []
                }
            }
        else:
            rpi_data[rpi_id]["light"] = light_value
            rpi_data[rpi_id]["city"] = city

        save_data()

    return jsonify({"status": "Light and City updated!"})

@app.route('/gamble', methods=['POST'])
def gamble():
    data = request.get_json()
    rpi_id = data.get("rpi_id")

    if not rpi_id or rpi_id not in rpi_data:
        return jsonify({"error": "Invalid or unknown rpi_id"}), 400

    with lock:
        light = rpi_data[rpi_id]["light"]
        city = rpi_data[rpi_id]["city"]
        stats = rpi_data[rpi_id]["stats"]

    odds = adjust_odds(light)
    bird = weighted_random_choice(odds, city)

    with lock:
        stats["last_bird"] = bird
        stats["all_birds"].append(bird)

        if bird in bird_pools["Super Rare"] or bird in regional_birds.values():
            stats["super_rares"] += 1

        # Determine rarity of won bird
        if bird in bird_pools["Common"]:
            bird_rarity = "Common"
        elif bird in bird_pools["Rare"]:
            bird_rarity = "Rare"
        else:
            bird_rarity = "Super Rare"

        # Compare rarity indexes
        current_best_index = bird_rarity_list.index(stats["rarest_bird"]) if stats["rarest_bird"] in bird_rarity_list else -1
        new_bird_index = bird_rarity_list.index(bird_rarity)

        if new_bird_index > current_best_index:
            stats["rarest_bird"] = bird_rarity

        save_data()

    return jsonify({"bird": bird, "stats": stats})

@app.route('/stats/<rpi_id>', methods=['GET'])
def stats(rpi_id):
    with lock:
        if rpi_id not in rpi_data:
            return jsonify({"error": "Unknown rpi_id"}), 404
        return jsonify(rpi_data[rpi_id]["stats"])

@app.route('/api/stats')
def api_stats():
    return jsonify(rpi_data)

@app.route('/dashboard')
def dashboard():
    html_template = """
    <html>
    <head>
        <title>Bird Game Dashboard</title>
        <style>
            table { border-collapse: collapse; width: 90%; margin: 20px auto; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
            th { background-color: #4CAF50; color: white; }
            body { font-family: Arial, sans-serif; background-color: #f2f2f2; }
            h1 { text-align: center; }
        </style>
    </head>
    <body>
        <h1>Bird Game Dashboard</h1>
        <table id="statsTable">
            <thead>
                <tr>
                    <th>RPI ID</th>
                    <th>City</th>
                    <th>Light Level</th>
                    <th>Super Rare Birds</th>
                    <th>Rarest Bird</th>
                    <th>Last Bird Won</th>
                </tr>
            </thead>
            <tbody>
                <!-- Rows will be inserted here by JavaScript -->
            </tbody>
        </table>

        <script>
            function fetchStats() {
                fetch('/api/stats')
                    .then(response => response.json())
                    .then(data => {
                        const tbody = document.querySelector('#statsTable tbody');
                        tbody.innerHTML = ''; // Clear old rows

                        for (const [rpi_id, info] of Object.entries(data)) {
                            const row = document.createElement('tr');

                            row.innerHTML = `
                                <td>${rpi_id}</td>
                                <td>${info.city ?? 'Unknown'}</td>
                                <td>${info.light ?? 'N/A'}</td>
                                <td>${info.stats?.super_rares ?? 0}</td>
                                <td>${info.stats?.rarest_bird ?? 'None'}</td>
                                <td>${info.stats?.last_bird ?? 'None'}</td>
                            `;
                            tbody.appendChild(row);
                        }
                    });
            }

            // Fetch immediately, then every 5 seconds
            fetchStats();
            setInterval(fetchStats, 5000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)


if __name__ == '__main__':
    load_data()
    app.run(host="0.0.0.0", port=5000)
