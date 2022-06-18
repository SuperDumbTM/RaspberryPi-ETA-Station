import os
import json

def get(path: str) -> dict | list:
    with open(path, 'r', encoding="utf-8") as f:
        return json.load(f)
    
def put(path:str, data: dict | list):
    with open(path, 'w', encoding="utf-8") as f:
        return json.dump(data, f)