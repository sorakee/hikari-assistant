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
    CHAR_NAME = character["name"]
    INSTRUCT_CMD = character["instruct_cmd"]
    MODULE_CMD = character["module_cmd"]
    desc = character["description"]
    module_ctx = character["module_context"]
    main_ctx = character["main_context"]

USER = "sorakee"
TEMPLATE = "ChatML"
VERBOSE = False
short_mem = []


async def infer_model(context: str, command: str, tp: float=1.0) -> str:
    """
    Sends a prompt to the model through a POST request to a specified API endpoint.
    
    Parameters
    ----------
    context: str
        The context of the prompt, which includes the AI's personality,
        few-shot examples, instructions and any other additional information.
    command: str
        The instruction command, which will be followed by the AI.
    tp: float
        This parameter determines whether the output is more random and creative
        or more predictable.
    
    Returns
    -------
    str
        The output of the large language model
    """

    headers = {
        "Content-Type": "application/json"
    }

    body = {
        "messages": short_mem,
        "name1": USER,
        "mode": "chat-instruct",
        "character": CHAR_NAME,
        "context": context,
        "chat_instruct_command": command,
        "instruction_template": TEMPLATE,
        "temperature": tp
    }

    hikari_msg = ""
    
    async with aiohttp.ClientSession() as session:
        async with session.post(URI, json=body, headers=headers) as resp:
            if resp.status == 200:
                hikari_msg = await resp.json()

                if VERBOSE:
                    print(hikari_msg)

                hikari_msg = hikari_msg["choices"][0]["message"]["content"]
                short_mem.append({"role": "assistant", "content": hikari_msg})
            else:
                hikari_msg = "ERROR: Please try again. Sorry!"

    return hikari_msg


async def process_message(sender_id: int, message_queue: list):
    """
    Process user's message that is in the message queue
    
    Parameters
    ----------
    sender_id : int
        The id of the sender
    message_queue : list
        The queue, consisting of user's message.
    
    Returns
    -------
    None

    Description
    -----------
    This function adds current date and time to the AI's context.
    It then sends a module selection prompt to the LLM, which returns
    four possible outcomes - Conversation, Calendar, Image Generation, Weather.
    Based on the outcome, this function will call a relevant function, which
    returns a string to provide additional context to the main prompt.
    """
    
    user_item = message_queue[0]
    user_msg: str = user_item["message"]
    msg_date: datetime = user_item["datetime"]
    msg_date_str: str = msg_date.strftime("%d/%m/%Y, %H:%M:%S")

    curr_date = f"Today's date is {datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}"
    curr_ctx = f"{curr_date}\n\n{desc}\n\n{module_ctx}"
    short_mem.append({"role": "user", "content": user_msg})

    # Splits generated result into a list of sentences
    result = await infer_model(curr_ctx, MODULE_CMD)
    result = sent_tokenize(result)

    for msg in result:
        await bot.send_message(sender_id, msg)
        await asyncio.sleep(1.5)
    
    message_queue.pop(0)


async def check_inactivity():
    return