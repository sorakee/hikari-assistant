import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(BOT_TOKEN)

async def send_reply():
    async with bot:
        await asyncio.sleep(1)
        await bot.send_message(5764657078, "Sent from another program.")

asyncio.run(send_reply())