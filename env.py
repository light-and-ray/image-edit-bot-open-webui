import os, json

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("dotenv not installed, skipping...")

WEBUI_URL = os.getenv("WEBUI_URL", "http://localhost:8080")
TOKEN = os.getenv("TOKEN", "")
COMFY_ADDRESS = os.getenv("COMFY_ADDRESS", "localhost:8188")
MAP_CHANNEL_NAME_WORKFLOW = os.getenv("MAP_CHANNEL_NAME_WORKFLOW", '{"qwen-image-edit": "qwen_image_edit.json"}')
LAZY_IMAGE_URLS = os.getenv("LAZY_IMAGE_URLS", "0").strip() != "0"


COMFY_ADDRESS = COMFY_ADDRESS.lower().removesuffix('/').removeprefix("http://")
MAP_CHANNEL_NAME_WORKFLOW = json.loads(MAP_CHANNEL_NAME_WORKFLOW)
