import os
import asyncio
from voicevox import Client 
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("TTS_HOST")
PORT = os.getenv("TTS_PORT")
URL = f"http://{HOST}:{PORT}/"
VOICE_TTS = os.getenv("TTS_PATH")
file_path = Path(VOICE_TTS)
directory = file_path.parent
# VOICEVOX: Amahare Hau (Speaker at Index 3 in fetch_speakers result)
# This is the speaker's style ID
SPEAKER: int = 10
VERBOSE = False

if not os.path.exists(directory):
    os.mkdir(directory)


async def synthesize_voice(text: str, language: str) -> bool:
    """
    Synthesize voice using VOICEVOX engine.
    Compatible with other TTS APIs/Engines in the future to expand language options
    for users.
    
    Parameters
    ----------
    text : str
        The text that will be used to synthesize the voice
    language : list
        The language of the synthesized voice (NOT YET IMPLEMENTED)
    
    Returns
    -------
    bool
        True if the operation was a success, else False
    """
    try:
        async with Client(URL) as client:
            # speaker_list = await client.fetch_speakers()
            # speaker_info = await client.fetch_speaker_info(speaker_list[SPEAKER-7].uuid)
            # print(speaker_info.portrait)
            # print(speaker_info.style_infos[0].id)
            audio_query = await client.create_audio_query(text, speaker=SPEAKER)
            if VERBOSE:
                print("\n##########")
                print("TTS RESULT:")
                print(audio_query.to_dict())
                print("##########\n")
            with open(VOICE_TTS, "wb") as f:
                f.write(await audio_query.synthesis(speaker=SPEAKER))
        return True
    except:
        # TTS API is offline
        print("TTS API currently offline")
        return False


if __name__ == "__main__": 
    text = "集ケサ邸取クゅ中質わをろて南率がぴゃお参変リワ気8違ヲタユ神土むなイド報縦だで販監ったへ県訪更人ほ国禁法ていぽ障9進をきな。"
    # text = "おはようございます！！！！"
    asyncio.run(synthesize_voice(text, "JP"))