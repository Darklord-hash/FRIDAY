import os
import subprocess
import psutil
import time
import threading
import re
from datetime import datetime, timedelta
import json

# ── App Launcher ──────────────────────────────────────────
# ── App Launcher ──────────────────────────────────────────
# Add your own paths here!
APP_PATHS = {
    # Browsers
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "brave": os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
    "opera": r"C:\Users\%USERNAME%\AppData\Local\Programs\Opera\launcher.exe",

    # System Apps
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "cmd": "cmd.exe",
    "explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "settings": "start ms-settings:",
    "control panel": "control.exe",
    "file explorer": "explorer.exe",

    # Media
    "spotify": os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
    "vlc": r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "windows media player": r"C:\Program Files\Windows Media Player\wmplayer.exe",
    "capcut": r"C:\Users\Kirtan\OneDrive\Desktop\CapCut.lnk",

    # Dev Tools
    "vscode": os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
    "visual studio code": os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
    "pycharm": os.path.expandvars(r"%PROGRAMFILES%\JetBrains\PyCharm Community Edition\bin\pycharm64.exe"),
    "notepad++": r"C:\Program Files\Notepad++\notepad++.exe",
    "git bash": r"C:\Program Files\Git\git-bash.exe",
    "claude": r"C:\Users\Kirtan\OneDrive\Desktop\Claude.lnk",
    "notion": r"C:\Users\Kirtan\OneDrive\Desktop\Notion.lnk",

    # Gaming Launchers
    "steam": r"C:\Program Files (x86)\Steam\steam.exe",
    "epic games": r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe",
    "epic": r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe",
    "nvidia geforce now": r"C:\Users\Kirtan\OneDrive\Desktop\NVIDIA GeForce NOW.lnk",
    "geforce now": r"C:\Users\Kirtan\OneDrive\Desktop\NVIDIA GeForce NOW.lnk",

    # Chat
    "discord": os.path.expandvars(r"%LOCALAPPDATA%\Discord\Update.exe"),
    "whatsapp": os.path.expandvars(r"%LOCALAPPDATA%\WhatsApp\WhatsApp.exe"),
    "telegram": os.path.expandvars(r"%APPDATA%\Telegram Desktop\Telegram.exe"),

    # Office
    "word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "powerpoint": r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",

    # YOUR GAMES
    "elden ring": r"D:\Games\eoiajsdmlkwtnde2ikla\Elden Ring\Game\eldenring.exe",
    "eldenring": r"D:\Games\eoiajsdmlkwtnde2ikla\Elden Ring\Game\eldenring.exe",
    "codevein": r"C:\Users\Kirtan\OneDrive\Desktop\CodeVein - Shortcut.lnk",
    "code vein": r"C:\Users\Kirtan\OneDrive\Desktop\CodeVein - Shortcut.lnk",

    # Remote Desktop
    "chrome remote desktop": r"C:\Users\Kirtan\OneDrive\Desktop\Chrome Remote Desktop (1).lnk",
    "remote desktop": r"C:\Users\Kirtan\OneDrive\Desktop\Chrome Remote Desktop (1).lnk",

    # Other
    "antigravity": r"C:\Users\Kirtan\OneDrive\Desktop\Antigravity.lnk",
    "tor browser": r"C:\Users\Kirtan\OneDrive\Desktop\Tor Browser.lnk",
    "tor": r"C:\Users\Kirtan\OneDrive\Desktop\Tor Browser.lnk",
}


def launch_app(app_name):
    """Launch an application by name."""
    app_name = app_name.lower().strip()

    # Direct match
    if app_name in APP_PATHS:
        path = APP_PATHS[app_name]
        try:
            if path.startswith("start "):
                os.system(path)
                return f"Launching {app_name}, Boss."
            else:
                # Expand environment variables
                path = os.path.expandvars(path)

                # Handle .lnk shortcuts
                if path.endswith('.lnk'):
                    os.startfile(path)
                    return f"Launching {app_name}, Boss."

                if os.path.exists(path):
                    subprocess.Popen(path, shell=True)
                    return f"Launching {app_name}, Boss."
                else:
                    # Try to find it anyway
                    subprocess.Popen(f'"{path}"', shell=True)
                    return f"Launching {app_name}, Boss."
        except Exception as e:
            return f"Couldn't launch {app_name}: {e}"

    # Try Windows start command as fallback
    try:
        subprocess.Popen(f'start "" "{app_name}"', shell=True)
        return f"Launching {app_name}, Boss."
    except:
        return f"Couldn't find {app_name}, Boss. Check the app name or add its path to APP_PATHS."
def kill_app(app_name):
    """Kill an application by name."""
    app_name = app_name.lower().strip()
    killed = []

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if app_name in proc.info['name'].lower():
                proc.terminate()
                killed.append(proc.info['name'])
                proc.wait(timeout=3)
        except psutil.TimeoutExpired:
            proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if killed:
        return f"Terminated {', '.join(set(killed))}, Boss."
    else:
        return f"No process named {app_name} found, Boss."


# ── System Monitoring ───────────────────────────────────
def get_system_stats():
    """Get CPU, RAM, GPU, Battery stats."""
    stats = {}

    # CPU
    stats['cpu_percent'] = psutil.cpu_percent(interval=0.5)
    stats['cpu_count'] = psutil.cpu_count()
    stats['cpu_freq'] = psutil.cpu_freq().current if psutil.cpu_freq() else 0

    # RAM
    mem = psutil.virtual_memory()
    stats['ram_percent'] = mem.percent
    stats['ram_used_gb'] = round(mem.used / (1024 ** 3), 2)
    stats['ram_total_gb'] = round(mem.total / (1024 ** 3), 2)

    # Disk
    disk = psutil.disk_usage('/')
    stats['disk_percent'] = disk.percent
    stats['disk_free_gb'] = round(disk.free / (1024 ** 3), 2)

    # Battery
    battery = psutil.sensors_battery()
    if battery:
        stats['battery_percent'] = battery.percent
        stats['battery_plugged'] = battery.power_plugged
        stats['battery_time_left'] = str(timedelta(seconds=battery.secsleft)) if battery.secsleft != -1 else "Unknown"
    else:
        stats['battery_percent'] = None

    # Network
    net = psutil.net_io_counters()
    stats['net_sent_mb'] = round(net.bytes_sent / (1024 ** 2), 2)
    stats['net_recv_mb'] = round(net.bytes_recv / (1024 ** 2), 2)

    # Boot time
    stats['boot_time'] = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M")

    return stats


def format_system_stats():
    """Format stats for speech."""
    stats = get_system_stats()

    msg = f"System status, Boss. "
    msg += f"CPU at {stats['cpu_percent']:.0f} percent across {stats['cpu_count']} cores. "
    msg += f"RAM at {stats['ram_percent']:.0f} percent, {stats['ram_used_gb']:.1f} of {stats['ram_total_gb']:.1f} gigabytes used. "
    msg += f"Disk {stats['disk_percent']:.0f} percent full, {stats['disk_free_gb']:.1f} gigabytes free. "

    if stats['battery_percent'] is not None:
        msg += f"Battery at {stats['battery_percent']:.0f} percent. "
        if stats['battery_plugged']:
            msg += "Plugged in and charging. "
        else:
            msg += f"Approximately {stats['battery_time_left']} remaining. "

    return msg


def check_alerts():
    """Check for system alerts."""
    stats = get_system_stats()
    alerts = []

    if stats['cpu_percent'] > 90:
        alerts.append(f"CPU critical at {stats['cpu_percent']:.0f} percent!")
    if stats['ram_percent'] > 90:
        alerts.append(f"RAM critical at {stats['ram_percent']:.0f} percent!")
    if stats['battery_percent'] is not None and stats['battery_percent'] < 20 and not stats['battery_plugged']:
        alerts.append(f"Battery low at {stats['battery_percent']:.0f} percent! Plug in now.")
    if stats['disk_percent'] > 90:
        alerts.append(f"Disk almost full at {stats['disk_percent']:.0f} percent!")

    return alerts


# ── Volume Control ────────────────────────────────────────
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL

    VOLUME_CONTROL = True
except ImportError:
    VOLUME_CONTROL = False


def get_volume_interface():
    """Get Windows volume control interface."""
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return interface.QueryInterface(IAudioEndpointVolume)


def set_volume(level):
    """Set volume 0-100."""
    if not VOLUME_CONTROL:
        return "Volume control not available, Boss."

    level = max(0, min(100, level))
    try:
        volume = get_volume_interface()
        volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        return f"Volume set to {level} percent, Boss."
    except Exception as e:
        return f"Volume control error: {e}"


def get_volume():
    """Get current volume."""
    if not VOLUME_CONTROL:
        return "Volume control not available, Boss."

    try:
        volume = get_volume_interface()
        current = int(volume.GetMasterVolumeLevelScalar() * 100)
        return f"Volume is at {current} percent, Boss."
    except Exception as e:
        return f"Volume control error: {e}"


def mute():
    """Mute system."""
    if not VOLUME_CONTROL:
        return "Volume control not available, Boss."

    try:
        volume = get_volume_interface()
        volume.SetMute(1, None)
        return "Muted, Boss."
    except Exception as e:
        return f"Mute error: {e}"


def unmute():
    """Unmute system."""
    if not VOLUME_CONTROL:
        return "Volume control not available, Boss."

    try:
        volume = get_volume_interface()
        volume.SetMute(0, None)
        return "Unmuted, Boss."
    except Exception as e:
        return f"Unmute error: {e}"


# ── Media Control ───────────────────────────────────────
try:
    import keyboard

    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False


def media_play_pause():
    if KEYBOARD_AVAILABLE:
        keyboard.press_and_release('play/pause media')
        return "Play or pause, Boss."
    return "Media control not available."


def media_next():
    if KEYBOARD_AVAILABLE:
        keyboard.press_and_release('next track')
        return "Next track, Boss."
    return "Media control not available."


def media_previous():
    if KEYBOARD_AVAILABLE:
        keyboard.press_and_release('previous track')
        return "Previous track, Boss."
    return "Media control not available."


# ── Task Scheduler ───────────────────────────────────────
scheduled_tasks = []
reminder_callbacks = []


def add_reminder(minutes, message):
    """Add a reminder."""
    reminder_time = datetime.now() + timedelta(minutes=minutes)
    task = {
        'time': reminder_time,
        'message': message,
        'triggered': False
    }
    scheduled_tasks.append(task)

    # Start background thread if not running
    if not any(t.name == 'reminder_thread' for t in threading.enumerate()):
        thread = threading.Thread(target=_reminder_loop, daemon=True, name='reminder_thread')
        thread.start()

    return f"Reminder set for {minutes} minutes, Boss: {message}"


def _reminder_loop():
    """Background thread for reminders."""
    while True:
        now = datetime.now()
        for task in scheduled_tasks:
            if not task['triggered'] and now >= task['time']:
                task['triggered'] = True
                # Notify via callback
                for callback in reminder_callbacks:
                    try:
                        callback(task['message'])
                    except:
                        pass
        # Clean up old tasks
        scheduled_tasks[:] = [t for t in scheduled_tasks if not t['triggered']]
        time.sleep(5)


def get_pending_reminders():
    """Get list of pending reminders."""
    pending = [t for t in scheduled_tasks if not t['triggered']]
    if not pending:
        return "No pending reminders, Boss."

    msg = f"You have {len(pending)} reminder{'s' if len(pending) > 1 else ''}, Boss. "
    for i, task in enumerate(pending, 1):
        time_left = task['time'] - datetime.now()
        minutes_left = max(0, int(time_left.total_seconds() / 60))
        msg += f"Reminder {i}: {task['message']} in {minutes_left} minutes. "
    return msg


def register_reminder_callback(callback):
    """Register a function to be called when reminder triggers."""
    reminder_callbacks.append(callback)


# ── File Operations ───────────────────────────────────────
def search_files(query, path=None, limit=5):
    """Search for files by name."""
    if path is None:
        path = os.path.expanduser("~")

    matches = []
    try:
        for root, dirs, files in os.walk(path):
            # Skip hidden/system folders
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['Windows', 'ProgramData']]
            for file in files:
                if query.lower() in file.lower():
                    matches.append(os.path.join(root, file))
                    if len(matches) >= limit:
                        return f"Found {len(matches)} files, Boss. Top match: {matches[0]}"
    except PermissionError:
        pass

    if matches:
        return f"Found {len(matches)} files, Boss. Top match: {matches[0]}"
    return f"No files found matching {query}, Boss."


def open_folder(path):
    """Open a folder in Explorer."""
    try:
        if os.path.exists(path):
            os.startfile(path)
            return f"Opened {path}, Boss."
        else:
            # Try common locations
            expanded = os.path.expandvars(path)
            if os.path.exists(expanded):
                os.startfile(expanded)
                return f"Opened {expanded}, Boss."
            return f"Folder not found: {path}, Boss."
    except Exception as e:
        return f"Couldn't open folder: {e}"


def create_folder(name, path=None):
    """Create a new folder."""
    if path is None:
        path = os.path.expanduser("~\\Desktop")
    full_path = os.path.join(path, name)
    try:
        os.makedirs(full_path, exist_ok=True)
        return f"Created folder {name}, Boss."
    except Exception as e:
        return f"Couldn't create folder: {e}"


# ── Screenshot ────────────────────────────────────────────
try:
    import pyautogui

    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False




# ── Test ────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== FRIDAY PC Control Test ===\n")
    print("Available apps:", list(APP_PATHS.keys()))
    print("\nSystem Stats:")
    print(format_system_stats())
    print(f"\nVolume: {get_volume()}")