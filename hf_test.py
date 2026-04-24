import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# load .env explicitly
load_dotenv(dotenv_path=Path(".env").resolve())

HF_TOKEN = os.getenv("HF_TOKEN")
MODEL = os.getenv("LLAMA_MODEL") or "google/gemma-2-2b-it"

print("HF token present:", bool(HF_TOKEN))
print("Model:", MODEL)

url = "https://router.huggingface.co/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json",
}

payload = {
    "model": MODEL,
    "messages": [
        {"role": "user", "content": "Reply with exactly HELLO_OK"}
    ],
    "max_tokens": 20,
}

try:
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    print("status:", r.status_code)
    print("body:", r.text[:2000])
except Exception as e:
    print("Exception:", repr(e))