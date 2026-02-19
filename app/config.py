from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SKILLS_DIR = BASE_DIR / "skills"
TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = BASE_DIR / "static"
EXTENSIONS_DIR = BASE_DIR / "extensions"

# Files
DASHBOARD_FILE = DATA_DIR / "dashboard.json"
TASKS_FILE = DATA_DIR / "tasks.json"
SESSIONS_DIR = DATA_DIR / "sessions"

# Agent
PI_COMMAND = "pi"
SYSTEM_SKILL = SKILLS_DIR / "_system.md"
DASHBOARD_EXTENSION = EXTENSIONS_DIR / "dashboard-tools.ts"
