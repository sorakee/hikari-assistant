import os
import json
import asyncio
import requests
from dotenv import load_dotenv
from datetime import datetime
from telegram import Bot

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(BOT_TOKEN)
URI = "http://127.0.0.1:5000/v1/chat/completions"

with open("character.json") as file:
    character = json.load(file)
    verbose: bool = False
    CHAR_NAME: str = character["name"]
    GREETING: str = character["greeting"]
    instruct_cmd: str = character["instruct_cmd"]
    context: str = character["context"]

USER: str = "sorakee"
memory = [{"role": "assistant", "content": GREETING}] if GREETING != "" else []


# Process user's message
async def process_message(sender_id, message_queue):
    # Retrieve the first item in queue
    user_item = message_queue[0]
    user_msg: str = user_item["message"]
    msg_date: datetime = user_item["datetime"]
    msg_date_str: str = msg_date.strftime("%m/%d/%Y, %H:%M:%S")

    memory.append({"role": "user", "content": user_msg})

    headers = {
        "Content-Type": "application/json"
    }

    body = {
        "messages": memory,
        "user": USER,
        "mode": "chat-instruct",
        "character": CHAR_NAME,
        "context": context,
        "chat_instruct_command": instruct_cmd
    }
    
    # THIS IS BLOCKING THE CODE >:(
    response = requests.post(URI, headers=headers, json=body, verify=False)
    hikari_msg = ""
        
    if response.status_code == 200:
        if verbose:
            print(response.json(), "\n")

        hikari_msg = response.json()["choices"][0]["message"]["content"]
        memory.append({"role": "assistant", "content": hikari_msg})
    else:
        hikari_msg = "ERROR: Please try again. Sorry!"
    
    await bot.send_message(sender_id, hikari_msg)
    message_queue.pop(0)


async def check_inactivity():
    return