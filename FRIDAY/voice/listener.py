import speech_recognition as sr
import time

# ── Config ────────────────────────────────────────────────
SAMPLE_RATE = 16000
WAKE_WORD = "hey friday"
WAKE_WORD_ALIASES = ["hey friday", "hay friday", "a friday", "friday"]

recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.8

# ── UI Callback (set by friday.py) ─────────────────────────
_ui_wake_callback = None

def set_ui_wake_callback(callback):
    """Set callback to trigger UI wake animation."""
    global _ui_wake_callback
    _ui_wake_callback = callback

# ── Microphone Test ───────────────────────────────────────
def list_microphones():
    print("Available microphones:")
    for i, name in enumerate(sr.Microphone.list_microphone_names()):
        marker = " ← DEFAULT" if i == sr.Microphone().device_index else ""
        print(f"  [{i}] {name}{marker}")

# ── Listen Once ───────────────────────────────────────────
def listen_once(timeout=5, phrase_limit=10, ambient_adjust=0.5):
    with sr.Microphone(sample_rate=SAMPLE_RATE) as source:
        print("🎤 Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=ambient_adjust)
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
            try:
                text = recognizer.recognize_google(audio, language="en-US")
                return text.lower().strip()
            except sr.UnknownValueError:
                print("🤷 Couldn't understand audio")
                return None
            except sr.RequestError as e:
                print(f"⚠ Google STT error: {e}")
                return None
        except sr.WaitTimeoutError:
            return None
        except Exception as e:
            print(f"⚠ Mic error: {e}")
            return None

# ── Wake Word Detection ───────────────────────────────────
def wait_for_wake_word():
    print(f"😴 Sleeping... say '{WAKE_WORD}' to wake F.R.I.D.A.Y.")
    while True:
        result = listen_once(timeout=10, phrase_limit=4, ambient_adjust=0.3)
        if result:
            if any(alias in result for alias in WAKE_WORD_ALIASES):
                print("✅ Wake word detected!")
                # Trigger UI wake animation
                if _ui_wake_callback:
                    try:
                        _ui_wake_callback()
                    except Exception as e:
                        print(f"⚠️ UI wake callback error: {e}")
                return True
            else:
                print(f"💤 Heard '{result}' — not wake word, still sleeping...")
        time.sleep(0.1)

# ── Full Voice Input ──────────────────────────────────────
def get_voice_command():
    """Get a voice command after wake word. Returns text or None."""
    print("🎤 Say your command...")
    result = listen_once(timeout=10, phrase_limit=20)
    if result:
        print(f"🗣 You said: {result}")
    else:
        print("🤷 No command detected")
    return result

if __name__ == "__main__":
    list_microphones()
    print("\nTesting wake word detection (say 'Hey Friday')...")
    if wait_for_wake_word():
        print("F.R.I.D.A.Y. is awake! Now say a command:")
        cmd = get_voice_command()
        if cmd:
            print(f"Command received: {cmd}")
        else:
            print("No command heard")