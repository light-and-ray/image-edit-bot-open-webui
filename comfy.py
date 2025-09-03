import websocket #NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
import uuid
import json
import urllib.request
import urllib.parse
from PIL import Image
import io
from env import COMFY_ADDRESS
from utils import get_image_hash
import requests

client_id = str(uuid.uuid4())

def queue_prompt(prompt, prompt_id):
    p = {"prompt": prompt, "client_id": client_id, "prompt_id": prompt_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request("http://{}/prompt".format(COMFY_ADDRESS), data=data)
    urllib.request.urlopen(req).read()

def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(COMFY_ADDRESS, url_values)) as response:
        return response.read()

def get_history(prompt_id):
    with urllib.request.urlopen("http://{}/history/{}".format(COMFY_ADDRESS, prompt_id)) as response:
        return json.loads(response.read())

def get_images(ws, prompt):
    prompt_id = str(uuid.uuid4())
    queue_prompt(prompt, prompt_id)
    output_images = {}
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break #Execution is done

    history = get_history(prompt_id)[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        images_output = []
        if 'images' in node_output:
            for image in node_output['images']:
                image_data = get_image(image['filename'], image['subfolder'], image['type'])
                images_output.append(image_data)
        output_images[node_id] = images_output

    return output_images


def upload_image_to_comfy(pil_image: Image.Image, filename_prefix: str = "pil_upload"):
    if not isinstance(pil_image, Image.Image):
        return False, "Error: Input must be a Pillow Image object."
    url = f"http://{COMFY_ADDRESS}/upload/image"
    filename = f"{filename_prefix}_{get_image_hash(pil_image)}.png"
    image_stream = io.BytesIO()
    pil_image.save(image_stream, format='PNG')
    image_stream.seek(0)
    files = {'image': (filename, image_stream, 'image/png')}

    try:
        response = requests.post(url, files=files)
        response.raise_for_status()
        try:
            response_data = response.json()
            return True, response_data
        except json.JSONDecodeError:
            return False, f"Error: Failed to decode JSON from response. Response content: {response.text}"

    except requests.exceptions.RequestException as e:
        return False, f"Error during image upload: {e}"


def processComfy(workflowName: str, prompt: str = None, image: Image.Image = None) -> Image.Image:
    with open(f"workflows/{workflowName}.json") as f:
        workflow: dict = json.loads(f.read())

    for node in workflow.values():
        if node["class_type"] == "LoadImage":
            if not image:
                raise Exception("image is required")
            success, data = upload_image_to_comfy(image, workflowName)
            print(data)
            if not success:
                raise Exception(data)
            node["inputs"]["image"] = data["name"]
            break

    for node in workflow.values():
        for promptKey in ("text", "prompt"):
            try:
                text: str = node["inputs"][promptKey]
                text = text.strip().lower()
                if text == "prompt here":
                    if not prompt:
                        raise Exception("prompt is required")
                    node["inputs"][promptKey] = prompt
                    break
            except KeyError:
                pass

    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(COMFY_ADDRESS, client_id))
    nodes = get_images(ws, workflow)
    ws.close()
    images = []

    for node_id in nodes:
        for image_data in nodes[node_id]:
            image = Image.open(io.BytesIO(image_data))
            images.append(image)

    if len(images) < 1:
        raise Exception(f"No image output found in the workflow {workflowName}")
    elif len(images) > 1:
        raise Exception(f"More then 1 image output found in the workflow {workflowName}")

    return images[0]


