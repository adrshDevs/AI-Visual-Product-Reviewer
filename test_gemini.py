import os
from dotenv import load_dotenv
from google import genai

load_dotenv(".env", override=True)

key = os.getenv("GEMINI_API_KEY", "").strip()

print("Key loaded:", bool(key))
print("Key prefix:", key[:8])
print("Key length:", len(key))

client = genai.Client(api_key=key)

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Say hello"
)

print(response.text)