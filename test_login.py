import requests
import json
import sys

try:
    url = "http://127.0.0.1:8000/login"
    data = {"username": "test@test.com", "password": "password"}
    res = requests.post(url, data=data)
    print(f"Status Code: {res.status_code}")
    print(res.text)
except Exception as e:
    print(f"Exception: {e}")
