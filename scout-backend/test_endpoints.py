#!/usr/bin/env python3
"""
Test script to hit the chat streaming endpoint directly
"""

import requests
import json

def test_chat_stream():
    url = "https://qhmdhagzcw.eu-central-1.awsapprunner.com/api/chat/stream"
    
    payload = {
        "message": "hello",
        "mode": "chat"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"Testing: {url}")
    print(f"Payload: {payload}")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print("-" * 50)
        
        if response.status_code == 200:
            print("Streaming response:")
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    print(f"Received: {line}")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_chat_stream()