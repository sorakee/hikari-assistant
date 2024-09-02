import os
import logging
import nltk
from dotenv import load_dotenv
from handler import (
    whitelist_users,
    handle_cmd,
    handle_msg,
    handle_aud
)
from telegram import Update
from telegram.ext import (
    filters,
    ApplicationBuilder,
    MessageHandler,
    TypeHandler
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def run_bot() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    filter_users = TypeHandler(Update, whitelist_users)
    cmd_handler = MessageHandler(filters.COMMAND, handle_cmd)
    msg_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg)
    aud_handler = MessageHandler(filters.VOICE, handle_aud)

    app.add_handler(filter_users, -1)
    app.add_handler(cmd_handler)
    app.add_handler(msg_handler)
    app.add_handler(aud_handler)
    
    user_states = {}
    app.context_types.context.user_states = user_states

    print("Attempting to run bot...")
    app.run_polling()


if __name__ == "__main__":
    # TODO : Create a Python setup script to download necessary models and run programs
    # nltk.download("punkt_tab")
    run_bot()