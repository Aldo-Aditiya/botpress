import os
from typing import List, Optional

from bp_katakita.config import load_config
from bp_katakita.chatgpt_nlu.model import NLUProcess, NLUDataSync

# ----------------- #

CONFIG = load_config()
BOT_FILES_DIR = CONFIG["BOT_FILES_DIR"]

# ----------------- #

nlu_intent_prompt = ""

# ----------------- #

def save_intents(args: NLUDataSync):
    intents = args.intents
    bot_id = args.bot_id

    bot_id_files_dir = BOT_FILES_DIR + bot_id
    if not os.path.exists(bot_id_files_dir):
        os.mkdir(bot_id_files_dir)
        os.mkdir(bot_id_files_dir + "/intents")
    
    # Remove files that are no longer in the intents list
    intent_names = [intent.name for intent in intents]
    intent_files = os.listdir(bot_id_files_dir + "/intents")
    for intent_file in intent_files:
        intent_name = intent_file.split(".")[0]
        if intent_name not in intent_names:
            os.remove(bot_id_files_dir + "/intents/" + intent_file)

    # Save intents
    for intent in intents:
        if "__qna__" in intent.name:
            continue
        with open(bot_id_files_dir + "/intents/" + intent.name + ".json", "w") as f:
            f.write(intent.json())

def get_intents(args:NLUProcess) -> List:
    input = args.input
    bot_id = args.bot_id

    return []