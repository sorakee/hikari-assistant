import asyncio
import os
from dotenv import load_dotenv
from telegram.ext import Application

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")


def get_message_queue():
    return


def process_message(message_queue):
    return


async def check_inactivity():
    return


async def check_inactivity(app: Application):
    return