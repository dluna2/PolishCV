import os
import requests
from pathlib import Path
from dotenv import load_dotenv

print("starting script...")

env_path = Path(".env").resolve()
print("loading env from:", env_path)

load_dotenv(dotenv_path=env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")

print("OpenAI key present:", bool(OPENAI_API_KEY))
print("Model:", OPENAI_MODEL)

url = "https://api.openai.com/v1/responses"
headers = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json",
}
payload = {
    "model": OPENAI_MODEL,
    "input": "Reply with exactly HELLO_OPENAI"
}

print("sending request...")

try:
    r = requests.post(url, headers=headers, json=payload, timeout=15)
    print("status:", r.status_code)
    print("raw body:", r.text[:2000])

    if r.status_code == 200:
        data = r.json()
        extracted_text = None

        for item in data.get("output", []):
            for block in item.get("content", []):
                if block.get("type") == "output_text":
                    extracted_text = block.get("text")
                    break
            if extracted_text:
                break

        print("extracted_text:", extracted_text)

except Exception as e:
    print("Exception:", repr(e))

print("script finished.")