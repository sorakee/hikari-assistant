import os
import emoji
import asyncio
import logging
import json
from dotenv import load_dotenv
from datetime import datetime
from handler import (
    whitelist_users,
    handle_cmd,
    handle_msg
)
from telegram import Update
from telegram.ext import (
    filters,
    ApplicationBuilder,
    ApplicationHandlerStop,
    ContextTypes,
    MessageHandler,
    TypeHandler
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    print(app)

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