import os
import sys
import json
import requests

###########################################################

print("Please input the host URL:")
print("Example: tend-altered-brian-formerly.trycloudflare.com")
host_input = input("> ")

URI = f"http://{host_input}/v1/chat/completions"

###########################################################
# CHAT SETTINGS
###########################################################
# 'CONTEXT' CAN BE CHANGED WHEN DEALING MEMORY STUFF
# 'CONTEXT' CAN ALSO HELP HER GUIDE HER RESPONSES
# 'CONTEXT' defines the character
# BELOW IS SIMPLY AN EXAMPLE
# This should be included if you are creating a new character
# or when using the old OpenAPI route


with open("../character.json") as file:
    character = json.load(file)
    verbose: bool = False
    USER: str = "You"
    CHAR_NAME: str = character["name"]
    GREETING: str = character["greeting"]
    INSTRUCT_CMD:str = character["instruct_cmd"]
    context: str = character["context"]

memory = [{"role": "assistant", "content": GREETING}]

# <|prompt|>"""

###########################################################

def main():
    if GREETING != "":
        print(f"{character}: " + GREETING + "\n")

    while True:
        user_message = input("> ")
        memory.append({"role": "user", "content": user_message})

        headers = {
            "Content-Type": "application/json"
        }

        body = {
            "messages": memory,
            "user": USER,
            "mode": "chat-instruct",
            "character": CHAR_NAME
        }
        
        response = requests.post(URI, headers=headers, json=body, verify=False)

        if response.status_code == 200:
            if verbose:
                print(response.json(), "\n")
                
            result = response.json()["choices"][0]["message"]["content"]
            memory.append({"role": "assistant", "content": result})
        else:
            result = "ERROR"

        print(f"\n{character}: " + result + "\n")


def main_alt():
    if GREETING != "":
        print(f"{character}: " + GREETING + "\n")
    
    while True:
        user_message = input("> ")
        memory.append({"role": "user", "content": user_message})

        headers = {
            "Content-Type": "application/json"
        }

        body = {
            "messages": memory,
            "user": USER,
            "mode": "chat-instruct",
            "character": CHAR_NAME,
            "context": context,
            "chat_instruct_command": INSTRUCT_CMD
        }
    
        response = requests.post(URI, headers=headers, json=body, verify=False)
        
        if response.status_code == 200:
            if verbose:
                print(response.json(), "\n")

            result = response.json()["choices"][0]["message"]["content"]
            memory.append({"role": "assistant", "content": result})
        else:
            result = "ERROR"
        
        print(f"\n{character}: " + result + "\n")
        

if __name__ == "__main__":
    flag: int = int(sys.argv[1])

    if flag == 0:
        main()
    else:
        main_alt()