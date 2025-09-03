import asyncio
import socketio
from env import WEBUI_URL, TOKEN, MAP_CHANNEL_NAME_WORKFLOW
from utils import send_message, send_typing, base64_url_to_pil, send_image
from comfy import processComfy

sio = socketio.AsyncClient(logger=False, engineio_logger=False)


@sio.event
async def connect():
    print("Connected!")


@sio.event
async def disconnect():
    print("Disconnected from the server!")


# Define a function to handle channel events
def events(user_id):
    @sio.on("channel-events")
    async def channel_events(data):
        if data["user"]["id"] == user_id:
            # Ignore events from the bot itself
            return

        async def print_error(e):
            text = str(type(e).__name__) + ": " + str(e)
            print(text)
            await send_message(data["channel_id"], text)

        if data["data"]["type"] == "message":
            workflow = None
            if "channel" in data.keys():
                workflow = MAP_CHANNEL_NAME_WORKFLOW.get(data["channel"]["name"])

            if workflow:
                print(f"Processing workflow: {workflow}")
                await send_typing(sio, data["channel_id"])
                prompt = data["data"]["data"]["content"]
                image = None
                try:
                    file = data["data"]["data"]["data"]["files"][0]
                    if file["type"] == "image":
                        try:
                            image = base64_url_to_pil(file["url"])
                        except Exception as e:
                            await print_error(e)
                except IndexError:
                    pass

                await send_message(data["channel_id"], "Processing...")
                try:
                    newImage = await asyncio.to_thread(lambda: processComfy(workflow, prompt=prompt, image=image))
                    await send_image(data["channel_id"], "Done", newImage)
                except Exception as e:
                    await print_error(e)
                    # raise


async def main():
    try:
        print(f"Connecting to {WEBUI_URL}...")
        await sio.connect(
            WEBUI_URL, socketio_path="/ws/socket.io", transports=["websocket"]
        )
        print("Connection established!")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    # Callback function for user-join
    async def join_callback(data):
        events(data["id"])  # Attach the event handlers dynamically

    # Authenticate with the server
    await sio.emit("user-join", {"auth": {"token": TOKEN}}, callback=join_callback)

    # Wait indefinitely to keep the connection open
    await sio.wait()


async def forever_main():
    while True:
        await main()
        await asyncio.sleep(3)


if __name__ == "__main__":
    while True:
        asyncio.run(main=forever_main())
