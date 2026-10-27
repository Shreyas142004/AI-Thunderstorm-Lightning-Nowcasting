import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import urllib.request
import urllib.error
from config import GEMINI_API_KEY

print("Testing Gemini API with key prefix:", GEMINI_API_KEY[:6])

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
try:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print("Available models:")
        for m in data.get("models", []):
            if "generateContent" in m.get("supportedGenerationMethods", []):
                print(" -", m.get("name"))
except Exception as e:
    print("List models failed:", e)
