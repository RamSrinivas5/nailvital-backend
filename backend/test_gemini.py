import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Exact config from main.py
model = genai.GenerativeModel('models/gemini-flash-latest', 
    system_instruction="You are NailVital AI, a versatile and intelligent assistant. While you have expertise in nail health and dermatology, you are capable of answering any general-purpose questions from the user across any topic. Provide clear, concise, and helpful responses.")

with open("diagnostic_results.txt", "w") as f:
    try:
        f.write("Test 1: General Query (History)\n")
        res1 = model.generate_content("Who painted the Mona Lisa?")
        f.write(f"Response: {res1.text}\n\n")

        f.write("Test 2: Clinical Query (Nails)\n")
        res2 = model.generate_content("What causes white spots on nails?")
        f.write(f"Response: {res2.text}\n")
    except Exception as e:
        f.write(f"ERROR: {str(e)}\n")
