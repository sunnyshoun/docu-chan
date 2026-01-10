import json

def save_plan(filepath: str, contents: dict):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(json.dumps(contents, indent=2))