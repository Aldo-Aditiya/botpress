from datetime import datetime
import requests
import uuid
import time
from collections import deque, defaultdict

import chainlit as cl
from chainlit.user_session import user_session as cl_user_session

from chat_assistant.config import load_config

from bp_katakita.utils.handler import raw_chat_history as raw_chat_history_handler
from bp_katakita.utils.handler.model import RawChatHistory

# ----------------- #

# Load Config
CONFIG = load_config()

# Setup Runtime Params
RUNTIME_PARAMS = {
    "user_session_message_count": defaultdict(int),
}

OPENING_MESSAGE = ["Selamat datang di Livechat Official Bank DKI. Sekarang kamu terhubung dengan Dian, Bank DKI Digital Assistant yang siap membantu kamu.", 
                   "Ada yang bisa aku bantu?"]

# ----------------- #

def bot_reply(message, timeout=60):
    payload = {"chat_session_id": cl_user_session.get("id"),"message": message}

    try:
        chat_endpoint = "http://localhost:45881/simple_document_qa"
        response = requests.post(chat_endpoint, json=payload, timeout=timeout).json()
        bot_messages = [response["assistant_reply"]]
    except requests.exceptions.Timeout:
        bot_messages = "Maaf, saya tidak bisa memproses permintaan kamu. Silahkan kirimkan pesanmu lagi."
    except requests.exceptions.JSONDecodeError:
        bot_messages = "Maaf, saya tidak bisa memproses permintaan kamu. Silahkan kirimkan pesanmu lagi."

    return bot_messages

def create_raw_chat_db_entry(message:str, author:str):
    chat_db_entry = RawChatHistory(
        message_id=str(uuid.uuid4()),
        session_id=cl_user_session.get("id"),
        bot_id="testing_18-07-23",
        datetime=datetime.now(),
        message=message,
        author=author
    )
    _ = raw_chat_history_handler.create(chat_db_entry)

# ----------------- #


@cl.on_chat_start
async def start():
    for message in OPENING_MESSAGE:
        await cl.Message(content=message).send()

@cl.on_message
async def on_message(message: str):
    create_raw_chat_db_entry(message, "User")

    bot_messages = bot_reply(message)
    for bot_message in bot_messages:
        await cl.Message(content=bot_message).send()

        create_raw_chat_db_entry(bot_message, "Assistant")
    
    RUNTIME_PARAMS["user_session_message_count"][cl_user_session.get("id")] += 1

    time.sleep(1)