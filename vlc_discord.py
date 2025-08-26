import time
import requests
import configparser
import threading
import sys
from pypresence import Presence
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw

# Load configuration
config = configparser.ConfigParser()
config.read("config.txt")

CLIENT_ID = config["discord"]["client_id"]
LARGE_IMAGE = config["discord"].get("large_image", "vlc")
LARGE_TEXT = config["discord"].get("large_text", "VLC Media Player")

VLC_URL = config["vlc"].get("url", "http://localhost:8080/requests/status.json")
VLC_PASSWORD = config["vlc"].get("password", "vlcpass")

UPDATE_INTERVAL = config["settings"].getint("update_interval", 15)

# Setup Discord RPC
RPC = Presence(CLIENT_ID)
RPC.connect()

running = True  # flag to control main loop


def get_vlc_title():
    """Fetch the currently playing title from VLC, including stream metadata."""
    try:
        r = requests.get(VLC_URL, auth=("", VLC_PASSWORD))
        data = r.json()

        if "information" in data and "category" in data["information"]:
            meta = data["information"]["category"].get("meta", {})

            # Check for streaming metadata first
            if "now_playing" in meta:
                return meta["now_playing"]

            # Some streams use "artist" + "title"
            if "artist" in meta and "title" in meta:
                return f"{meta['artist']} - {meta['title']}"

            # Fallback: just title or filename
            return meta.get("title") or meta.get("filename")

    except Exception:
        return None


# --- Tray icon setup ---
def create_icon():
    """Make a simple orange cone-like icon."""
    img = Image.new("RGB", (64, 64), (255, 128, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((8, 8, 56, 56), fill=(255, 128, 0), outline=(0, 0, 0))
    return img


def on_exit(icon, item):
    global running
    running = False
    icon.stop()
    RPC.clear()
    RPC.close()
    sys.exit(0)


def run_tray():
    menu = Menu(MenuItem("Exit", on_exit))
    icon = Icon("VLC Discord RPC", create_icon(), "VLC Discord RPC", menu)
    icon.run()


# Run tray in background thread
threading.Thread(target=run_tray, daemon=True).start()

# --- Main loop ---
while running:
    title = get_vlc_title()
    if title:
        RPC.update(
            state="Playing via VLC",
            details=title,
            large_image=LARGE_IMAGE,
            large_text=LARGE_TEXT
        )
    else:
        RPC.clear()
    time.sleep(UPDATE_INTERVAL)
