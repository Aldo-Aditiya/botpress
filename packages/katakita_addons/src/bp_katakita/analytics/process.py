import time
from datetime import datetime, timedelta, timezone
import pytz

from colorama import Fore, Back, Style
from typing import List, Tuple
from collections import defaultdict

from bp_katakita.analytics import (
    answered_detection,
    topic_detection
)
from bp_katakita.config import load_config
from bp_katakita.utils.handler import chat_history as chat_history_handler
from bp_katakita.utils.handler import raw_chat_history as raw_chat_history_handler
from bp_katakita.utils.handler.model import ChatHistory

# ----------------- #

CONFIG = load_config()

RUNTIME_PARAMS = {
    "last_updated": datetime.now(),
    "conversation_history": defaultdict(list),
    "unprocessed_exists": False
}

# ----------------- #

def create_chat_db_entry(message:dict):
    chat_db_entry = ChatHistory(
        message_id=message["message_id"],
        session_id=message["session_id"],
        bot_id=message["bot_id"],
        datetime=message["datetime"],
        message=message["message"],
        author=message["author"],
        topic=message["topic"],
        answered=message["answered"]
    )

    result = chat_history_handler.collection.find_one({"message_id": message["message_id"]})
    if result is None:
        print(str(datetime.now()) + " | ", end="")
        print(Fore.YELLOW + "[PROCESS][MESSAGE] " + Style.RESET_ALL, end="")
        print(f"Writing to database, for message_id: {message['message_id']}")
        _ = chat_history_handler.create(chat_db_entry)  
    else:
        print(str(datetime.now()) + " | ", end="")
        print(Fore.YELLOW + "[PROCESS][MESSAGE] " + Style.RESET_ALL, end="")
        print(f"Updating to database, for message_id: {message['message_id']}")
        _ = chat_history_handler.update(chat_db_entry)

# ----------------- #

def detect_chat_history_changes():
    # Check if the newest chat history is newer than the last time we checked
    newest_chat = raw_chat_history_handler.collection.find().sort("datetime", -1).limit(1)
    newest_chat_datetime = list(newest_chat)[0]["datetime"]

    return newest_chat_datetime

def process(chat_history_k:int=1, message_buffer_time_mins:int=2):
    last_chat_update = detect_chat_history_changes()

    if last_chat_update <= RUNTIME_PARAMS["last_updated"] and not RUNTIME_PARAMS["unprocessed_exists"]:
        pass

    elif last_chat_update > RUNTIME_PARAMS["last_updated"] or RUNTIME_PARAMS["unprocessed_exists"]:

        print("")
        print(str(datetime.now()) + " | ", end="")
        print(Fore.GREEN + "[START] " + Style.RESET_ALL, end="")
        print("Starting Process...")
        
        print(str(datetime.now()) + " | ", end="")
        print(Fore.YELLOW + "[FETCH] " + Style.RESET_ALL, end="")
        print("Fetching Newest Chat History...")

        RUNTIME_PARAMS["unprocessed_exists"] = False

        # Get the newest chat histories from last updated to recent
        last_chat_update_str = last_chat_update.strftime('%Y-%m-%d %H:%M:%S')
        last_updated_str = RUNTIME_PARAMS["last_updated"].strftime('%Y-%m-%d %H:%M:%S')
        query = {
            "datetime": {
                "$gte": RUNTIME_PARAMS["last_updated"],
                "$lte": last_chat_update
            }
        }
        result = raw_chat_history_handler.collection.find(query).sort("datetime", 1)
        raw_chat_history = list(result)

        # Update the last_updated
        RUNTIME_PARAMS["last_updated"] = last_chat_update + timedelta(seconds=1)

        # Convert raw_chat_history to conversation_history
        for message in raw_chat_history:
            message["processed"] = False
            RUNTIME_PARAMS["conversation_history"][message["session_id"]].append(message)

        print(str(datetime.now()) + " | ", end="")
        print(Fore.GREEN + "[FETCH] " + Style.RESET_ALL, end="")
        print(f"Fetched Newest Chat History between {last_updated_str} and {last_chat_update_str}.")

        # Process each conversation
        for conversation_id, conversation_history in RUNTIME_PARAMS["conversation_history"].items():
            print(str(datetime.now()) + " | ", end="")
            print(Fore.YELLOW + "[PROCESS] " + Style.RESET_ALL, end="")
            print(f"Processing chat history for conversation_id: {conversation_id}")

            user_message_indices = [i for i, message in enumerate(conversation_history) if message["author"] == "User"]
            unprocessed_conversation_history_indices = [i for i, message in enumerate(conversation_history) if not message["processed"]]
            unprocessed_user_message_indices = [i for i, message in enumerate(conversation_history) if (message["author"] == "User" and not message["processed"])]

            # Process each Message
            ## Previous k user messages (and assistant messages), Current User Message, and Assistant Message up until the next User Message (after at least 1 assistant message).
            ## ASSUMPTION: User messages are not back to back
            for message_idx in unprocessed_conversation_history_indices:
                message = conversation_history[message_idx]

                print(str(datetime.now()) + " | ", end="")
                print(Fore.YELLOW + "[PROCESS][MESSAGE] " + Style.RESET_ALL, end="")
                print(f"Processing {message['author']} message: '{message['message']}' with message_id: {message['message_id']}")
                
                if message['author'] == 'User':

                    # Check if the user message is the newest message in the conversation, and check its buffer time
                    if message_idx == unprocessed_user_message_indices[-1]:
                        if message["datetime"] + timedelta(minutes=message_buffer_time_mins) > datetime.now():
                            print(str(datetime.now()) + " | ", end="")
                            print(Fore.YELLOW + "[PROCESS][MESSAGE][SKIP] " + Style.RESET_ALL, end="")
                            print(f"User message is currently newest and buffer time not passed. Directly writing to database...")

                            message["topic"] = ""
                            message["answered"] = None
                            message["processed"] = False
                            RUNTIME_PARAMS["unprocessed_exists"] = True

                            create_chat_db_entry(message)
                            continue

                    # We want to find where the value of the user message's index is in the list "user_message_indices" and take the previous k user message indices. 
                    message_idx_idx = user_message_indices.index(message_idx)
                    user_chat_history_idxs = user_message_indices[max(0, message_idx_idx-chat_history_k):message_idx_idx]
                    if user_chat_history_idxs == []:
                        user_chat_history_idxs = [0]

                    # We take the oldest user_chat_history and use that up until the user message idx to construct the chat history.
                    oldest_user_chat_history_idx = user_chat_history_idxs[0]
                    previous_chat_history_list = []
                    for idx in range(oldest_user_chat_history_idx, message_idx):
                        previous_chat_history_list.append(conversation_history[idx])

                    # Construct chat history string
                    ## Starting from Previous Chat History
                    previous_chat_history = ""
                    for previous_message in previous_chat_history_list:
                        previous_chat_history += f'{previous_message["author"]}: {previous_message["message"]}\n'
                    
                    ## Current User Message and Assistant Message (until next User Message - assuming at least 1 assistant message in between)
                    current_chat_history = ""
                    current_chat_history += f'User: {conversation_history[message_idx]["message"]}\n'

                    assistant_message_exist = False
                    if message_idx == unprocessed_user_message_indices[-1]:
                        for idx in range(message_idx+1, len(conversation_history)):
                            current_chat_history += f'{conversation_history[idx]["author"]}: {conversation_history[idx]["message"]}\n'
                    else:
                        for idx in range(message_idx+1, unprocessed_user_message_indices[-1]):
                            if assistant_message_exist:
                                if conversation_history[idx]["author"] == "User":
                                    break
                            else:
                                if conversation_history[idx]["author"] == "Assistant":
                                    assistant_message_exist = True
                            current_chat_history += f'{conversation_history[idx]["author"]}: {conversation_history[idx]["message"]}\n'

                    # Process answered_detection and topic_detection
                    print(str(datetime.now()) + " | ", end="")
                    print(Fore.YELLOW + "[PROCESS][MESSAGE][ANSWERED_DET] " + Style.RESET_ALL, end="")
                    print(f"Detecting 'answered'...")
                    try:
                        print(previous_chat_history + current_chat_history)
                        answered_dict = answered_detection.predict(previous_chat_history + current_chat_history)
                        message["answered"] = answered_dict["answered"]
                        message["processed"] = True
                    except:
                        message["answered"] = None
                        message["processed"] = True#False
                        #RUNTIME_PARAMS["unprocessed_exists"] = True

                    print(str(datetime.now()) + " | ", end="")
                    print(Fore.YELLOW + "[PROCESS][MESSAGE][ANSWERED_DET] " + Style.RESET_ALL, end="")
                    print(f"Set 'answered' as {message['answered']}")
                    
                    print(str(datetime.now()) + " | ", end="")
                    print(Fore.YELLOW + "[PROCESS][MESSAGE][TOPIC_DET] " + Style.RESET_ALL, end="")
                    print(f"Detecting 'topic'...")
                    try:
                        print(current_chat_history)
                        topic_dict = topic_detection.predict(current_chat_history)
                        message["topic"] = topic_dict["topic"]
                    except:
                        message["topic"] = "unknown"
                    print(str(datetime.now()) + " | ", end="")
                    print(Fore.YELLOW + "[PROCESS][MESSAGE][TOPIC_DET] " + Style.RESET_ALL, end="")
                    print(f"Set topic as {message['topic']}")

                elif message['author'] == "Assistant":
                    # If Message is from Assistant, we don't need to process it
                    message["topic"] = ""
                    message["answered"] = None
                    message["processed"] = True
                
                else:
                    raise Exception(f"Invalid Author: Must be either 'User' or 'Assistant', got {message['author']}")

                # Construct ChatHistory and Write to MongoDB
                create_chat_db_entry(message)  

            print(str(datetime.now()) + " | ", end="")
            print(Fore.GREEN + "[PROCESS] " + Style.RESET_ALL, end="")
            print(f"Processs done for conversation_id: {conversation_id}")

        print(str(datetime.now()) + " | ", end="")
        print(Fore.GREEN + "[END] " + Style.RESET_ALL, end="")
        print("Process Finished.")

# ----------------- #

def main():
    """
    Runs in the background to process botpress chat histories and write results to dashboard database.
    """
    print("")
    print(str(datetime.now()) + " | ", end="")
    print(Fore.GREEN + "[BOOT] " + Style.RESET_ALL, end="")
    print("Standing by for process...")
    while True:
        process()
        time.sleep(10)

if __name__ == "__main__":
    main()
