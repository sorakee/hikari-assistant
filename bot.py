import os
import emoji
import asyncio
import logging

from datetime import datetime
from telegram import Update
from telegram.ext import (
    filters,
    ApplicationBuilder,
    ApplicationHandlerStop,
    ContextTypes,
    MessageHandler,
    TypeHandler
)

from dotenv import load_dotenv


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CREATOR_ID = int(os.getenv("CREATOR_ID"))

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

stickers = {
    "sorry" : "CAACAgQAAxkBAAIBgGaO6q2sBUXGeHBGRoxMjfPzDFIJAAKSAAO646QhC0FTFucGe-U1BA",
    "whattodo" : "CAACAgQAAxkBAAIBd2aO6l5Iqu-IumvJ0iWQCf7NubsbAAKQAAO646QhfG1UhUhtwto1BA",
    "hello" : "CAACAgQAAxkBAAIBmGaO8ZgTlY4pJn3xcHi5bYgkhTAzAAKPAAO646QhmIg8RcEGo941BA",
    "goodnight" : "CAACAgQAAxkBAAIB2WaO92iboaxcq-Moh3mD1-SwGAABtAAClQADuuOkIZlpYIIQ5aSmNQQ"
}


async def handle_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmds = ["/start", "/stop"]
    user_states = context.user_states
    # print(user_states)
    sender = update.message.from_user

    if update.message.text not in cmds:
        msg = "I'm afraid your command is invalid."
        await context.bot.send_message(sender.id, msg, reply_to_message_id=update.message.id)

    if update.message.text == "/start":
        msg = "Hello~!"
        user_states[sender.id] = {}
        user_states[sender.id]['message_queue'] = []

        await context.bot.send_message(sender.id, msg)
        await context.bot.send_sticker(sender.id, stickers["hello"])
    
    if update.message.text == "/stop":
        msg = "Goodbye~!"

        try:  
            del user_states[sender.id]
        except:
            await context.bot.send_message(
                sender.id,
                "<i>Hikari already went back to sleep!</i>",
                "html"
            )
            return
        
        await context.bot.send_message(sender.id, msg)
        await context.bot.send_sticker(sender.id, stickers["goodnight"])
        

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.message.from_user
    user_states = context.user_states
    # print(update.message.text)
    # print(user_states)

    msg = "<i>Hikari is currently sleeping. Use the /start command to wake her up.</i>"
    
    if sender.id not in user_states:
        await context.bot.send_message(sender.id, msg, "html")
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
    else:
        message_queue.append({
            "name" : "Creator" if sender.id == CREATOR_ID else f'{sender.full_name}',
            "message" : user_msg,
            "datetime" : datetime.now()
        })


async def whitelist_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # print(update.effective_message)
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

        await context.bot.send_sticker(senderID, stickers["sorry"])

        raise ApplicationHandlerStop


def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    filter_users = TypeHandler(Update, whitelist_users)
    cmd_handler = MessageHandler(filters.COMMAND, handle_cmd)
    msg_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg)

    app.add_handler(filter_users, -1)
    app.add_handler(cmd_handler)
    app.add_handler(msg_handler)
    
    user_states = {}
    app.context_types.context.user_states = user_states
    app.run_polling()


if __name__ == "__main__":
    run_bot()