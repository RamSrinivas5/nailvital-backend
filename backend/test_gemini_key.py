import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

def test_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    try:
        print("Testing models/gemini-2.0-flash with new key...")
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        response = model.generate_content("Say hello!")
        print(f"Response: {response.text}")
        print("Success!")
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    test_gemini()
