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
chat = load_azure_chat_openai(timeout=20)#callback=prompt_callback_handler)

# ----------------- #

SYSTEM_PROMPT = """Assistant's task is to think step by step using the below CUSTOM_FORMAT delimited by triple backticks below:
```
thinking: Argue step by step based on the chat_history whther or not the user question is answered. Emphasize newest messages.
answered: <One of [yes,no,unknown] depending on previous step>
```
"""

PRIMING_USER_MESSAGE_1 = """chat_history is delimited by triple backticks below.
```
User: Mau tanya tentang rover Mars
Assistant: Apa yang ingin Anda ketahui tentang rover Mars? Saya dapat memberi tahu Anda tentang lokasinya atau statusnya.
User: lokasinya
Assistant: Rover Mars berada di Kater Jezero, dengan posisi spesifiknya dapat bervariasi.
```

answer in CUSTOM_FORMAT, delimited by triple backticks below:
```
thinking:
"""

PRIMING_ASSISTANT_MESSAGE_1 = """The user asked about the location of the Mars rover in Indonesian. The assistant responded that the Mars rover is in Jezero Crater, with the specific location being variable. Thus, the assistant provided the general area where the rover is located on Mars, which directly addresses the user's question.
answered: yes
```
"""

PRIMING_USER_MESSAGE_2 = """chat_history is delimited by triple backticks below.
```
User: Mau tanya tentang Nasa
Assistant: Tentu! Apa yang ingin kamu tanyakan tentang NASA?
User: Lokasinya
Assistant: NASA (National Aeronautics and Space Administration) berlokasi di Amerika Serikat. 
User: Kalau lokasi bank terdekat di mana?
Assistant: Maaf, saya tidak memiliki akses langsung ke informasi terkini tentang lokasi bank terdekat.
```

answer in CUSTOM_FORMAT, delimited by triple backticks below:
```
thinking:
"""

PRIMING_ASSISTANT_MESSAGE_2 = """The user asked two questions about locations: one about NASA, and one about the nearest bank. The assistant answered the question about NASA correctly, stating it's located in the United States. However, when the user asked about the location of the nearest bank, the assistant indicated that it does not have direct access to real-time location information, thus not providing an actionable answer to the user's question.
answered: no
"""

USER_MESSAGE_TEMPLATE = """chat_history is delimited by triple backticks below.
```
{chat_history}
```

answer in CUSTOM_FORMAT, delimited by triple backticks below:
```
thinking:
"""

# ----------------- #

def parse_bool(text:str):
    if text == "yes":
        return "yes"
    elif text == "no":
        return "no"
    elif "unknown" in text:
        return "unknown"
    else:
        raise OutputParserException(f"Could not parse text: {text}")

def parse_output(text:str) -> dict:
    pattern = r"answered: (.+)"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        raise OutputParserException(f"Could not parse output: {text}")

    reply_dict = {
        "answered": parse_bool(match.group(1)),
    }

    return reply_dict

def predict(chat_history:str):
    # Construct Prompt
    prompt = []
    prompt.append(SystemMessage(content=SYSTEM_PROMPT))
    prompt.append(HumanMessage(content=PRIMING_USER_MESSAGE_1))
    prompt.append(AIMessage(content=PRIMING_ASSISTANT_MESSAGE_1))
    prompt.append(HumanMessage(content=PRIMING_USER_MESSAGE_2))
    prompt.append(AIMessage(content=PRIMING_ASSISTANT_MESSAGE_2))
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