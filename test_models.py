import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    
    # List available models
    models = genai.list_models()
    print("Available models:")
    for model in models:
        print(f"- {model.name}")
        if 'generateContent' in model.supported_generation_methods:
            print(f"  SUPPORTS generateContent")
else:
    print("GEMINI_API_KEY not found in .env")