import os
import json
import re
from typing import List, Optional
from pprint import pprint

from langchain.schema import OutputParserException

from chat_assistant.utils import load_azure_chat_openai
from chat_assistant.callbacks import PromptCallbackHandler

from bp_katakita.config import load_config
from bp_katakita.chatgpt_nlu.model import NLUProcess, NLUDataSync

# ----------------- #

CONFIG = load_config()
BOT_FILES_DIR = CONFIG["BOT_FILES_DIR"]

# ----------------- #

prompt_callback_handler = PromptCallbackHandler()
chat = load_azure_chat_openai(callback=prompt_callback_handler)
NLU_INTENT_PROMPT = """You are an intent recognition engine.
Your job is to recognize the intent and slots of the user's input, based on the given intent context.

---

Below are the intent context:
```
{intent_context}
```

---

You must use the following format, delimited by triple backticks:
```
intent_classes: {intent_classes} <DO NOT change this>
intent: <The intent_name that most matches the input, based on the given utterances. ONLY from values in intent_classes. If nothing matches, set as `None`]>
intent_slots: <Is the `slots` value from the relevant intent class. If intent is `None`, then set as []>
slots: [<list of slots that appear in the intent. ONLY from values in the intent_slots. If intent is `None`, then set as []>]
slot_values: [<list of slot values. If intent is `None`, then set as []>]
```

---

Examples

```
input: Show me pictures from 2019-08-02
intent_classes: [rover-pictures, rover-status]
intent: rover-pictures
intent_slots: [earthDate, imageType, planet]
slots: [imageType, earthDate]
slot_values: [pictures, 2019-08-02]

input: Show me Mars pictures
intent_classes: [rover-pictures, rover-weather, rover-status]
intent: rover-pictures
intent_slots: [earthDate, imageType, planet]
slots: [planet, imageType]
slot_values: [Mars, pictures]

input: Show me Mars pictures from 2019-08-02
intent_classes: [order-mcdonalds, order-pizza]
intent: None
intent_slots: []
slots: []
slot_values: []
```

---

Begin

input: {input}

"""

# ----------------- #

def parse_list(text: str) -> List:
    text = text.replace("[", "").replace("]", "")
    output = [item.strip() for item in text.split(",")]
    if output == [""]:
        return []
    return output

def parse_output(text: str) -> dict:
    pattern = r"intent_classes: (.+).*intent: (.+).*intent_slots: (.+).*slots: (.+).*slot_values: (.+)"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        raise OutputParserException(f"Could not parse output: {text}")

    reply_dict = {
        "intent_classes": parse_list(match.group(1)),
        "intent": match.group(2).replace("\n", ""),
        "intent_slots": parse_list(match.group(3)),
        "slots": parse_list(match.group(4)),
        "slot_values": parse_list(match.group(5))
    }

    return reply_dict


def save_intent_examples(args: NLUDataSync):
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

def get_intent_examples(bot_id: str):
    intent_examples = []
    for intent_file in os.listdir(BOT_FILES_DIR + bot_id + "/intents"):
        with open(BOT_FILES_DIR + bot_id + "/intents/" + intent_file, "r") as f:
            intent = json.load(f)
            intent_examples.append(intent)
    return intent_examples

def predict_intents(args:NLUProcess):
    input = args.input
    bot_id = args.bot_id

    # Construct Prompt
    intent_examples = get_intent_examples(bot_id)

    intent_classes_prompt = "[" + ", ".join(intent_example["name"] for intent_example in intent_examples) + "]"

    intent_prompts = []
    for intent_example in intent_examples:
        intent_prompt = """intent_name: {intent_name}
slots: {slots}
utterances: \n\t{utterances}
        """
        intent_prompt = intent_prompt.format(intent_name=intent_example["name"],
                                             slots="[" + ", ".join(slot["name"] for slot in intent_example["slots"]) + "]",
                                             utterances="\n\t".join(intent_example["utterances"]["en"]))
        intent_prompts.append(intent_prompt)
    intent_context_prompt = "\n".join(intent_prompts)
    
    prompt = NLU_INTENT_PROMPT.format(intent_context=intent_context_prompt, 
                                      intent_classes=intent_classes_prompt,
                                      input=input)

    # Predict and Parse
    result = chat.predict(prompt)
    result_dict = parse_output(result)

    # Edit Schema
    output = {}
    output["intent"] = {
        "name": result_dict["intent"],
        "confidence": 1,
        "context": "global" # TODO - Change Context to be dynamic
    }

    output["slots"] = {}
    for i, slot in enumerate(result_dict["slots"]):
        output["slots"][slot] = {
            "name": slot,
            "value": result_dict["slot_values"][i]
        }

    return output

    