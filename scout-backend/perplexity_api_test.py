import os
import requests
from dotenv import load_dotenv
from config.settings import settings

# Load environment variables
load_dotenv()

def test_perplexity_api():
    api_key = getattr(settings, "perplexity_api_key", None) or os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("PERPLEXITY_API_KEY not set in settings or environment.")
        return
    print(f"Using Perplexity API key: {api_key[:4]}...{api_key[-4:]}")
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "sonar",
        "messages": [{"role": "user", "content": "What is the capital of France?"}]
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        print("Status code:", response.status_code)
        print("Response:", response.text)
    except Exception as e:
        print("Error calling Perplexity API:", e)

if __name__ == "__main__":
    test_perplexity_api()
