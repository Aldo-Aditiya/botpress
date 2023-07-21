import re
import traceback

from langchain.schema import OutputParserException
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

from chat_assistant.utils import load_azure_chat_openai
from chat_assistant.callbacks import PromptCallbackHandler

from bp_katakita.config import load_config

# ----------------- #

CONFIG = load_config()
BOT_FILES_DIR = CONFIG["BOT_FILES_DIR"]

prompt_callback_handler = PromptCallbackHandler()
chat = load_azure_chat_openai(timeout=30)

# ----------------- #

SYSTEM_PROMPT = """Assistant's task is to think step by step using the below CUSTOM_FORMAT delimited by triple backticks below:
```
summary: <Summarize the chat_history in 50 tokens using Indonesian.>
sentiment: <MUST BE ONE OF [positive, negative, neutral] depending on previous step>
```"""

USER_MESSAGE_TEMPLATE = """chat_history is delimited by triple backticks below.
```
{chat_history}
```

answer in CUSTOM_FORMAT:
summary:
"""

# ----------------- #

def parse_sentiment(text:str):
    text = text.strip().lower()
    if "positive" in text:
        return "positive"
    elif "negative" in text:
        return "negative"
    elif "neutral" in text:
        return "neutral"
    else:
        raise OutputParserException(f"Could not parse text: {text}")

def parse_output(text:str) -> dict:
    pattern = r"(.+).*answered: (.+)"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        raise OutputParserException(f"Could not parse output: {text}")

    reply_dict = {
        "summary": match.group(1),
        "sentiment": parse_sentiment(match.group(2))
    }

    return reply_dict

def predict(chat_history:str):
    # Construct Prompt
    prompt = []
    prompt.append(SystemMessage(content=SYSTEM_PROMPT))
    prompt.append(HumanMessage(content=USER_MESSAGE_TEMPLATE.format(chat_history=chat_history)))

    # Predict and Parse
    try:
        result = chat(prompt)
        print(result.content)
        result_dict = parse_output(result.content)
        return result_dict
    except Exception as e:
        traceback.print_exc()
        raise e