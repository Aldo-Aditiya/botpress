import time
from datetime import datetime, timedelta, timezone
import pytz

from colorama import Fore, Back, Style
from typing import List, Tuple
from collections import defaultdict

from bp_katakita.analytics import (
    conversation_insight_detection,
)
from bp_katakita.config import load_config
from bp_katakita.utils.handler import chat_history as chat_history_handler
from bp_katakita.utils.handler import conversation_analytics as conversation_analytics_handler
from bp_katakita.utils.handler.model import ConversationAnalytics

# ----------------- #

CONFIG = load_config()

RUNTIME_PARAMS = {}

# ----------------- #

def create_conversation_analytics_db_entry(analytics:dict):
    chat_db_entry = ConversationAnalytics(
        session_id=analytics["session_id"],
        bot_id=analytics["bot_id"],
        datetime=analytics["datetime"],
        first_response_time=analytics["first_response_time"],
        avg_response_time=analytics["avg_response_time"],
        duration=analytics["duration"],
        wait_time=analytics["wait_time"],
        sentiment=analytics["sentiment"],
        summary=analytics["summary"]
    )

    result = conversation_analytics_handler.collection.find_one({"session_id": analytics["session_id"]})
    if result is None:
        print(str(datetime.now()) + " | ", end="")
        print(Fore.YELLOW + "[PROCESS][CONVERSATION] " + Style.RESET_ALL, end="")
        print(f"Writing to database, for session_id: {analytics['session_id']}")
        _ = conversation_analytics_handler.create(chat_db_entry)  
    else:
        print(str(datetime.now()) + " | ", end="")
        print(Fore.YELLOW + "[PROCESS][CONVERSATION] " + Style.RESET_ALL, end="")
        print(f"Updating to database, for session_id: {analytics['session_id']}")
        _ = conversation_analytics_handler.update(chat_db_entry)

def get_next_assistant_idx(chat_history:List[dict], start_idx:int):
    idx = start_idx
    while chat_history[idx]["author"] != "Assistant":
        idx += 1
        if idx == len(chat_history):
            raise Exception("No Assistant Message Found")
    assistant_idx = idx

    return assistant_idx

def get_next_user_idx(chat_history:List[dict], start_idx:int):
    idx = start_idx
    while chat_history[idx]["author"] != "User":
        idx += 1
        if idx == len(chat_history):
            raise Exception("No User Message Found")
    user_idx = idx

    return user_idx

def calc_first_response_time(chat_history:List[dict]):
    first_user_msg_idx = get_next_user_idx(chat_history, 0)
    first_assistant_msg_idx = get_next_assistant_idx(chat_history, first_user_msg_idx)

    return (chat_history[first_assistant_msg_idx]["datetime"] - chat_history[first_user_msg_idx]["datetime"]).total_seconds()

def calc_avg_response_time(chat_history:List[dict]):
    user_idx = [idx for idx in range(len(chat_history)) if chat_history[idx]["author"] == "User"]
    response_time_list = []

    for idx in user_idx:
        try:
            assistant_idx = get_next_assistant_idx(chat_history, idx)
        except:
            continue
        response_time_list.append((chat_history[assistant_idx]["datetime"] - chat_history[idx]["datetime"]).total_seconds())

    return sum(response_time_list) / len(response_time_list)

# ----------------- #

def detect_conversation_history_changes(buffer_time_min:int=5):
    # Check if there are any new conversations, and if converastion buffer time has passed
    process_session_ids = []
    session_ids = chat_history_handler.collection.distinct("session_id")
    for session_id in session_ids:
        result = conversation_analytics_handler.collection.find_one({"session_id": session_id})
        if result is not None:
            continue
        else:
            # Check if conversation buffer time has passed
            chat_history = list(chat_history_handler.collection.find({"session_id": session_id}).sort("datetime", -1).limit(1))[0]
            chat_history_datetime = chat_history["datetime"]
            now = datetime.now()
            buffer_time = timedelta(minutes=buffer_time_min)
            if now - chat_history_datetime > buffer_time:
                process_session_ids.append(session_id)
            else:
                continue

    return process_session_ids

def process():
    process_session_ids = detect_conversation_history_changes()

    if process_session_ids == []:
        pass
    else:
        print("")
        print(str(datetime.now()) + " | ", end="")
        print(Fore.GREEN + "[START] " + Style.RESET_ALL, end="")
        print(f"Starting Process for session ids: {process_session_ids}")

        for session_id in process_session_ids:
            analytics = defaultdict()
            analytics["session_id"] = session_id
            analytics["bot_id"] = list(chat_history_handler.collection.find({"session_id": session_id}).limit(1))[0]["bot_id"]
            analytics["datetime"] = list(chat_history_handler.collection.find({"session_id": session_id}).sort("datetime", -1).limit(1))[0]["datetime"]

            print(str(datetime.now()) + " | ", end="")
            print(Fore.YELLOW + "[PROCESS][TIME_ANALYSIS] " + Style.RESET_ALL, end="")
            print(f"Calculating Time metrics for session_id: {session_id}")

            # Calculate Time Analytics
            chat_history = list(chat_history_handler.collection.find({"session_id": session_id}).sort("datetime", 1))
            try:
                analytics["first_response_time"] = calc_first_response_time(chat_history)
                analytics["avg_response_time"] = calc_avg_response_time(chat_history)
                analytics["duration"] = (chat_history[-1]["datetime"] - chat_history[0]["datetime"]).total_seconds()
                analytics["wait_time"] = analytics["first_response_time"]
            except:
                analytics["first_response_time"] = None
                analytics["avg_response_time"] = None
                analytics["duration"] = None
                analytics["wait_time"] = None

            print(str(datetime.now()) + " | ", end="")
            print(Fore.GREEN + "[PROCESS][TIME_ANALYSIS] " + Style.RESET_ALL, end="")
            print("Time analysis finished.")

            # Process Conversation Insight Analytics
            print(str(datetime.now()) + " | ", end="")
            print(Fore.YELLOW + "[PROCESS][CONVERSATION_INSIGHTS] " + Style.RESET_ALL, end="")
            print(f"Processing Conversation Insights (summary and sentiment)...")

            conversation_history_text = ""
            for chat in chat_history:
                conversation_history_text += chat["author"] + ": " + chat["message"] + "\n"

            try:
                conversation_insights_dict = conversation_insight_detection.predict(conversation_history_text)
                analytics["summary"] = conversation_insights_dict["summary"]
                analytics["sentiment"] = conversation_insights_dict["sentiment"]
            except:
                analytics["summary"] = ""
                analytics["sentiment"] = ""

            create_conversation_analytics_db_entry(analytics)
            
            print(str(datetime.now()) + " | ", end="")
            print(Fore.GREEN + "[PROCESS][CONVERSATION_INSIGHTS] " + Style.RESET_ALL, end="")
            print(f"Finished processing Conversation Insights.")

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
        time.sleep(120)

if __name__ == "__main__":
    main()