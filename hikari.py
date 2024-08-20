import os
import json
import aiohttp
import asyncio
from nltk import sent_tokenize
from dotenv import load_dotenv
from datetime import datetime
from telegram import Bot

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(BOT_TOKEN)
URI = "http://127.0.0.1:5000/v1/chat/completions"

# TODO: Separate context into parts, each part responsible for a task
# 1. module-context - Module Selection
# 2. conversation-context - Conversation & Topic Selection -> Memory Query
# 3. image-context - Image Prompt & Generation -> Stable Diffusion Model Query
# 4. calendar-context - Event Reminder -> Google Calendar Query (Get Date from User Input)

with open("character.json") as file:
    character = json.load(file)
    verbose: bool = False
    CHAR_NAME: str = character["name"]
    GREETING: str = character["greeting"]
    instruct_cmd: str = character["instruct_cmd"]
    context: str = character["context"]

USER: str = "sorakee"
# Nous-Hermes-SOLAR
TEMPLATE: str = "ChatML"
# Wizard-Vicuna
# TEMPLATE: str = "Vicuna-v1.1"
memory = [{"role": "assistant", "content": GREETING}] if GREETING != "" else []
current_date = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")


# Process user's message
async def process_message(sender_id, message_queue):
    # Retrieve the first item in queue
    user_item = message_queue[0]
    user_msg: str = user_item["message"]
    msg_date: datetime = user_item["datetime"]
    msg_date_str: str = msg_date.strftime("%d/%m/%Y, %H:%M:%S")

    context_with_date = "Today's date is " + current_date + ".\n\n" + context
    memory.append({"role": "user", "content": user_msg})

    headers = {
        "Content-Type": "application/json"
    }

    body = {
        "messages": memory,
        "name1": USER,
        "mode": "chat-instruct",
        "character": CHAR_NAME,
        "context": context_with_date,
        "chat_instruct_command": instruct_cmd,
        "instruction_template": TEMPLATE
    }

    hikari_msg = ""
    
    async with aiohttp.ClientSession() as session:
        response = await session.post(URI, json=body, headers=headers)
    
        if response.status == 200:
            if verbose:
                print(response.json(), "\n")

            hikari_msg = await response.json()
            hikari_msg = hikari_msg["choices"][0]["message"]["content"]
            memory.append({"role": "assistant", "content": hikari_msg})
        else:
            hikari_msg = "ERROR: Please try again. Sorry!"
    
    hikari_msg = sent_tokenize(hikari_msg)

    for msg in hikari_msg:
        await bot.send_message(sender_id, msg)
        await asyncio.sleep(1)
    
    message_queue.pop(0)


async def check_inactivity():
    return