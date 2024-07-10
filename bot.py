import os
import asyncio
import logging

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ApplicationHandlerStop,
    ContextTypes,
    CommandHandler,
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "Hi, I'm Hikari! Nice to meet you!"
    chatID = update.effective_chat.id
    print(chatID)
    await context.bot.send_message(
        chat_id=chatID, 
        text=msg
    )


async def whitelist_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != CREATOR_ID or update.message.chat.type != 'private':
        await update.effective_message.reply_text(
            "Uhm, who are you?",
            reply_to_message_id=update.effective_message.id
        )
        raise ApplicationHandlerStop


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    filter_users = TypeHandler(Update, whitelist_users)
    app.add_handler(filter_users, -1)
    start_handler = CommandHandler('start', start)
    app.add_handler(start_handler)
    
    app.run_polling()

if __name__ == '__main__':
    main()