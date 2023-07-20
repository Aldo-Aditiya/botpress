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

# Setup Runtime Params
RUNTIME_PARAMS = {
    "user_session_message_count": defaultdict(int)
}

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

@cl.action_callback("Bicara dengan Live Agent")
async def on_action(action):
    await cl.Message(content=f"Baik, mohon menunggu sambil kami sambungkan anda ke Live Agent kami.").send()

@cl.on_chat_start
async def start():
    await cl.Message(content=f"Halo! Aku adalah Bank DKI Q/A Bot. Saya siap membantu menjawab pertanyaanmu tentang Bank DKI.").send()

@cl.on_message
async def on_message(message: str):
    create_raw_chat_db_entry(message, "User")

    bot_messages = bot_reply(message)
    for bot_message in bot_messages:
        await cl.Message(content=bot_message).send()

        create_raw_chat_db_entry(bot_message, "Assistant")
    
    RUNTIME_PARAMS["user_session_message_count"][cl_user_session.get("id")] += 1

    if RUNTIME_PARAMS["user_session_message_count"][cl_user_session.get("id")] % 5 == 0:
        actions = [
            cl.Action(name="Bicara dengan Live Agent", value="Bicara dengan Live Agent", description="Klik untuk dihubungkan kepada Live Agent kami.")
        ]
        await cl.Message(content="Apabila kamu masih butuh bantuan, Live Agent kami siap untuk membantu anda. Klik tombol di bawah untuk dihubungkan dengan Live Agent kami.", actions=actions).send()