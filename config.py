"""
Configuration and Environment Settings
=====================================
Centralized configuration loader for the Thunderstorm Nowcasting project.
"""

import os
from pathlib import Path

# Project Root Directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file using native standard library (zero-dependency, no red squiggly lines)
def load_env_file(env_path: Path):
    """Load key-value pairs from .env into os.environ."""
    if not env_path.exists():
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip("\"'")
                os.environ.setdefault(key, val)
    except Exception as e:
        print(f"[WARNING] Could not load .env: {e}")

load_env_file(BASE_DIR / ".env")

# API Keys
VISUAL_CROSSING_API_KEY = os.getenv("VISUAL_CROSSING_API_KEY", "")

# Directory Paths
DATASET_DIR = BASE_DIR / "dataset"
PROCESSED_DIR = BASE_DIR / "processed_data"
MODELS_DIR = BASE_DIR / "models"

# Ensure directories exist
for directory in [DATASET_DIR, PROCESSED_DIR, MODELS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


def check_api_key() -> bool:
    """Check if the API key is configured."""
    if not VISUAL_CROSSING_API_KEY or VISUAL_CROSSING_API_KEY == "your_api_key_here":
        print("[WARNING] VISUAL_CROSSING_API_KEY is not configured in .env")
        return False
    return True


if __name__ == "__main__":
    print(f"Project Root: {BASE_DIR}")
    if check_api_key():
        masked_key = VISUAL_CROSSING_API_KEY[:4] + "..." + VISUAL_CROSSING_API_KEY[-4:]
        print(f"[OK] Visual Crossing API Key loaded: {masked_key}")
    else:
        print("[ERROR] Please add your API key to .env")
