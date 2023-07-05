from datetime import datetime
import argparse
import gradio as gr
import uuid
import requests
import json

from chat_assistant.config import load_config, load_app_config

# ----------------- #

# Setup Global Config
CONFIG = load_config()

# Setup Runtime Parameters
RUNTIME_PARAMS = {
    "bot_id": ""
}

# ----------------- #

def send_message(history, message, request: gr.Request):
    history = history + [(message, None)]
    return history, ""

def bot_reply(history, session_id, timeout=60):
    payload = {"type": "text","text": history[-1][0]}
    headers = {"Content-Type": "application/json"}

    try:
        chat_endpoint = APP_CONFIG["chatbot_api"]["base_url"]
        chat_endpoint = chat_endpoint.replace("{bot_id}", APP_CONFIG["chatbot_api"]["bot_id"]).replace("{session_id}", session_id)
        response = requests.post(chat_endpoint, json=payload, headers=headers, timeout=timeout).json()

        bot_messages = [reply["text"] for reply in response["responses"] if reply["type"] == "text"]
            
    except requests.exceptions.Timeout:
        bot_messages = [APP_CONFIG["ui"]["ui_messages"]["error_message"]]
    except requests.exceptions.JSONDecodeError:
        bot_messages = [APP_CONFIG["ui"]["ui_messages"]["error_message"]]

    for i, bot_message in enumerate(bot_messages):
        if i == 0:
            history[-1][1] = bot_message.replace("\n", "<br>") # newline bug fix for gradio
        else:
            history.append([None, bot_message.replace("\n", "<br>")])

    return history

def bot_reset():
    return None, str(uuid.uuid4())

# ----------------- #

def main():
    parser = argparse.ArgumentParser(description='UI for Running Chat Assistant Agents')
    parser.add_argument('-c', '--app_config', help='App config used to run the app', required=True)
    args = parser.parse_args()

    global APP_CONFIG 
    APP_CONFIG = load_app_config(args.app_config)["runtime_params"]

    with gr.Blocks(title=APP_CONFIG["ui"]["ui_messages"]["title"]) as demo:

        # Establish Agent and Session
        session_uuid_state = gr.State(value=str(uuid.uuid4()))

        # Setup UI
        gr.Markdown(APP_CONFIG["ui"]["ui_messages"]["header"])

        chatbot_initial_messages = []
        for message in APP_CONFIG["ui"]["ui_messages"]["initial_messages"]:
            chatbot_initial_messages.append((None, message))
        chatbot_box = gr.Chatbot(chatbot_initial_messages, elem_id="chatbot_box").style(height=600)

        with gr.Row():
            with gr.Column(scale=0.9):
                txt = gr.Textbox(
                    show_label=False,
                    placeholder="Type your question and press enter to send",
                ).style(container=False)
            with gr.Column(scale=0.05, min_width=0):
                send_btn = gr.Button("Send")
            with gr.Column(scale=0.05, min_width=0):
                reset_btn = gr.Button("Reset")
        gr.Markdown(APP_CONFIG["ui"]["ui_messages"]["disclaimer_message"])

        txt.submit(send_message, inputs=[chatbot_box, txt], outputs=[chatbot_box, text]).then(
            bot_reply, inputs=[chatbot_box, session_uuid_state], outputs=chatbot_box
        )
        send_btn.click(send_message, inputs=[chatbot_box,txt], outputs=[chatbot_box, text]).then(
            bot_reply, inputs=[chatbot_box, session_uuid_state], outputs=chatbot_box
        )

        reset_btn.click(bot_reset, inputs=[], outputs=[chatbot_box, session_uuid_state], queue=False)

    demo.launch(favicon_path=APP_CONFIG["ui"]["favicon_path"], 
                server_port=APP_CONFIG["ui"]["port"], 
                server_name=APP_CONFIG["ui"]["host"],
                auth=(CONFIG["APP_LOGIN"]["username"], CONFIG["APP_LOGIN"]["password"]))

if __name__ == "__main__":
    main()