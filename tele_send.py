import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(BOT_TOKEN)


async def get_me():
    while True:
        async with bot:
            print(await bot.get_me())


async def send_reply(sender_id, bot_msg, message_queue):
    async with bot:
        await bot.send_message(sender_id, bot_msg)
        message_queue.pop(0)