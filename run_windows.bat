@echo off
setlocal enabledelayedexpansion

@rem Load configuration from config.env
if exist config.env (
    for /f "usebackq tokens=1,* delims==" %%A in ("config.env") do (
        set "%%A=%%B"
    )
) else (
    echo Error: config.env not found! Please create the config.env file with the correct paths.
    exit /b 1
)

@rem Check for required paths
if not defined TEXT_GEN_PATH (
    echo Error: TEXT_GEN_PATH is not defined in config.env.
    exit /b 1
)
if not defined SD_PATH (
    echo Error: SD_PATH is not defined in config.env.
    exit /b 1
)
if not defined BOT_VENV_PATH (
    echo Error: BOT_VENV_PATH is not defined in config.env.
    exit /b 1
)
if not defined LANG_MODEL (
    echo Error: LANG_MODEL is not defined in config.env.
    exit /b 1
)

set PATH=%PATH%;%SystemRoot%\system32

@rem fix failed install when installing to a separate drive
set TMP=%TEXT_GEN_PATH%\installer_files
set TEMP=%TEXT_GEN_PATH%\installer_files

@rem deactivate existing conda envs as needed to avoid conflicts
(call conda deactivate && call conda deactivate && call conda deactivate) 2>nul

@rem config
set CONDA_ROOT_PREFIX=%TEXT_GEN_PATH%\installer_files\conda
set INSTALL_ENV_DIR=%TEXT_GEN_PATH%\installer_files\env

@rem environment isolation
set PYTHONNOUSERSITE=1
set PYTHONPATH=
set PYTHONHOME=
set "CUDA_PATH=%INSTALL_ENV_DIR%"
set "CUDA_HOME=%CUDA_PATH%"

@rem Pull and run the Docker container for voicevox
echo Starting voicevox engine...
start cmd /k "docker pull voicevox/voicevox_engine:nvidia-ubuntu20.04-latest && docker run --rm --gpus all -p 127.0.0.1:50021:50021 voicevox/voicevox_engine:nvidia-ubuntu20.04-latest"
echo Voicevox engine started in a new window.

@rem Run the text-generation-webui server
echo Starting text-generation-webui server...
start cmd /k "cd /d %TEXT_GEN_PATH% && call "%CONDA_ROOT_PREFIX%\condabin\conda.bat" activate "%INSTALL_ENV_DIR%" && python server.py --nowebui --verbose --api --model %LANG_MODEL%"
echo Text-generation-webui server started in a new window.

@rem Run the stable-diffusion webui
echo Starting stable-diffusion webui...
start cmd /k "cd /d %SD_PATH% && run.bat"
echo Stable-diffusion webui started in a new window.

@rem Activate virtual environment and run bot.py
echo Starting bot.py...
start cmd /k "cd /d %BOT_VENV_PATH% && venv\Scripts\activate && python bot.py"
echo bot.py started in a new window.

@rem Done
echo All processes have been started.
echo Press any key to close all spawned Command Prompt windows...
pause

@rem Close all Command Prompt windows
taskkill /IM WindowsTerminal.exe

exit