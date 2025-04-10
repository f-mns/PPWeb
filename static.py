import os
import json
from win32comext.shell import shell, shellcon

VERSION = "1.0.0"
CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "HOST": "0.0.0.0",
    "PORT": 5000,
    "DEBUG_MODE": True,
    "INSTANCE_NAME": "Default Instanc",
    "LOGIN_PASSWORD": "your_login_password",
    "ADMIN_PASSWORD": "your_admin_password",
    "UPLOAD_FOLDER": "ppweb",
    "FILE_NAME": "upload.pptx",
    "VIEW_ONLY": {
        "hidden": False,
        "download": True
    }
}

def ensure_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        print(f"[INFO] '{CONFIG_FILE}' was missing and has been created with default values.")
    else:
        print(f"[INFO] '{CONFIG_FILE}' already exists.")

# Ensure config exists
ensure_config()

# Load config
with open(CONFIG_FILE) as f:
    config = json.load(f)

# Extract values from the config
HOST = config.get("HOST", "127.0.0.1")
PORT = config.get("PORT", 5000)
DEBUG_MODE = config.get("DEBUG_MODE", False)
INSTANCE_NAME = config.get("INSTANCE_NAME", "Default Instance")
LOGIN_PASSWORD = config.get("LOGIN_PASSWORD", "your_login_password")
ADMIN_PASSWORD = config.get("ADMIN_PASSWORD", "your_admin_password")
SCREENSHOT_FILE_PATH = "./screen.png"

# View-only flags
VIEW_ONLY_HIDDEN = config.get("VIEW_ONLY", {}).get("hidden", False)
VIEW_ONLY_DOWNLOAD = config.get("VIEW_ONLY", {}).get("download", True)

# Dynamic paths
UPLOAD_FOLDER = os.path.join(
    shell.SHGetFolderPath(0, shellcon.CSIDL_PROFILE, None, 0),
    config.get("UPLOAD_FOLDER", "ppweb")
)
FILE_PATH = os.path.join(UPLOAD_FOLDER, config.get("FILE_NAME", "upload.pptx"))

# App state
RUNNING = False

# Reload configuration
def reload_config():
    global config, HOST, PORT, DEBUG_MODE, INSTANCE_NAME, LOGIN_PASSWORD, ADMIN_PASSWORD, SCREENSHOT_FILE_PATH, VIEW_ONLY_HIDDEN, VIEW_ONLY_DOWNLOAD, UPLOAD_FOLDER, FILE_PATH
    with open(CONFIG_FILE) as f:
        config = json.load(f)
        # Update global variables
        HOST = config.get("HOST", "127.0.0.1")
        PORT = config.get("PORT", 5000)
        DEBUG_MODE = config.get("DEBUG_MODE", False)
        INSTANCE_NAME = config.get("INSTANCE_NAME", "Default Instance")
        LOGIN_PASSWORD = config.get("LOGIN_PASSWORD", "")
        ADMIN_PASSWORD = config.get("ADMIN_PASSWORD", "")
        SCREENSHOT_FILE_PATH = "./screen.png"

        # View-only flags
        VIEW_ONLY_HIDDEN = config.get("VIEW_ONLY", {}).get("hidden", True)
        VIEW_ONLY_DOWNLOAD = config.get("VIEW_ONLY", {}).get("download", False)

        # Update dynamic paths
        UPLOAD_FOLDER = os.path.join(
            shell.SHGetFolderPath(0, shellcon.CSIDL_PROFILE, None, 0),
            config.get("UPLOAD_FOLDER", "ppweb")
        )
        FILE_PATH = os.path.join(UPLOAD_FOLDER, config.get("FILE_NAME", "upload.pptx"))
