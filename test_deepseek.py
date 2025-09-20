import requests
import os
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
print(f"API Key: {DEEPSEEK_API_KEY[:10]}...")  # Show first 10 chars

def test_deepseek():
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 0.7,
        "max_tokens": 50
    }
    
    try:
        print("Testing DeepSeek API...")
        response = requests.post(
            "https://api.deepseek.com/chat/completions",  # CORRECTED URL
            json=data, 
            headers=headers,
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result['choices'][0]['message']['content']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_deepseek()