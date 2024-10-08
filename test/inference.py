import os
import sys
import json
import requests
from pathlib import Path

###########################################################

# print("Please input the host URL:")
# print("Example: test.com")
# host_input = input("> ")

URI = f"http://127.0.0.1:5000/v1/chat/completions"

###########################################################
# CHAT SETTINGS
###########################################################
# 'CONTEXT' CAN BE CHANGED WHEN DEALING MEMORY STUFF
# 'CONTEXT' CAN ALSO HELP HER GUIDE HER RESPONSES
# 'CONTEXT' defines the character
# NOTE : Character cannot be created through API
# Therefore, create a new character yaml/json and
# place it in oobabooga's 'characters' folder

root_dir = Path(__file__).resolve().parent.parent
filename = root_dir / "character.json"

with open(filename, encoding="utf-8") as file:
    character = json.load(file)
    verbose: bool = False
    CHAR_NAME: str = character["name"]
    GREETING: str = character["greeting"]
    instruct_cmd: str = character["instruct_cmd"]
    context: str = character["main_context"]
    desc: str = character["description"]

TEMPLATE = "Vicuna-v1.1"
USER: str = "sorakee"

memory = [{"role": "assistant", "content": GREETING}]
ctx = f"{desc}\n\n{context}"

def main():
    if GREETING != "":
        print(f"{CHAR_NAME}: " + GREETING + "\n")
    
    while True:
        user_message = input("> ")
        memory.append({"role": "user", "content": user_message})
        

        headers = {
            "Content-Type": "application/json"
        }

        body = {
            "messages": memory,
            "name1": USER,
            "mode": "chat-instruct",
            "character": CHAR_NAME,
            "context": ctx,
            "chat_instruct_command": instruct_cmd,
            "instruction_template": TEMPLATE,
            "temperature": 0.7,
            "repetition_penalty": 1.1
        }
    
        response = requests.post(URI, headers=headers, json=body, verify=False)
        
        if response.status_code == 200:
            if verbose:
                print(response.json(), "\n")

            result = response.json()["choices"][0]["message"]["content"]
            memory.append({"role": "assistant", "content": result})
        else:
            result = "ERROR"
        
        print(f"\n{CHAR_NAME}: " + result + "\n")
        

if __name__ == "__main__":
    main()