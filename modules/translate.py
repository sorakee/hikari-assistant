import os
import deepl
from dotenv import load_dotenv
from googletrans import Translator

load_dotenv()

AUTH_KEY = os.getenv("DEEPL_TOKEN")
USER = os.getenv("USER")
USER_PRONUNCIATION = os.getenv("USER_PRONUNCIATION")
d_translator = deepl.Translator(AUTH_KEY)
g_translator = Translator()


def translate(txt: str, translator: str="google") -> str:
    txt = txt.replace(USER, USER_PRONUNCIATION)
    d_usage = d_translator.get_usage()
    if d_usage.any_limit_reached or translator == "google":
        print("\n##########")
        print("DeepL API translation limit reached or a different translator is used.")
        print("Using another translator... (GoogleTL)")
        print("##########\n")
        result = g_translator.translate(
            txt,
            src="en",
            dest="ja"
        )
        return str(result.text)

    result = d_translator.translate_text(
        txt, 
        source_lang="EN", 
        target_lang="JA", 
        formality="less"
    )

    if d_usage.character.valid:
        print(
            f"Character usage: {d_usage.character.count} of {d_usage.character.limit}")

    return str(result)

if __name__ == "__main__":
    text = "Hello! How are you today, old man?"
    print(translate(text))