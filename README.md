# image edit (and not only) bot for openwebui

This is a simple bot for openwebui that allows you to create a channel-wrapper around any ComfyUI workflow that has one prompt or one image input, and one image output

Based on two examples: [open-webui/bot](https://github.com/open-webui/bot) and [websockets_api_example.py](https://github.com/comfyanonymous/ComfyUI/blob/master/script_examples/websockets_api_example.py)

How to set it up:
- enable channels in openwebui's admin setting
- create an account with admin rights for your bot
- create a channel with your desired name, e.g. `qwen-image-edit`. Make it public or private for the same group where are both you and bot
- have a working comfy ui with your workflow. I assume you already have it
- put text `prompt here` as a prompt (the bot will find it by this text and replace with proper prompt)
- remove all preview images and similar, you need to have only one image out
- export it for API, and put the json file inside bot's `workflows` directory
- set up .env file
- run the bot (python main.py), openwebui and comfyui
