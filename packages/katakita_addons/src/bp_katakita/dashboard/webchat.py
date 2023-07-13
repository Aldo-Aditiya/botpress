from datetime import datetime
import argparse
import uuid
import requests
import json

import uvicorn
import asyncio

import chainlit as cl
from chainlit.user_session import user_session as cl_user_session

from chat_assistant.config import load_config

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

# ----------------- #

@cl.on_message
async def on_message(message: str):
    bot_messages = bot_reply(message)
    for bot_message in bot_messages:
        await cl.Message(content=bot_message).send()