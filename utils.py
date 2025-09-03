import aiohttp
import socketio
import base64, io
from env import WEBUI_URL, TOKEN
from PIL import Image
import hashlib


async def send_message(channel_id: str, message: str):
    url = f"{WEBUI_URL}/api/v1/channels/{channel_id}/messages/post"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    data = {"content": str(message)}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status != 200:
                # Raise an exception if the request fails
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=await response.text(),
                    headers=response.headers,
                )
            # Return response JSON if successful
            return await response.json()


async def send_image(channel_id: str, text: str, image: Image.Image|str):
    url = f"{WEBUI_URL}/api/v1/channels/{channel_id}/messages/post"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if not isinstance(image, str):
        image = pil_to_base64_url(image)
    data = {"content": text, "data": {"files": [{"type": "image", "url": image}]}}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status != 200:
                # Raise an exception if the request fails
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=await response.text(),
                    headers=response.headers,
                )
            # Return response JSON if successful
            return await response.json()


async def send_typing(sio: socketio.AsyncClient, channel_id: str):
    await sio.emit(
        "channel-events",
        {
            "channel_id": channel_id,
            "data": {"type": "typing", "data": {"typing": True}},
        },
    )


def base64_url_to_pil(base64_url: str) -> Image.Image:
    """
    Converts a Base64-encoded data URL string to a PIL Image object.

    Args:
        base64_url: The Base64-encoded image URL string, typically starting with
                    "data:image/png;base64," or similar.

    Returns:
        A PIL Image.Image object.

    Raises:
        ValueError: If the input string is not a valid Base64 data URL.
        Exception: For any other errors during decoding or image opening.
    """
    if not isinstance(base64_url, str):
        raise TypeError("Input must be a string.")

    # Find the comma that separates the header from the data
    try:
        header, data = base64_url.split(',', 1)
        # Check for a valid Base64 header
        if not header.startswith('data:image/') or not header.endswith(';base64'):
            raise ValueError("Invalid Base64 data URL format.")
    except ValueError:
        raise ValueError("Invalid Base64 data URL format. Missing comma.")

    try:
        # Decode the Base64 string to bytes
        image_bytes = base64.b64decode(data)
        # Use BytesIO to read the bytes as an in-memory file
        image_stream = io.BytesIO(image_bytes)
        # Open the image stream with PIL and return the Image object
        pil_image = Image.open(image_stream)
        return pil_image
    except base64.binascii.Error as e:
        raise ValueError(f"Invalid Base64 string: {e}")
    except Exception as e:
        # Catch other potential errors like invalid image format
        raise Exception(f"Failed to open image from Base64 data: {e}")


def pil_to_base64_url(pil_image: Image.Image, image_format: str = "PNG") -> str:
    """
    Converts a PIL Image object to a Base64-encoded data URL string.

    Args:
        pil_image: The PIL Image.Image object to convert.
        image_format: The format of the image to encode (e.g., "PNG", "JPEG").
                      This determines the MIME type in the URL. Defaults to "PNG".

    Returns:
        A Base64-encoded image URL string.

    Raises:
        TypeError: If the input is not a PIL Image object.
        ValueError: If the specified image format is invalid.
    """
    if not isinstance(pil_image, Image.Image):
        raise TypeError("Input must be a PIL Image object.")

    # Use BytesIO to create an in-memory file buffer
    image_stream = io.BytesIO()

    try:
        # Save the PIL image to the in-memory buffer
        pil_image.save(image_stream, format=image_format)
    except Exception as e:
        raise ValueError(f"Failed to save image in '{image_format}' format: {e}")

    # Get the bytes from the buffer
    image_bytes = image_stream.getvalue()
    # Encode the bytes to a Base64 string
    base64_encoded_string = base64.b64encode(image_bytes).decode('utf-8')
    # Construct the final data URL string
    return f"data:image/{image_format.lower()};base64,{base64_encoded_string}"


def get_image_hash(image: Image.Image) -> str:
    """
    Generates a SHA-256 hash from a Pillow (PIL) Image object.

    This function hashes the raw pixel data of the image. Any change to the
    image, no matter how small (e.g., one pixel change), will result in a
    completely different hash value. This is useful for verifying image
    integrity and is not a perceptual hash.

    Args:
        image: A Pillow Image object.

    Returns:
        A hexadecimal string representing the SHA-256 hash of the image data.
    """
    # Convert the image to bytes. This gets the raw pixel data.
    image_bytes = image.tobytes()

    # Create a SHA-256 hash object.
    hasher = hashlib.sha256()

    # Update the hash object with the image data.
    hasher.update(image_bytes)

    # Return the hexadecimal representation of the hash.
    return hasher.hexdigest()[:20]


