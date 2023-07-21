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
thinking: Argue step by step based on the chat_history what the topic of the interaction is. Emphasize newest messages.
topic: <Prioritize taking from topic_list. Pick `oot` if user message is out of topic. Pick `unknown` as a last resort if topic is not clear. Use Indonesian by default.>
```
"""

PRIMING_USER_MESSAGE_1 = """chat_history is delimited by triple backticks below.
```
User: Mau tanya tentang rover Mars
Assistant: Apa yang ingin Anda ketahui tentang rover Mars? Saya dapat memberi tahu Anda tentang lokasinya atau statusnya.
```

topic_list is delimited by triple backtics below:
```
- Mars Rover
- NASA
- SpaceX
```

answer in CUSTOM_FORMAT:
thinking:"""


PRIMING_ASSISTANT_MESSAGE_1 = """The user is expressing interest in asking about the Mars rovers, as reflected in their question. I, as the assistant, offered to provide information regarding the Mars rovers' location or status. Hence, it's evident that the central subject of this conversation revolves around the Mars rovers.
topic: Mars Rovers"""

PRIMING_USER_MESSAGE_2 = """chat_history is delimited by triple backticks below.
```
User: Lokasi Nasa di mana ya?
Assistant: NASA (National Aeronautics and Space Administration) berlokasi di Amerika Serikat.
```

topic_list is delimited by triple backtics below:
```
- Mars Rover
- NASA
- SpaceX
```

answer in CUSTOM_FORMAT:
thinking:"""

PRIMING_ASSISTANT_MESSAGE_2 = """Based on the chat history, the user is asking about the location of NASA. My response confirmed that NASA is located in the United States. The primary topic of the conversation can be inferred from this exchange.
topic: NASA"""

USER_MESSAGE_TEMPLATE = """chat_history is delimited by triple backticks below.
```
{chat_history}
```

topic_list is delimited by triple backtics below:
```
- Bank DKI General
- Kartu Jakarta Pintar (KJP)
- Kartu Jakarta Mahasiswa Unggul (KJMU)
- Kartu Lanjut Jakarta (KLJ)
- Kartu Anak Jakarta (KAJ)
- Kredit Multi Guna (KMG)
- Kredit Monas Pemula
- Gerbang Pembayaran Nasional (GPN)
- Deposito
- Jakone Mobile
```

answer in CUSTOM_FORMAT:
thinking:"""

# ----------------- #

def parse_output(text:str) -> dict:
    pattern = r"topic: (.+)"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        raise OutputParserException(f"Could not parse output: {text}")

    reply_dict = {
        "topic": clean_up_topic(match.group(1)),
    }

    return reply_dict

def clean_up_topic(text:str):
    topics_dict = {
        "General": ["Bank DKI General"],
        "KJP": ["Kartu Jakarta Pintar (KJP)", "KJP", "Kartu Jakarta Pintar"],
        "KJMU": ["Kartu Jakarta Mahasiswa Unggul (KJMU)", "KJMU", "Kartu Jakarta Mahasiswa Unggul"],
        "KLJ": ["Kartu Lanjut Jakarta (KLJ)", "KLJ", "Kartu Lanjut Jakarta"],
        "KAJ": ["Kartu Anak Jakarta (KAJ)", "KAJ", "Kartu Anak Jakarta"],
        "KMG": ["Kredit Multi Guna (KMG)", "KMG", "Kredit Multi Guna"],
        "Kredit Monas Pemula": ["Kredit Monas Pemula Bank DKI", "Kredit Monas Pemula", "Kredit Monas"],
        "GPN": ["Gerbang Pembayaran Nasional (GPN)", "GPN", "Gerbang Pembayaran Nasional"],
        "Deposito": ["Deposito"],
        "Jakone Mobile": ["Jakone Mobile Bank DKI", "Jakone Mobile", "Jakone"],
    }

    for title, topics in topics_dict.items():
        for topic in topics:
            if topic.lower().strip() in text.lower().strip():
                return title
        return text

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
