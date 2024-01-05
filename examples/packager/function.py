import json


def handler(event, context):  # pylint: disable=unused-argument
    with open("config.json", "rb") as f:
        config = json.load(f)
    return config.get("version")
