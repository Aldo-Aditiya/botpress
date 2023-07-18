import time
from datetime import datetime, timedelta
from typing import List, Tuple
from collections import defaultdict

from bp_katakita.analytics import (
    answered_detection,
    topic_detection
)
from bp_katakita.config import load_config
from bp_katakita.utils import db
from bp_katakita.utils.handler import chat_history as chat_history_handler
from bp_katakita.model import DashboardChatHistory

# ----------------- #

CONFIG = load_config()

RUNTIME_PARAMS = {
    "last_updated": datetime.now(),
    "conversation_history": defaultdict(list),
    "conversation_last_updated": defaultdict(lambda: datetime.now())
}

# ----------------- #

msg_messages_idx_to_colname = {
    0: "id",
    1: "conversationId",
    2: "authorId",
    3: "sentOn",
    4: "payload"
}
msg_messages_colname_to_idx = {v: k for k, v in msg_messages_idx_to_colname.items()}

def msg_messages_to_list(msg_messages:List[Tuple]) -> List[dict]:
    message_list = []
    for message in msg_messages:
        message_dict = {
            "id": message[msg_messages_colname_to_idx["id"]],
            "conversationId": message[msg_messages_colname_to_idx["conversationId"]],
            "authorId": message[msg_messages_colname_to_idx["authorId"]],
            "sentOn": message[msg_messages_colname_to_idx["sentOn"]],
            "payload": message[msg_messages_colname_to_idx["payload"]]
        }
        message_list.append(message_dict)

    return message_list

def construct_chat_db_entry(message:dict) -> DashboardChatHistory:
    chat_db_entry = DashboardChatHistory(
        user_id=message["authorId"],
        botpress_message_id=message["Id"],
        botpress_conversation_id=message["conversationId"],
        datetime=message["sentOn"],
        message=message["payload"]["text"],
        author=message["author"],
        topic=message["topic"],
        answered=message["answered"]
    )
    return chat_db_entry

# ----------------- #

def detect_botpress_chat_history_changes():
    # Check if the newest chat history is newer than the last time we checked
    query = 'SELECT * FROM "msg_messages" ORDER BY "sentOn" DESC LIMIT 1;'
    result = db.read_postgres_db(query)
    newest_chat = result[0]
    newest_chat_datetime = newest_chat[msg_messages_colname_to_idx["sentOn"]]

    return newest_chat_datetime

def process(chat_history_k:int=3, message_buffer_time_mins:int=2):
    last_chat_update = detect_botpress_chat_history_changes()
    if last_chat_update <= RUNTIME_PARAMS["last_updated"]:
        pass

    elif last_chat_update > RUNTIME_PARAMS["last_updated"]:

        # Get the newest chat histories from last updated
        last_chat_update_str = last_chat_update.strftime('%Y-%m-%d %H:%M:%S')
        last_updated_str = RUNTIME_PARAMS["last_updated"].strftime('%Y-%m-%d %H:%M:%S')
        query = f"""SELECT * FROM "msg_messages" WHERE "sentOn" BETWEEN TO_TIMESTAMP('{last_updated_str}', 'YYYY-MM-DD HH24:MI:SS') AND TO_TIMESTAMP('{last_chat_update_str}', 'YYYY-MM-DD HH24:MI:SS') ORDER BY "sentOn" ASC;"""
        result = db.read_postgres_db(query)
        msg_messages_list = msg_messages_to_list(result)

        # Update the last_updated
        RUNTIME_PARAMS["last_updated"] = last_chat_update + timedelta(seconds=1)

        # Convert msg_messages_list to conversation_history
        for message in msg_messages_list:
            message["author"] = "User" if message["authorId"] is not None else "Assistant"
            message["processed"] = False
            RUNTIME_PARAMS["conversation_history"][message["conversationId"]].append(message)
            RUNTIME_PARAMS["conversation_last_updated"][message["conversationId"]] = message["conversationId"]["sentOn"]

        # Process each conversation
        for conversation_id, conversation_history in RUNTIME_PARAMS["conversation_history"].items():
            user_message_indices = [i for i, message in enumerate(conversation_history) if message["author"] == "User"]
            process_user_message_indices = [i for i, message in enumerate(conversation_history) if (message["author"] == "User" and not message["processed"])]

            # Process each Message
            ## Previous k user messages (and assistant messages), Current User Message, and Assistant Message up until the next User Message (after at least 1 assistant message).
            ## ASSUMPTION: User messages are not back to back
            unprocessed_conversation_history = [message for message in conversation_history if not message["processed"]]
            for message_idx, message in enumerate(unprocessed_conversation_history):

                if message_idx in process_user_message_indices:

                    # Check if the user message is the newest message in the conversation, and check its buffer time
                    um_idx = message_idx
                    if um_idx == process_user_message_indices[-1]:
                        if conversation_history[um_idx]["sentOn"] + timedelta(minutes=message_buffer_time_mins) > datetime.now():
                            message["topic"] = ""
                            message["answered"] = None
                            message["processed"] = False
                            chat_db_entry = construct_chat_db_entry(message)
                            _ = chat_history_handler.create(chat_db_entry)

                    # We want to find where the value of the user message's index is in the list "user_message_indices" and take the previous k user message indices. 
                    um_idx_idx = user_message_indices.index(um_idx)
                    user_chat_history_idxs = user_message_indices[max(0, um_idx_idx-chat_history_k):um_idx_idx]

                    # We take the oldest user_chat_history and use that up until the um_idx user message to construct the chat history.
                    oldest_user_chat_history_idx = user_chat_history_idxs[0]
                    previous_chat_history_list = []
                    for idx in range(oldest_user_chat_history_idx, um_idx):
                        previous_chat_history_list.append(conversation_history[idx])

                    # Construct chat history string
                    ## Starting from Previous Chat History
                    previous_chat_history = ""
                    for previous_message in previous_chat_history_list:
                        previous_chat_history += f'{previous_message["author"]}: {previous_message["payload"]["text"]}\n'
                    
                    ## Current User Message and Assistant Message (until next User Message)
                    current_chat_history = ""
                    current_chat_history += f'User: {conversation_history[um_idx]["payload"]["text"]}\n'

                    assistant_message_exist = False
                    for idx in range(um_idx+1, process_user_message_indices[-1]):
                        if assistant_message_exist:
                            if conversation_history[idx]["author"] == "User":
                                break
                        else:
                            if conversation_history[idx]["author"] == "Assistant":
                                assistant_message_exist = True
                        current_chat_history += f'{conversation_history[idx]["author"]}: {conversation_history[idx]["payload"]["text"]}\n'

                    # Process answered_detection and topic_detection
                    try:
                        answered_dict = answered_detection.predict(previous_chat_history + current_chat_history)
                        message["answered"] = answered_dict["answered"]
                        message["processed"] = True
                    except:
                        message["answered"] = None

                    try:
                        topic_dict = topic_detection.predict(current_chat_history)
                        message["topic"] = topic_dict["topic"]
                    except:
                        message["topic"] = ""

                else:
                    # If Message is from Assistant, we don't need to process it
                    message["topic"] = ""
                    message["answered"] = None
                    message["processed"] = True

                # Construct DashboardChatHistory and Write to MongoDB
                chat_db_entry = construct_chat_db_entry(message)
                _ = chat_history_handler.create(chat_db_entry)      

# ----------------- #

def main():
    """
    Runs in the background to process botpress chat histories and write results to dashboard database.
    """
    while True:
        process()
        time.sleep(5)

if __name__ == "__main__":
    main()
