import requests
import sys

url = "http://127.0.0.1:11434/api/generate"
payload = {
    "model": "qwen2.5-coder:1.5b",
    "prompt": "hi",
    "stream": False
}

print(f"Testing connection to {url}...")
try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json().get('response')}")
except Exception as e:
    print(f"FAILED: {str(e)}")
