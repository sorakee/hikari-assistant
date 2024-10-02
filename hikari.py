import os
import re
import json
import emoji
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
from modules.translate import translate
from modules.voicevox_tts import synthesize_voice
from modules.imagegen import generate_img
from telegram import error

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
HOST_NAME = os.getenv("LLM_HOST")
TTS_ENABLED = os.getenv("TTS_ENABLED").lower() == "true"
TTS_LANG = os.getenv("TTS_LANG")
VOICE_TTS = os.getenv("TTS_PATH")
IMG_PATH = os.getenv("IMAGE_PATH")
TL_ENABLED = os.getenv("TL_ENABLED").lower() == "true"
USER = os.getenv("USER")
TEMPLATE = os.getenv("LLM_TEMPLATE")
DB_PATH = os.getenv("DB_PATH")
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
    CHAR_DESC = character["description"]
    SYS_NAME = character["sys_name"]

    MAIN_CMD = character["main_cmd"]
    MODULE_CMD = character["module_cmd"]

    MAIN_TEMPLATE = character["main_template"]
    MODULE_TEMPLATE = character["module_template"]

    main_ctx = character["main_context"]
    module_ctx = character["module_context"]


VERBOSE = True
short_mem = []
module_mem = []
long_mem = HyperDB()
if Path(DB_PATH).is_file():
    long_mem.load(DB_PATH)


async def infer_model(
        context: str,
        char: str,
        command: str,
        chat_template: str,
        memory: list,
        tp: float=1.0,
        repeat_penalty: float=1.0,
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

    # body = {
    #     "messages": memory,
    #     "name1": USER,
    #     "mode": "chat-instruct",
    #     "character": char,
    #     "context": context,
    #     "chat_instruct_command": command,
    #     "instruction_template": TEMPLATE,
    #     "chat_template_str": chat_template,
    #     "temperature": tp,
    #     "repetition_penalty": repeat_penalty
    # }
    
    body = {
        "messages": memory,
        "name1": USER,
        "mode": "chat-instruct",
        "character": char,
        "context": context,
        "chat_instruct_command": command,
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
                # Remove any action text surrounded by asterisks (e.g. *gasp*)
                # hikari_msg = re.sub(r'\*.*?\*', '', hikari_msg).strip()
                hikari_msg = re.sub(r"\bnya\b", "meow", hikari_msg, flags=re.IGNORECASE)
                hikari_msg = emoji.replace_emoji(hikari_msg, replace="").strip()
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
    curr_ctx = f"{CHAR_DESC}\n\n{module_ctx}\n\n{curr_date}"
    curr_ctx += "\n{{char}} may use the following information below to come up with a MODULE selection:"
    for i in [-2, -1]:
        if len(short_mem) > 2:
            sender = USER if short_mem[i]["role"] == "user" else CHAR_NAME   
            curr_ctx += f"\n{sender}: {short_mem[i]["content"]}"
        else:
            curr_ctx += "\nNone"
            break
    
    short_mem.append({"role": "user", "content": user_msg})
    module_mem.append({"role": "user", "content": user_msg})
    result = ""

    # Checks if model 'MODULE' response meets the specified pattern
    # Example: MODULE = Conversation. Topic = Food.
    # Any additional text after the second full stop is ignored.
    while True:
        result = await infer_model(
            curr_ctx, 
            SYS_NAME,
            MODULE_CMD, 
            MODULE_TEMPLATE, 
            module_mem,
            1.0, 1.1
        )
        result = f"MODULE = {result}"

        pattern = r"MODULE\s*=\s*(Calendar|Image|Weather|Conversation)\.\s*(Date\s*=\s*([^\n.]+)|Description\s*=\s*([^\n.]+)|Tags\s*=\s*([^\n.]+))?"
        match = re.search(pattern, result)

        
        if match:
            # result[0] - Module Prompt
            # result[1] - Module Name
            # result[2] - Date/Description/Tags
            result = [match.group(0), match.group(1)]
            if match.group(3):  # If Date matched
                result.append(match.group(3).strip())
            elif match.group(4):  # If Description matched
                result.append(match.group(4).strip())
            elif match.group(5):  # If Tags matched
                result.append(match.group(5).strip())
            break

        module_mem.pop()

    module_result = ""
    if result[1] == "Conversation":
        queries = long_mem.query(user_msg, return_similarities=False)
        for q in queries:
            module_result += f"{q}\n"
    elif result[1] == "Calendar":
        events = get_event(result[2])
        module_result = events
    elif result[1] == "Weather":
        weather = await get_weather(result[2])
        module_result = weather
    elif result[1] == "Image":
        img = generate_img(result[2])
        photo_sent = False
        sent_attempt = 0
        while not photo_sent:
            try:
                if sent_attempt == 3:
                    await bot.send_message(
                        sender_id,
                        "<i>Image generation failed.</i>",
                        "html"
                    )
                    await bot.send_message(
                        sender_id,
                        f"<i>Expected Image's Description: {result[2]}.</i>",
                        "html"
                    )
                    break
                await bot.send_photo(sender_id, IMG_PATH)
                module_result = f"Description of image sent by {{{{char}}}}: {result[2]}"
                photo_sent = True
            except error.TimedOut:
                sent_attempt += 1
                continue
            

    if VERBOSE:
        print("\n##########")
        print(f"MODULE PROMPT:\n{result[0]} ")
        print(f"{result[1]} PROMPT RESULT:\n{module_result}")
        print("##########\n")

    # Remove parts of short-term memory and save it in the vector database
    if len(short_mem) > 10:
        docs = []
        for _ in range(5):
            pop_mem = short_mem.pop(0)
            sender = USER if pop_mem["role"] == "user" else CHAR_NAME
            msg = f"{sender}: {pop_mem["content"]}"
            docs.append(msg)
        long_mem.add_documents(docs)
        long_mem.save(DB_PATH)

    curr_ctx = f"{CHAR_DESC}\n\n{main_ctx}\n\n{curr_date}"
    curr_ctx += "\n{{char}} may use the following information below to come up with a reply if it is related to {{user}}'s message:"
    curr_ctx += f"\n{module_result if module_result else "None"}"
    result = await infer_model(curr_ctx, CHAR_NAME, MAIN_CMD, MAIN_TEMPLATE, short_mem)

    translation = translate(result) if TL_ENABLED else False
    if VERBOSE and translation:
        print("\n##########")
        print("Translation succesful!")
        print(f"Translation: {translation}")
        print("Attempting to synthesize voice...")
        print("##########\n")
    tts = await synthesize_voice(translation, TTS_LANG) if TTS_ENABLED and translation else False

    # Splits generated result into a list of sentences
    result = sent_tokenize(result)
    for msg in result:
        await bot.send_message(sender_id, msg)
        await asyncio.sleep(1.5)
    if tts:
        if VERBOSE:
            print("\n##########")
            print("Sending voice...")
            print("##########\n")
        voice_sent = False
        sent_attempt = 0
        while not voice_sent:
            try:
                if sent_attempt == 3:
                    await bot.send_message(
                        sender_id,
                        "<i>TTS generation failed. Skipping...</i>",
                        "html"
                    )
                    break
                await bot.send_voice(sender_id, VOICE_TTS)
                voice_sent = True
            except error.TimedOut:
                sent_attempt += 1
                continue
    
    print("Message process success!")
    print("Removing message from queue...")
    message_queue.pop(0)


async def check_inactivity():
    return