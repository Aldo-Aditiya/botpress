from datetime import datetime
import pytz
import requests
import uuid
from collections import deque, defaultdict

import chainlit as cl
from chainlit.user_session import user_session as cl_user_session

from chat_assistant.config import load_config

from bp_katakita.utils.handler import raw_chat_history as raw_chat_history_handler
from bp_katakita.utils.handler.model import RawChatHistory

# ----------------- #

# Load Config
CONFIG = load_config()

# ----------------- #

def bot_reply(message, timeout=60):
    payload = {"type": "text","text": message}
    headers = {"Content-Type": "application/json"}

    try:
        chat_endpoint = "http://localhost:3000/api/v1/bots/{bot_id}/converse/{session_id}"
        chat_endpoint = chat_endpoint.replace("{bot_id}", "bank_dki-050723").replace("{session_id}", cl_user_session.get("id"))
        response = requests.post(chat_endpoint, json=payload, headers=headers, timeout=timeout).json()
        bot_messages = [reply["text"] for reply in response["responses"] if reply["type"] == "text"]

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

@cl.on_message
async def on_message(message: str):
    create_raw_chat_db_entry(message, "User")

    bot_messages = bot_reply(message)
    for bot_message in bot_messages:
        await cl.Message(content=bot_message).send()

        create_raw_chat_db_entry(bot_message, "Assistant")
    
