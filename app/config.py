import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# MongoDB
MONGO_DSN = os.environ.get("MONGO_DSN", "")
MONGODB_DB = os.environ.get("MONGODB_DB", "hypane")

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SKILLS_DIR = BASE_DIR / "skills"
TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = BASE_DIR / "static"
EXTENSIONS_DIR = BASE_DIR / "extensions"

# Files
DASHBOARD_FILE = DATA_DIR / "dashboard.json"  # used by migrate.py only
SESSIONS_DIR = DATA_DIR / "sessions"

# Agent
PI_COMMAND = "pi"
DASHBOARD_EXTENSION = EXTENSIONS_DIR / "dashboard-tools.ts"

# Skills to load
SKILLS = [
    SKILLS_DIR / "_system.md",
    SKILLS_DIR / "data_collection.md",
]
