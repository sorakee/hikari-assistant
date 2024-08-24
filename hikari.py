import os
import re
import json
import aiohttp
import asyncio
import random
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

with open("character.json", encoding="utf-8") as file:
    character = json.load(file)
    CHAR_NAME = character["name"]
    INSTRUCT_CMD = character["instruct_cmd"]
    MODULE_CMD = character["module_cmd"]
    MODULE_TEMPLATE = character["module_template"]
    desc = character["description"]
    module_ctx = character["module_context"]
    main_ctx = character["main_context"]

USER = "sorakee"
# TEMPLATE = "ChatML"
TEMPLATE = "Vicuna-v1.1"
VERBOSE = True
short_mem = []
module_mem = []
valid_modules = ["Conversation", "Calendar", "Weather", "Image"]


async def infer_model(
        context: str,
        command: str,
        chat_template: str,
        memory: list,
        tp: float=1.0,
        repeat_penalty: float=1.0
    ) -> str:
    """
    Sends a prompt to the model through an HTTP POST request to a specified API endpoint.
    
    Parameters
    ----------
    context: str
        The context of the prompt, which includes the AI's personality,
        few-shot examples, instructions and any other additional information.
    command: str
        The instruction command, which will be followed by the AI.
    chat_template: str
    memory: list
        A list of dicts (dialogue history between the roles 'user' and 'assistant').
    tp: float
        Temperature. 
        This parameter determines whether the output is more random and creative
        or more predictable.
    repeat_penalty: float
        This parameter determines how much you want to penalize the AI when it 
        repeats text.
    
    Returns
    -------
    str
        The output of the large language model
    """

    headers = {
        "Content-Type": "application/json"
    }

    body = {
        "messages": memory,
        "name1": USER,
        "mode": "chat-instruct",
        "character": CHAR_NAME,
        "context": context,
        "chat_instruct_command": command,
        "instruction_template": TEMPLATE,
        "chat_template_str": chat_template,
        "temperature": tp,
        "repetition_penalty": repeat_penalty
    }

    hikari_msg = ""
    
    async with aiohttp.ClientSession() as session:
        async with session.post(URI, json=body, headers=headers) as resp:
            if resp.status == 200:
                hikari_msg = await resp.json()

                if VERBOSE:
                    print(hikari_msg["choices"][0]["message"]["content"])

                hikari_msg = hikari_msg["choices"][0]["message"]["content"]
                memory.append({"role": "assistant", "content": hikari_msg})
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
    msg_date: str = user_item["datetime"].strftime("%d %B %Y, %H:%M:%S")

    curr_date = f"Today's date and time is {datetime.now().strftime("%d %B %Y, %H:%M:%S")}"
    curr_ctx = f"{desc}\n\n{module_ctx}\n\n{curr_date}"
    
    short_mem.append({"role": "user", "content": user_msg})
    module_mem.append({"role": "user", "content": user_msg})
    result = ""

    # Checks if model 'MODULE' response meets the specified pattern
    # Example: MODULE = Conversation. Topic = Food.
    # Any additional text after the second full stop is ignored.
    while True:
        result = await infer_model(curr_ctx, 
                                   MODULE_CMD, 
                                   MODULE_TEMPLATE, 
                                   module_mem, 
                                   0.7, 
                                   1.1)
        result = f"MODULE = {result}"

        pattern = r"MODULE\s*=\s*(\w+)\.\s*(Topic|Date|Description)\s*=\s*([^.]+)"
        match = re.search(pattern, result)
        module_name = match.group(1)
        if match and module_name in valid_modules:
            # result[0] - Module Name
            # result[1] - Topic/Date/Description
            # result[2] - Text related to result[1]
            result = [match.group(1), match.group(2), match.group(3).strip()]
            break

        module_mem.pop()

    result = f"MODULE = {result[0]}. {result[1]} = {result[2]}."
    
    # if result[0] == "Conversation":
    #     long_mem = query_vdb(result[1])
    # elif result[0] == "Calendar":
    #     events = query_calendar(result[1])
    # elif result[0] == "Weather":
    #     weather = query_weather(result[1])
    # elif result[0] == "Image"
    #     img = generate_img(result[1])

    # Splits generated result into a list of sentences
    result = sent_tokenize(result)

    for msg in result:
        await bot.send_message(sender_id, msg)
        await asyncio.sleep(1.5)
    
    message_queue.pop(0)


async def check_inactivity():
    return