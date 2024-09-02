import os
import re
import json
import aiohttp
import asyncio
from pathlib import Path
from nltk import sent_tokenize
from dotenv import load_dotenv
from datetime import datetime
from telegram import Bot
from modules.hyperdb import HyperDB
from modules.gcalendar import get_event
from modules.weather import get_weather

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
HOST_NAME = os.getenv("LLM_HOST")
URI = f"http://{HOST_NAME}/v1/chat/completions"
bot = Bot(BOT_TOKEN)

# TODO: Separate context into parts, each part responsible for a task
# 1. Module context - Module Selection
#   i)   Conversation & Topic Selection -> Memory Query
#   ii)  Image context - Image Prompt & Generation -> Stable Diffusion Model Query
#   iii) Calendar context - Event Reminder -> Google Calendar Query (Get Date from User Input)
# 2. Replace placeholder in main context with module prompt result 

with open("character.json", encoding="utf-8") as file:
    character = json.load(file)

    CHAR_NAME = character["name"]
    desc = character["description"]

    MAIN_CMD = character["main_cmd"]
    MODULE_CMD = character["module_cmd"]

    MAIN_TEMPLATE = character["main_template"]
    MODULE_TEMPLATE = character["module_template"]

    main_ctx = character["main_context"]
    module_ctx = character["module_context"]

USER = "sorakee"
# TEMPLATE = "ChatML"
TEMPLATE = "Vicuna-v1.1"
DB_PATH = "db/hikari.pickle.gz"
VERBOSE = True

short_mem = []
module_mem = []
long_mem = HyperDB()
if Path(DB_PATH).is_file():
    long_mem.load(DB_PATH)

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
                    print("##########\n")
                    print(f"{hikari_msg["choices"][0]["message"]["content"]}\n")
                    print("##########\n")

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
    # msg_date: str = user_item["datetime"].strftime("%d %B %Y, %I:%M %p")

    curr_date = f"Today's date and time is {datetime.now().strftime("%d %B %Y, %I:%M %p")}"
    curr_ctx = f"{desc}\n\n{module_ctx}\n\n{curr_date}"
    
    short_mem.append({"role": "user", "content": user_msg})
    module_mem.append({"role": "user", "content": user_msg})
    result = ""

    # Checks if model 'MODULE' response meets the specified pattern
    # Example: MODULE = Conversation. Topic = Food.
    # Any additional text after the second full stop is ignored.
    while True:
        result = await infer_model(
            curr_ctx, 
            MODULE_CMD, 
            MODULE_TEMPLATE, 
            module_mem,
            0.7, 1.1)
        result = f"MODULE = {result}"

        pattern = r"MODULE\s*=\s*(\w+)\.\s*(Topic|Date|Description)\s*=\s*([^.]+)"
        match = re.search(pattern, result)

        try:
            module_name = match.group(1)
        except AttributeError:
            pass

        if match and module_name in valid_modules:
            # result[0] - Module Name
            # result[1] - Topic/Date/Description
            # result[2] - Text related to result[1]
            result = [match.group(1), match.group(2), match.group(3).strip()]
            break

        module_mem.pop()

    module_result = ""
    if result[0] == "Conversation":
        queries = long_mem.query(user_msg)
        for q in queries:
            module_result += f"{q}\n"
    elif result[0] == "Calendar":
        events = get_event(result[2])
        module_result = events
    elif result[0] == "Weather":
        weather = await get_weather(result[2])
        module_result = weather
    # elif result[0] == "Image"
    #     img = generate_img(result[1])

    if VERBOSE:
        print("\n##########")
        print(f"MODULE PROMPT RESULT:\nMODULE = {result[0]}. {result[1]} = {result[2]}.")
        print(f"{result[0]} PROMPT RESULT:\n{module_result}")
        print("##########\n")

    if len(short_mem) > 10:
        docs = []
        for _ in range(5):
            pop_mem = short_mem.pop(0)
            sender = USER if pop_mem["role"] == "user" else CHAR_NAME
            msg = f"{sender}: {pop_mem["content"]}"
            docs.append(msg)
        long_mem.add_documents(docs)
        long_mem.save(DB_PATH)

    curr_ctx = f"{desc}\n\n{main_ctx}\n\n{curr_date}"
    curr_ctx += "\n{{char}} may use the following information below to come up with a reply:"
    curr_ctx += f"\n{module_result}"
    result = await infer_model(curr_ctx, MAIN_CMD, MAIN_TEMPLATE, short_mem)
    # The AI likes to say nya for some reason.
    # Replace 'nya' to 'meow' before translating to JP for TTS
    result = re.sub(r"\bnya\b", "meow", result, flags=re.IGNORECASE)

    # Splits generated result into a list of sentences
    result = sent_tokenize(result)

    for msg in result:
        await bot.send_message(sender_id, msg)
        await asyncio.sleep(1.5)
    
    message_queue.pop(0)


async def check_inactivity():
    return