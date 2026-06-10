import os
import base64
import mss
import mss.tools
from datetime import datetime

# Try to import OCR libraries (optional)
try:
    from PIL import Image
    import pytesseract

    # Try common Tesseract paths
    tesseract_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',  # YOUR PATH
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Tesseract-OCR\tesseract.exe',
    ]
    OCR_AVAILABLE = False
    for path in tesseract_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            OCR_AVAILABLE = True
            print(f"✅ Tesseract found at: {path}")
            break
    if not OCR_AVAILABLE:
        print("⚠️ Tesseract not found in common paths")
except ImportError as e:
    print(f"⚠️ OCR import error: {e}")
    OCR_AVAILABLE = False

# Try to import ollama client
try:
    from brain.llm import get_ollama_client

    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

VISION_MODEL = "llava:7b"
SCREENSHOTS_DIR = os.path.expanduser("~\\Desktop\\FRIDAY_Screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


# ── Screenshot ────────────────────────────────────────────
def capture_screen(filename=None):
    """Take a screenshot and save it."""
    try:
        if filename is None:
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        path = os.path.join(SCREENSHOTS_DIR, filename)

        with mss.mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=path)

        return path, f"Screenshot saved to Desktop, Boss."
    except Exception as e:
        return None, f"Screenshot error, Boss: {e}"

# ── OCR ───────────────────────────────────────────────────
def read_screen_text():
    """Read text from current screen using OCR."""
    if not OCR_AVAILABLE:
        return "OCR not available. Check Tesseract installation, Boss."

    try:
        path, msg = capture_screen("ocr_temp.png")
        if not path:
            return "Couldn't take screenshot for OCR, Boss."

        image = Image.open(path)
        text = pytesseract.image_to_string(image).strip()

        if text:
            return f"Here's what I can read on screen, Boss: {text[:800]}"
        return "No readable text found on screen, Boss."
    except Exception as e:
        return f"OCR error, Boss: {e}"


def read_image_text(image_path):
    """Read text from a specific image file."""
    if not OCR_AVAILABLE:
        return "OCR not available, Boss."

    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image).strip()
        if text:
            return f"Text found, Boss: {text[:800]}"
        return "No readable text found in image, Boss."
    except Exception as e:
        return f"OCR error, Boss: {e}"


# ── Vision LLM ────────────────────────────────────────────
def image_to_base64(image_path):
    """Convert image to base64 for LLaVA."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def describe_screen(prompt="Describe what you see on this screen in detail."):
    """Use LLaVA to describe the current screen."""
    try:
        path, msg = capture_screen("vision_temp.png")
        if not path:
            return "Couldn't take screenshot, Boss."

        return analyze_image(path, prompt)
    except Exception as e:
        return f"Vision error, Boss: {e}"


def analyze_image(image_path, prompt="What do you see in this image?"):
    """Use LLaVA to analyze any image."""
    try:
        if not OLLAMA_AVAILABLE:
            return "Ollama not available for vision analysis, Boss."

        client = get_ollama_client()
        if not client:
            return "Ollama not connected, Boss."

        image_data = image_to_base64(image_path)

        response = client.chat(
            model=VISION_MODEL,
            messages=[{
                "role": "user",
                "content": prompt,
                "images": [image_data]
            }]
        )
        return response['message']['content']
    except Exception as e:
        return f"Vision analysis error, Boss: {e}"


def read_error_message():
    """Take screenshot and ask LLaVA to identify and fix any error."""
    prompt = """You are FRIDAY, an AI assistant. 
Look at this screenshot and:
1. Identify any error messages or problems
2. Explain what the error means
3. Suggest how to fix it
Be concise and clear. Address the user as Boss."""
    return describe_screen(prompt)


def game_assist():
    """Take screenshot and analyze game UI/stats."""
    prompt = """You are FRIDAY, an AI assistant analyzing a game screen.
Look at this screenshot and:
1. Identify the game if possible
2. Describe the current game state, UI elements, health/stats if visible
3. Give any useful tactical advice
Be concise. Address the user as Boss."""
    return describe_screen(prompt)


def what_is_on_screen():
    """General screen description."""
    prompt = """You are FRIDAY, an AI assistant.
Look at this screenshot and briefly describe:
1. What application or website is open
2. What content is visible
3. Anything important the user should know
Keep it under 3 sentences. Address the user as Boss."""
    return describe_screen(prompt)


def analyze_active_window(app_name: str = ""):
    """Take screenshot and analyze specific app/window content."""
    try:
        # Take screenshot first
        path, msg = capture_screen("active_window.png")
        if not path:
            return "Couldn't take screenshot, Boss."

        # Build prompt based on app name
        if app_name:
            prompt = f"""You are FRIDAY, Tony Stark's AI assistant.
The user wants to know what's happening on {app_name}.
Look at this screenshot carefully and:
1. Find and focus on {app_name} content if visible
2. Describe what's happening there — messages, notifications, activity
3. Summarize the key information
Be concise and direct. Address the user as Boss."""
        else:
            prompt = """You are FRIDAY, Tony Stark's AI assistant.
Look at this screenshot and describe what's currently on screen.
Focus on the most active/visible application.
Be concise. Address the user as Boss."""

        return analyze_image(path, prompt)

    except Exception as e:
        return f"Vision error, Boss: {e}"


# ── Test ──────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing screenshot...")
    path, msg = capture_screen()
    print(msg)
    if path:
        print(f"Saved to: {path}")
        print("\nTesting OCR...")
        print(read_screen_text())