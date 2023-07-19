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
thinking: Argue step by step based on the chat_history what the topic is. Emphasize newest messages.
topic: <One keyword determining the topic. `unknown` if not clear. Use Indonesian by default.>
```
"""

PRIMING_USER_MESSAGE_1 = """chat_history is delimited by triple backticks below.
```
User: Mau tanya tentang rover Mars
Assistant: Apa yang ingin Anda ketahui tentang rover Mars? Saya dapat memberi tahu Anda tentang lokasinya atau statusnya.
```

answer in CUSTOM_FORMAT, delimited by triple backticks below:
```
thinking:
"""

PRIMING_ASSISTANT_MESSAGE_1 = """The user is expressing interest in asking about the Mars rovers, as reflected in their question. I, as the assistant, offered to provide information regarding the Mars rovers' location or status. Hence, it's evident that the central subject of this conversation revolves around the Mars rovers.
topic: Mars Rovers
```
"""

PRIMING_USER_MESSAGE_2 = """chat_history is delimited by triple backticks below.
```
User: Lokasi Nasa di mana ya?
Assistant: NASA (National Aeronautics and Space Administration) berlokasi di Amerika Serikat.
```

answer in CUSTOM_FORMAT, delimited by triple backticks below:
```
thinking:
"""

PRIMING_ASSISTANT_MESSAGE_2 = """Based on the chat history, the user is asking about the location of NASA. My response confirmed that NASA is located in the United States. The primary topic of the conversation can be inferred from this exchange.
topic: NASA
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

def parse_output(text:str) -> dict:
    pattern = r"topic: (.+)"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        raise OutputParserException(f"Could not parse output: {text}")

    reply_dict = {
        "topic": match.group(1),
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
