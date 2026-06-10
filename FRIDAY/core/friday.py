import datetime
import webbrowser
import subprocess
import pyttsx3
import colorama
from colorama import Fore, Style
import requests
import re
import sys
import threading
import ollama
import pythoncom

sys.path.insert(0, 'C:\\FRIDAY')
from voice.listener import wait_for_wake_word, get_voice_command, set_ui_wake_callback
from core.memory import (
    init_db, save_conversation, add_to_short_term,
    get_recent_conversations, save_memory, get_memory
)
from brain.llm import ask_llm, is_llm_available, get_ollama_client
from core.pc_control import (
    launch_app, kill_app, format_system_stats, check_alerts,
    set_volume, get_volume, mute, unmute,
    media_play_pause, media_next, media_previous,
    add_reminder, get_pending_reminders, register_reminder_callback,
    search_files, open_folder, create_folder
)
from core.web_search import search_web, search_news, search_youtube, get_wikipedia_summary, get_instant_answer

# -- Web UI Integration -----------------------------------
WEB_UI_AVAILABLE = False
try:
    from ui.friday_ui import (
        start_ui, update_stats, update_weather, update_uptime,
        set_listening, add_message, set_callbacks
    )

    WEB_UI_AVAILABLE = True
    print("Web UI module loaded")
except ImportError as e:
    print(f"Web UI module not available: {e}")
    import traceback

    traceback.print_exc()

# Import vision with better error handling
VISION_AVAILABLE = False
try:
    import core.vision as vision_module

    if hasattr(vision_module, 'capture_screen'):
        capture_screen = vision_module.capture_screen
        read_screen_text = vision_module.read_screen_text
        describe_screen = vision_module.describe_screen
        analyze_image = vision_module.analyze_image
        read_error_message = vision_module.read_error_message
        game_assist = vision_module.game_assist
        what_is_on_screen = vision_module.what_is_on_screen
        if hasattr(vision_module, 'analyze_active_window'):
            analyze_active_window = vision_module.analyze_active_window
        else:
            def analyze_active_window(app_name=""):
                return "Vision: analyze_active_window not available"
        VISION_AVAILABLE = True
        print("Vision module loaded successfully")
    else:
        raise ImportError("capture_screen not found in vision module")
except Exception as e:
    print(f"Vision module not available: {e}")


    def capture_screen(filename=None):
        return None, f"Vision error: {e}"


    def read_screen_text():
        return "Vision not available"


    def describe_screen(prompt=""):
        return "Vision not available"


    def analyze_image(image_path, prompt=""):
        return "Vision not available"


    def read_error_message():
        return "Vision not available"


    def game_assist():
        return "Vision not available"


    def what_is_on_screen():
        return "Vision not available"


    def analyze_active_window(app_name=""):
        return "Vision not available"

colorama.init()

# -- Voice Toggle ------------------------------------------
voice_active = True

# -- Voice Engine (Thread-Safe) --------------------------
_selected_voice = None


def _get_tts_engine():
    """Create a fresh TTS engine (thread-safe for Flask)."""
    engine = pyttsx3.init()
    engine.setProperty('rate', 175)
    engine.setProperty('volume', 1.0)
    voices = engine.getProperty('voices')

    voice_id = None
    for voice in voices:
        if 'female' in voice.name.lower() or 'zira' in voice.name.lower() or 'samantha' in voice.name.lower():
            voice_id = voice.id
            break
    if not voice_id and voices:
        voice_id = voices[0].id
    if voice_id:
        engine.setProperty('voice', voice_id)

    return engine


def speak(text, limit=800):
    """Speak text with configurable limit. Works from any thread."""
    if len(text) > limit:
        text = text[:limit] + "... That's all for now, Boss."

    print(Fore.CYAN + f"FRIDAY: {text}" + Style.RESET_ALL)

    if WEB_UI_AVAILABLE:
        try:
            add_message("FRIDAY", text, "friday")
        except Exception as e:
            pass

    # Thread-safe TTS: initialize COM + fresh engine per call
    try:
        pythoncom.CoInitialize()
        engine = _get_tts_engine()
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(Fore.RED + f"TTS Error: {e}" + Style.RESET_ALL)
    finally:
        try:
            pythoncom.CoUninitialize()
        except:
            pass

    save_conversation("friday", text)
    add_to_short_term("friday", text)


# -- Reminder Callback -------------------------------------
def on_reminder_triggered(message):
    """Called when a reminder fires."""
    speak(f"Reminder, Boss: {message}")


register_reminder_callback(on_reminder_triggered)


# -- UI Wake Handler ---------------------------------------
def on_ui_wake():
    """Called when wake word detected - trigger UI listening state."""
    if WEB_UI_AVAILABLE:
        try:
            set_listening(True)
            add_message("FRIDAY", "Yes Boss? I'm listening...", "friday")
        except Exception as e:
            print(f"UI wake error: {e}")


set_ui_wake_callback(on_ui_wake)


# -- Live Stats Updater ------------------------------------
def _update_live_stats():
    """Background thread to update system stats on UI."""
    import time
    import psutil

    while True:
        try:
            if WEB_UI_AVAILABLE:
                cpu = psutil.cpu_percent(interval=1)
                ram = psutil.virtual_memory()
                ram_used = round(ram.used / (1024 ** 3), 1)
                ram_total = round(ram.total / (1024 ** 3), 1)
                ram_pct = ram.percent

                disk = psutil.disk_usage('/')
                disk_used = round(disk.used / (1024 ** 3), 1)
                disk_total = round(disk.total / (1024 ** 3), 1)

                boot_time = psutil.boot_time()
                uptime_sec = int(time.time() - boot_time)
                hours = uptime_sec // 3600
                mins = (uptime_sec % 3600) // 60
                secs = uptime_sec % 60
                uptime_str = f"{hours:02d}:{mins:02d}:{secs:02d}"

                update_stats({
                    "cpu": f"{cpu}%",
                    "cpu_bar": f"{cpu}%",
                    "ram": f"{ram_used} GB",
                    "ram_percent": f"{ram_pct}%",
                    "ram_bar": f"{ram_pct}%",
                    "disk": f"{disk_used}/{disk_total} GB",
                    "disk_bar": f"{disk.percent}%"
                })
                update_uptime(uptime_str)

        except Exception as e:
            print(f"Stats update error: {e}")

        time.sleep(2)


# -- Personality --------------------------------------------
def greet():
    hour = datetime.datetime.now().hour
    if hour < 12:
        period = "Good morning"
    elif hour < 17:
        period = "Good afternoon"
    else:
        period = "Good evening"

    name = get_memory("name")
    if name:
        speak(f"{period}, {name}. F.R.I.D.A.Y. systems online. Welcome back, Boss.")
    else:
        speak(f"{period}, Boss. F.R.I.D.A.Y. systems online. How can I assist you today?")

    alerts = check_alerts()
    for alert in alerts:
        speak(f"Alert, Boss! {alert}")


# -- Skills -------------------------------------------------
def get_time():
    now = datetime.datetime.now().strftime("%I:%M %p")
    speak(f"The time is {now}, Boss.")


def get_date():
    today = datetime.datetime.now().strftime("%A, %B %d, %Y")
    speak(f"Today is {today}.")


def get_weather(city="Surat"):
    """Fetch weather using Open-Meteo (free, no API key)."""
    try:
        import urllib.request
        import urllib.parse
        import json

        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1&language=en&format=json"
        with urllib.request.urlopen(geo_url, timeout=15) as response:
            geo_data = json.loads(response.read().decode())

        if not geo_data.get("results"):
            speak(f"Sorry Boss, I couldn't find weather data for {city}.")
            return

        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m"
            f"&timezone=auto"
        )
        with urllib.request.urlopen(weather_url, timeout=15) as response:
            weather_data = json.loads(response.read().decode())

        current = weather_data.get("current", {})
        temp = round(current.get("temperature_2m", 0))
        humidity = current.get("relative_humidity_2m", 0)
        wind = current.get("wind_speed_10m", 0)
        feels = round(current.get("apparent_temperature", 0))

        code = current.get("weather_code", 0)
        conditions = {
            0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
            45: "foggy", 48: "rime fog", 51: "light drizzle", 53: "drizzle",
            55: "heavy drizzle", 61: "light rain", 63: "rain", 65: "heavy rain",
            71: "light snow", 73: "snow", 75: "heavy snow", 95: "thunderstorm"
        }
        condition = conditions.get(code, "unknown conditions")

        speak(
            f"Current weather in {city}: {temp} degrees Celsius with {condition}. Humidity is {humidity} percent, wind speed {wind} kilometers per hour. Feels like {feels} degrees.")

        if WEB_UI_AVAILABLE:
            try:
                update_weather(temp, city, condition.capitalize(), str(humidity), str(wind), str(feels))
            except:
                pass

    except Exception as e:
        print(f"Weather error: {e}")
        speak("Sorry Boss, I couldn't fetch the weather right now.")


def open_website(url):
    webbrowser.open(url)
    speak(f"Opening {url} for you, Boss.")


# -- Command Handler ----------------------------------------
def handle_command(command):
    global voice_active
    command = command.lower().strip()

    save_conversation("user", command)
    add_to_short_term("user", command)

    # -- DIRECT SYSTEM COMMANDS --
    if "time" in command and len(command) < 20:
        get_time()
    elif "date" in command and len(command) < 20:
        get_date()
    elif "weather" in command and "in" not in command and "at" not in command:
        get_weather()
    elif "youtube" in command and "search" not in command:
        open_website("https://youtube.com")
    elif "google" in command and "search" not in command:
        open_website("https://google.com")
    elif "github" in command:
        open_website("https://github.com")
    elif "hello" in command or "hi" in command:
        speak("Hello Boss! Always good to hear from you.")
    elif "joke" in command:
        speak("Why do programmers prefer dark mode? Because light attracts bugs, Boss.")
    elif "who are you" in command:
        speak(
            "I am F.R.I.D.A.Y. - Female Replacement Intelligent Digital Assistant Youth. Built exclusively for you, Boss.")

    # -- PC CONTROL COMMANDS --
    elif any(x in command for x in ["launch", "open", "start"]) and not any(
            x in command for x in ["website", "folder", "directory", "web", "news"]):
        app = command.replace("launch", "").replace("open", "").replace("start", "").strip()
        speak(launch_app(app))

    elif any(x in command for x in ["kill", "close", "stop", "terminate"]) and "website" not in command:
        app = command.replace("kill", "").replace("close", "").replace("stop", "").replace("terminate", "").strip()
        speak(kill_app(app))

    elif any(x in command for x in ["system status", "cpu", "ram", "memory", "battery", "disk", "pc status"]):
        stats = format_system_stats()
        speak(stats)
        if WEB_UI_AVAILABLE:
            try:
                import psutil
                cpu = psutil.cpu_percent(interval=0.5)
                ram = psutil.virtual_memory()
                update_stats({
                    "cpu": f"{cpu}%",
                    "cpu_bar": f"{cpu}%",
                    "ram": f"{round(ram.used / (1024 ** 3), 1)} GB",
                    "ram_percent": f"{ram.percent}%",
                    "ram_bar": f"{ram.percent}%"
                })
            except:
                pass

    elif "set volume" in command or "volume to" in command:
        numbers = re.findall(r'\d+', command)
        if numbers:
            speak(set_volume(int(numbers[0])))
        else:
            speak("What volume level, Boss?")

    elif "volume" in command and "set" not in command:
        speak(get_volume())

    elif "mute" in command:
        speak(mute())
    elif "unmute" in command:
        speak(unmute())

    elif any(x in command for x in ["play", "pause", "resume"]):
        speak(media_play_pause())
    elif "next track" in command or "next song" in command or "skip" in command:
        speak(media_next())
    elif "previous track" in command or "previous song" in command or "last song" in command:
        speak(media_previous())

    elif "remind me" in command or "set reminder" in command:
        numbers = re.findall(r'\d+', command)
        if numbers:
            minutes = int(numbers[0])
            msg = "Boss"
            if " to " in command:
                msg = command.split(" to ", 1)[-1]
            elif " that " in command:
                msg = command.split(" that ", 1)[-1]
            else:
                msg = command.replace("remind me", "").replace("set reminder", "").strip()
                msg = re.sub(r'in \d+ minutes?', '', msg).strip()
                msg = re.sub(r'in \d+ min', '', msg).strip()
            speak(add_reminder(minutes, msg))
        else:
            speak("When should I remind you, Boss?")

    elif any(x in command for x in ["pending reminders", "my reminders", "show reminders", "what reminders"]):
        speak(get_pending_reminders())

    elif "find file" in command or "locate file" in command or "search for file" in command:
        query = command.replace("find file", "").replace("locate file", "").replace("search for file", "").strip()
        speak(search_files(query))

    elif "open folder" in command or "open directory" in command:
        path = command.replace("open folder", "").replace("open directory", "").strip()
        speak(open_folder(path))

    elif "create folder" in command or "new folder" in command or "make folder" in command:
        name = command.replace("create folder", "").replace("new folder", "").replace("make folder", "").strip()
        speak(create_folder(name))

    elif "screenshot" in command or "take a picture" in command or "capture screen" in command:
        speak("Taking screenshot, Boss...")
        path, msg = capture_screen()
        speak(msg)

    elif any(x in command for x in
             ["whats on", "what's on", "whats happening on", "what's happening on", "check", "look at"]):
        if VISION_AVAILABLE:
            app_name = ""
            for word in ["whats on", "what's on", "whats happening on", "what's happening on", "check", "look at"]:
                if word in command:
                    app_name = command.replace(word, "").strip()
                    break
            speak(f"Looking at {app_name if app_name else 'your screen'}, Boss...")
            result = analyze_active_window(app_name)
            speak(result, limit=1000)
        else:
            speak("Vision module not available, Boss.")

    # -- WEB SEARCH COMMANDS --
    elif "youtube" in command and ("search" in command or "for" in command or "on" in command):
        query = command
        for phrase in ["search", "on youtube", "in youtube", "at youtube", "youtube"]:
            query = query.replace(phrase, "")
        query = query.replace("for", "").strip()
        if query:
            speak(search_youtube(query))
        else:
            speak("What should I search on YouTube, Boss?")

    elif "search" in command or "look up" in command or "google" in command:
        query = command.replace("search", "").replace("look up", "").replace("google", "").replace("for", "").strip()
        if query:
            speak("Searching the web, Boss...")
            result = search_web(query)
            speak(result, limit=1000)
        else:
            speak("What should I search for, Boss?")

    elif "news" in command or "headlines" in command or "what's happening" in command:
        query = command.replace("news", "").replace("headlines", "").replace("what's happening", "").strip()
        if not query:
            query = "latest news"
        speak("Getting the latest news, Boss...")
        result = search_news(query)
        speak(result, limit=1000)

    elif "wikipedia" in command or "wiki" in command:
        query = command.replace("wikipedia", "").replace("wiki", "").strip()
        if query:
            speak("Looking up Wikipedia, Boss...")
            result = get_wikipedia_summary(query)
            speak(result, limit=1000)
        else:
            speak("What should I look up on Wikipedia, Boss?")

    elif "weather in" in command or "weather at" in command:
        city = command.replace("weather in", "").replace("weather at", "").strip()
        if city:
            get_weather(city)
        else:
            get_weather()

    elif any(x in command for x in ["who is", "what is", "how to", "when is", "where is"]):
        speak("Looking that up, Boss...")
        result = get_instant_answer(command)
        speak(result, limit=800)

    # -- VISION COMMANDS --
    elif any(x in command for x in ["whats on screen", "what is on screen", "describe screen", "look at screen"]):
        if VISION_AVAILABLE:
            speak("Looking at your screen, Boss...")
            result = what_is_on_screen()
            speak(result, limit=1000)
        else:
            speak("Vision module not available, Boss.")

    elif any(x in command for x in ["read screen", "read text", "what does it say", "ocr"]):
        if VISION_AVAILABLE:
            speak("Reading the screen, Boss...")
            result = read_screen_text()
            speak(result, limit=1000)
        else:
            speak("Vision module not available, Boss.")

    elif any(x in command for x in ["read error", "fix error", "what's the error", "error on screen"]):
        if VISION_AVAILABLE:
            speak("Analyzing the error, Boss...")
            result = read_error_message()
            speak(result, limit=1000)
        else:
            speak("Vision module not available, Boss.")

    elif any(x in command for x in ["game assist", "help me with game", "analyze game"]):
        if VISION_AVAILABLE:
            speak("Analyzing your game, Boss...")
            result = game_assist()
            speak(result, limit=1000)
        else:
            speak("Vision module not available, Boss.")

    # -- MEMORY COMMANDS --
    elif "what do you remember" in command:
        convos = get_recent_conversations(5)
        if convos:
            speak("Here's what we talked about recently Boss.")
            for entry in convos:
                print(
                    Fore.YELLOW + f"[{entry['timestamp']}] {entry['role'].upper()}: {entry['message']}" + Style.RESET_ALL)
        else:
            speak("I don't have any memory of previous conversations Boss.")

    elif "remember" in command and " is " in command:
        try:
            after = command.replace("remember", "").strip()
            parts = after.split(" is ")
            key = parts[0].replace("my", "").strip()
            value = parts[1].strip()
            save_memory(key, value)
            speak(f"Got it Boss, I'll remember that your {key} is {value}.")
        except:
            speak("Sorry Boss, I couldn't save that. Try saying: remember my name is Kirtan.")

    # -- VOICE TOGGLE COMMANDS --
    elif "disable voice" in command or "stop listening" in command or "voice off" in command:
        voice_active = False
        speak("Voice disabled Boss, text mode only.")

    elif "enable voice" in command or "start listening" in command or "voice on" in command:
        voice_active = True
        speak("Voice enabled Boss, I'm listening.")

    # -- EXIT --
    elif "bye" in command or "exit" in command or "shutdown" in command:
        speak("Goodbye Boss. FRIDAY going offline. Stay safe.")
        if WEB_UI_AVAILABLE:
            try:
                set_listening(False)
            except:
                pass
        return False

    # -- FALLBACK TO LLM --
    else:
        if is_llm_available():
            print(Fore.MAGENTA + "Thinking..." + Style.RESET_ALL)
            response = ask_llm(command)
            print(Fore.YELLOW + f"Response: {response[:150]}..." + Style.RESET_ALL)
            if response and not response.startswith("Brain error"):
                speak(response, limit=1000)
            else:
                speak("Sorry Boss, my brain had a hiccup. Try again.")
        else:
            speak(f"I heard you say: {command}. I'm still learning, Boss. More skills coming soon.")

    if WEB_UI_AVAILABLE:
        try:
            set_listening(False)
        except:
            pass

    return True


# -- Main Loop --------------------------------------------
if __name__ == "__main__":
    init_db()

    if WEB_UI_AVAILABLE:
        print("Starting Web UI...")
        try:
            start_ui()
            set_callbacks(
                on_command=handle_command,
                on_wake=lambda: set_listening(True),
                on_camera_toggle=lambda: None
            )
            try:
                import psutil

                cpu = psutil.cpu_percent(interval=0.5)
                ram = psutil.virtual_memory()
                update_stats({
                    "cpu": f"{cpu}%",
                    "cpu_bar": f"{cpu}%",
                    "ram": f"{round(ram.used / (1024 ** 3), 1)} GB",
                    "ram_percent": f"{ram.percent}%",
                    "ram_bar": f"{ram.percent}%"
                })
            except:
                pass
            update_uptime("00:00:00")
            stats_thread = threading.Thread(target=_update_live_stats, daemon=True)
            stats_thread.start()
            add_message("FRIDAY", "F.R.I.D.A.Y. systems initializing...", "friday")
            print("UI started - open http://127.0.0.1:5000")
            import time

            time.sleep(1.5)
        except Exception as e:
            print(f"UI failed: {e}")
            import traceback

            traceback.print_exc()

    greet()

    client = get_ollama_client()
    if client:
        try:
            models = client.list()
            print(Fore.GREEN + f"Ollama connected. Models: {[m['model'] for m in models['models']]}" + Style.RESET_ALL)
        except Exception as e:
            print(Fore.GREEN + f"Ollama connected." + Style.RESET_ALL)
    else:
        print(Fore.RED + f"Ollama not connected. Run 'ollama serve' in another terminal." + Style.RESET_ALL)

speak("FRIDAY online. Type your command or say Hey Friday, Boss.")


def voice_loop():
    while True:
        if not voice_active:
            import time
            time.sleep(0.5)
            continue
        wait_for_wake_word()
        speak("Yes Boss?")
        command = get_voice_command()
        if command:
            handle_command(command)
        else:
            speak("I didn't catch that Boss. Try again.")


# Start voice in background thread
voice_thread = threading.Thread(target=voice_loop, daemon=True)
voice_thread.start()

# Text input in main thread
while True:
    print(Fore.YELLOW + "\nBoss: " + Style.RESET_ALL, end="")
    user_input = input()
    if user_input.strip() == "":
        continue
    if not handle_command(user_input):
        break

sys.exit(0)