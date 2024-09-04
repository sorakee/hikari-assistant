import os
from pathlib import Path
from webuiapi import WebUIApi, HiResUpscaler
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("IMAGE_HOST")
PORT = os.getenv("IMAGE_PORT")
SD_MODEL = os.getenv("SD_MODEL")
DEFAULT_PROMPT = os.getenv("DEFAULT_PROMPT")
NEGATIVE_PROMPT = os.getenv("NEGATIVE_PROMPT")
IMG_PATH = os.getenv("IMAGE_PATH")
file_path = Path(IMG_PATH)
directory = file_path.parent
if not os.path.exists(directory):
    os.mkdir(directory)
api = WebUIApi(host=HOST, port=PORT)


def generate_img(prompt: str) -> bool:
    prompt = f"{DEFAULT_PROMPT}, {prompt}"
    negative_prompt = NEGATIVE_PROMPT
    options = {
        "sd_model_checkpoint": SD_MODEL,
        "CLIP_stop_at_last_layers": 2
    }
    try:
        api.set_options(options=options)
        result = api.txt2img(
            prompt=prompt,
            negative_prompt=negative_prompt,
            sampler_index="DPM++ 2M",
            scheduler="Karras",
            steps=25,
            width=512,
            height=512,
            cfg_scale=6.5,
            enable_hr=True,
            hr_scale=1.5,
            denoising_strength=0.7,
            hr_upscaler=HiResUpscaler.LatentNearestExact
        )
        result.image.save(file_path)
        return True
    except:
        # Image API is offline
        return False
    
    

if __name__ == "__main__":
    generate_img("sitting in a cozy bedroom playing a guitar")