import os
import asyncio
from voicevox import Client 
from pathlib import Path

URL = "http://127.0.0.1:50021/"
VOICE_TTS = "audio_temp/tts.wav"
file_path = Path(VOICE_TTS)
directory = file_path.parent
SPEAKER: int = 10

if not os.path.exists(directory):
    os.mkdir(directory)


async def synthesize_voice(jp_text: str):
    async with Client(URL) as client:
        audio_query = await client.create_audio_query(jp_text, speaker=SPEAKER)
        with open(VOICE_TTS, "wb") as f:
            f.write(await audio_query.synthesis(speaker=SPEAKER))


if __name__ == "__main__": 
    asyncio.run(synthesize_voice("おはようございます！"))