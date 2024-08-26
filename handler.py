import os
import json
import emoji
import asyncio
from dotenv import load_dotenv
from hikari import process_message
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, ApplicationHandlerStop

load_dotenv()

CREATOR_ID = int(os.getenv("CREATOR_ID"))
VERBOSE = True

with open("stickers.json") as file:
    STICKERS = json.load(file)


async def handle_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cmds = ["/start", "/stop"]
    user_states = context.user_states
    sender = update.message.from_user

    if VERBOSE:
        print(user_states)

    if update.message.text not in cmds:
        msg = "I'm afraid your command is invalid."
        await context.bot.send_message(sender.id, msg, reply_to_message_id=update.message.id)

    if update.message.text == "/start":
        msg = "Hello~!"
        user_states[sender.id] = {}
        user_states[sender.id]['message_queue'] = []

        await context.bot.send_message(sender.id, msg)
        await context.bot.send_sticker(sender.id, STICKERS["hello"])
    
    if update.message.text == "/stop":
        msg = "Goodbye~!"

        try:  
            del user_states[sender.id]
        except:
            await context.bot.send_message(
                sender.id,
                "<i>Hikari is already asleep!</i>",
                "html"
            )
            return
        
        await context.bot.send_message(sender.id, msg)
        await context.bot.send_sticker(sender.id, STICKERS["goodnight"])
        

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sender = update.message.from_user
    user_states = context.user_states

    if VERBOSE:
        print(update.message.text)
        print(user_states)

    reminder_msg = "<i>Hikari is currently sleeping. Use the /start command to wake her up.</i>"
    
    if sender.id not in user_states:
        await context.bot.send_message(sender.id, reminder_msg, "html")
        return
    
    user_msg = update.message.text
    user_msg = emoji.replace_emoji(user_msg, replace="").strip()
    message_queue = user_states[sender.id]["message_queue"]

    if len(message_queue) > 0:
        await context.bot.send_message(
            sender.id,
            "<i>Hikari is still typing... Please wait a second.</i>",
            "html"
        )
        return
    else:
        message_queue.append({
            "name" : "sorakee" if sender.id == CREATOR_ID else f'{sender.full_name}',
            "message" : user_msg,
            "datetime" : datetime.now()
        })
    
    # Runs a coroutine in the background 
    # Allows the current function to continue running and finish
    asyncio.create_task(process_message(sender.id, message_queue))


async def whitelist_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if VERBOSE:
        print(update.effective_message)
    
    senderID = update.effective_chat.id
    msg = ["Huh?! Who are you?", 
           "You need my creator's permission first before you can talk to me.", 
           "Sorry!"]

    if senderID != CREATOR_ID or update.message.chat.type != "private":
        await update.effective_message.reply_text(
            text=msg[0],
            reply_to_message_id=update.effective_message.id
        )
        
        for m in msg[1:]:
            await asyncio.sleep(1)
            await context.bot.send_message(senderID, m)

        await context.bot.send_sticker(senderID, STICKERS["sorry"])

        raise ApplicationHandlerStop