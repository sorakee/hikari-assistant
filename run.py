import subprocess
import os


def validate_filepath(filepath):
    if not os.path.exists(filepath):
        print(f"Invalid path: {filepath}")
        return False
    return True


def run_text_generation_webui():
    filepath = r"C:\path\to\text-generation-webui\script.bat"
    try:
        print("Running text-generation-webui script...")
        subprocess.run([filepath], shell=True)
    except Exception as e:
        print(f"Failed to run text-generation-webui script: {e}")


def run_sd_webui():
    filepath = r"C:\path\to\sd.webui\sd_script.bat"
    try:
        print("Running sd.webui script...")
        subprocess.run([filepath], shell=True)
    except Exception as e:
        print(f"Failed to run sd.webui script: {e}")


def run_voicevox_docker():
    try:
        print("Pulling Docker image for voicevox (if not already pulled)...")
        subprocess.run('docker pull voicevox/voicevox_engine:nvidia-ubuntu20.04-latest', shell=True, check=True)
        print("Running Docker container with voicevox...")
        subprocess.run("docker run --rm --gpus all -p '127.0.0.1:50021:50021' voicevox/voicevox_engine:nvidia-ubuntu20.04-latest", shell=True)
    except Exception as e:
        print(f"Failed to run Docker for voicevox: {e}")


def run_bot():
    try:
        print("Running the bot program...")
        main_script_path = os.path.join(os.getcwd(), 'noy.py')
        subprocess.run(['python', main_script_path], shell=True)
    except Exception as e:
        print(f"Failed to run bot: {e}")


def run():
    run_text_generation_webui()
    run_sd_webui()
    run_voicevox_docker()
    run_bot()


if __name__ == "__main__":
    run()