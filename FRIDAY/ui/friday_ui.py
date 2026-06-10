from flask import Flask, render_template, jsonify, request
import threading
import logging
import json
import os
import sys
import time
from datetime import datetime
import urllib.request
import urllib.parse

sys.path.insert(0, 'C:\FRIDAY')

app = Flask(__name__, template_folder='templates', static_folder='static')

# Global state
ui_state = {
    "listening": False,
    "speaking": False,
    "messages": [],
    "system_stats": {},
    "weather": {"temp": "--", "city": "Surat", "condition": "Loading...", "humidity": "", "wind": "", "feels_like": ""},
    "uptime": "00:00:00",
    "camera_active": False,
    "status": "STANDBY"
}

_callbacks = {
    "on_command": None,
    "on_wake": None,
    "on_camera_toggle": None
}

# Weather config
WEATHER_CITY = "Surat"
WEATHER_UPDATE_INTERVAL = 600  # 10 minutes


def set_callbacks(on_command=None, on_wake=None, on_camera_toggle=None):
    _callbacks["on_command"] = on_command
    _callbacks["on_wake"] = on_wake
    _callbacks["on_camera_toggle"] = on_camera_toggle


@app.route('/')
def index():
    return render_template('friday.html')


@app.route('/api/state')
def get_state():
    return jsonify(ui_state)


@app.route('/api/command', methods=['POST'])
def command():
    data = request.json
    text = data.get('text', '')
    # FIX: Removed add_message here - friday.py handle_command() already adds it
    if _callbacks["on_command"]:
        _callbacks["on_command"](text)
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "message": "No handler"})


@app.route('/api/wake', methods=['POST'])
def wake():
    ui_state["listening"] = True
    ui_state["status"] = "LISTENING"
    if _callbacks["on_wake"]:
        _callbacks["on_wake"]()
    return jsonify({"status": "ok"})


@app.route('/api/sleep', methods=['POST'])
def sleep():
    ui_state["listening"] = False
    ui_state["speaking"] = False
    ui_state["status"] = "STANDBY"
    return jsonify({"status": "ok"})


def add_message(sender, text, msg_type):
    ui_state["messages"].append({
        "sender": sender,
        "text": text,
        "type": msg_type,
        "time": datetime.now().strftime("%H:%M:%S")
    })
    if len(ui_state["messages"]) > 50:
        ui_state["messages"] = ui_state["messages"][-50:]


def update_stats(stats_dict):
    ui_state["system_stats"].update(stats_dict)


def update_weather(temp, city, condition, humidity="", wind="", feels_like=""):
    ui_state["weather"] = {
        "temp": temp,
        "city": city,
        "condition": condition,
        "humidity": humidity,
        "wind": wind,
        "feels_like": feels_like
    }


def update_uptime(uptime_str):
    ui_state["uptime"] = uptime_str


def set_listening(listening):
    ui_state["listening"] = listening
    ui_state["status"] = "LISTENING" if listening else "STANDBY"


# ==================== WEATHER ====================

def get_weather_condition(code):
    """Convert WMO weather code to readable condition."""
    conditions = {
        0: "Clear sky",
        1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Depositing rime fog",
        51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
        56: "Light freezing drizzle", 57: "Dense freezing drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        66: "Light freezing rain", 67: "Heavy freezing rain",
        71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
        85: "Slight snow showers", 86: "Heavy snow showers",
        95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
    }
    return conditions.get(code, "Unknown")


def fetch_weather(city=None):
    """Fetch live weather from Open-Meteo (free, no API key)."""
    if city is None:
        city = WEATHER_CITY

    try:
        # Step 1: Get coordinates
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1&language=en&format=json"
        with urllib.request.urlopen(geo_url, timeout=5) as response:
            geo_data = json.loads(response.read().decode())

        if not geo_data.get("results"):
            print(f"⚠️ City '{city}' not found")
            return None

        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]

        # Step 2: Get weather
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m"
            f"&timezone=auto"
        )
        with urllib.request.urlopen(weather_url, timeout=5) as response:
            weather_data = json.loads(response.read().decode())

        current = weather_data.get("current", {})

        return {
            "temp": round(current.get("temperature_2m", 0)),
            "city": city,
            "condition": get_weather_condition(current.get("weather_code", 0)),
            "humidity": f"{current.get('relative_humidity_2m', 0)}",
            "wind": f"{current.get('wind_speed_10m', 0)}",
            "feels_like": round(current.get("apparent_temperature", 0))
        }
    except Exception as e:
        print(f"⚠️ Weather fetch failed: {e}")
        return None


def weather_updater():
    """Background thread: updates weather every 10 minutes."""
    while True:
        weather = fetch_weather()
        if weather:
            update_weather(
                temp=weather["temp"],
                city=weather["city"],
                condition=weather["condition"],
                humidity=weather["humidity"],
                wind=weather["wind"],
                feels_like=weather["feels_like"]
            )
            print(f"🌤️ Weather updated: {weather['city']} {weather['temp']}°C, {weather['condition']}")
        time.sleep(WEATHER_UPDATE_INTERVAL)


# ==================== START UI ====================

def start_ui(host='127.0.0.1', port=5000):
    # Suppress Flask request logs
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    # Start weather updater (fetch once immediately, then every 10 min)
    weather_thread = threading.Thread(target=weather_updater, daemon=True)
    weather_thread.start()

    def run():
        app.run(host=host, port=port, debug=False, use_reloader=False)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    print(f"🌐 FRIDAY UI running at http://{host}:{port}")
    return thread


if __name__ == "__main__":
    start_ui()