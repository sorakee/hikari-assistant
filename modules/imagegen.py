import os
from pathlib import Path
from webuiapi import WebUIApi, HiResUpscaler
from dotenv import load_dotenv

load_dotenv()

USER = os.getenv("USER")
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


def generate_img(
        prompt: str,
        sampler: str = "DPM++ 2M",
        scheduler: str = "Karras",
        steps: int = 25,
        width: int = 768,
        height: int = 768,
        cfg_scale: float = 6.5,
        enable_hr: bool = False,
        hr_scale: float = 1.5,
        denoising_strength: float = 0.7,
    ) -> bool:
    prompt = prompt.replace(USER, "1boy")
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
            sampler_index=sampler,
            scheduler=scheduler,
            steps=steps,
            width=width,
            height=height,
            cfg_scale=cfg_scale,
            enable_hr=enable_hr,
            hr_scale=hr_scale,
            denoising_strength=denoising_strength,
            hr_upscaler=HiResUpscaler.LatentNearestExact
        )
        result.image.save(file_path)
        return True
    except:
        # Image API is offline
        return False
    

if __name__ == "__main__":
    img_result = generate_img("sitting in a cozy bedroom playing a guitar while smiling")
    if img_result:
        print("ImageGen Success!")