import json


def handler(event, context):
    with open("config.json", "rb") as f:
        config = json.load(f)
    return config.get("version")
