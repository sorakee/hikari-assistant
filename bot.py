import os
import asyncio
import telegram
from dotenv import load_dotenv


load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')


async def main():
    bot = telegram.Bot(BOT_TOKEN)
    async with bot:
        updates = (await bot.get_updates())
        print(updates)
        chatID = updates[-1].message.from_user.id
        sender = updates[-1].message.from_user.first_name
        msg = f"Hi, {sender}!"
        await bot.send_message(text=msg, chat_id=chatID)

if __name__ == '__main__':
    asyncio.run(main())