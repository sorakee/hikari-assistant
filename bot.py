import os
import asyncio
import logging

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
BOT_TOKEN = os.getenv('BOT_TOKEN')
CREATOR_ID = int(os.getenv('CREATOR_ID'))

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def handle_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmds = ['/start', '/stop']
    user_states = context.user_states
    senderID = update.message.from_user.id
    senderID_2 = update.effective_chat.id
    isSame = senderID == senderID_2
    print(isSame)
    sender = update.message.from_user

    if update.message.text not in cmds:
        msg = "I'm afraid your command is invalid."
        await context.bot.send_message(
            chat_id=senderID,
            text=msg,
            reply_to_message_id=update.message.id
        )

    if update.message.text == '/start':
        msg = "Hi, I'm Hikari! Nice to meet you!"
        chatID = update.effective_chat.id
        print(chatID)
        await context.bot.send_message(
            chat_id=chatID, 
            text=msg
        )


async def whitelist_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    senderID = update.effective_chat.id
    msg = ["Huh?! Who are you?", 
           "You need my creator's permission first before you can talk to me.", 
           "Sorry!"]

    if senderID != CREATOR_ID or update.message.chat.type != 'private':
        await update.effective_message.reply_text(
            text=msg[0],
            reply_to_message_id=update.effective_message.id
        )
        
        for m in msg:
            if m == msg[0]:
                continue

            await asyncio.sleep(1)
            await context.bot.send_message(
                chat_id=senderID,
                text=m
            )

        raise ApplicationHandlerStop


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    filter_users = TypeHandler(Update, whitelist_users)
    app.add_handler(filter_users, -1)
    cmd_handler = MessageHandler(filters.COMMAND, handle_cmd)
    app.add_handler(cmd_handler)
    
    user_states = {}
    app.context_types.context.user_states = user_states
    app.run_polling()

if __name__ == '__main__':
    main()