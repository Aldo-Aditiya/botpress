import pymongo
from pydantic import parse_obj_as

from chat_assistant.app.utils.mongodb import load_collection

from bp_katakita.config import load_config
from bp_katakita.utils.handler.model import RawChatHistory

# ----------------- #

CONFIG = load_config()

# Connect to the database
DB_CONFIG = CONFIG["DATABASE"]
APP_DB_NAME = CONFIG["APP_DB"]["name"]
APP_DB_PARAMS = CONFIG["APP_DB"]["params"]
APP_DB_COLLECTION_NAME = CONFIG["APP_DB"]["collections"]["raw_chat_history"]

collection = load_collection(APP_DB_NAME, APP_DB_PARAMS, APP_DB_COLLECTION_NAME)

# ----------------- #

def create(chat_history:RawChatHistory):
    if APP_DB_NAME == "mongo-db":
        message_id = chat_history.message_id
        mongodb_chat_history = collection.find_one({"message_id": message_id})
        if mongodb_chat_history is not None:
            raise Exception(f"RawChatHistory {message_id} already exists")
        result = collection.insert_one(chat_history.dict())
        return {"success": result.inserted_id is not None}

def read(message_id:str):
    if APP_DB_NAME == "mongo-db":
        try:
            chat_history = collection.find_one({"message_id": message_id})
            return parse_obj_as(RawChatHistory, chat_history)
        except:
            raise Exception(f"RawChatHistory {message_id} not found")

def update(chat_history:RawChatHistory):
    if APP_DB_NAME == "mongo-db":
        result = collection.update_one({"message_id": chat_history.message_id}, {"$set": chat_history})
        return {"success": result.modified_count > 0}
     
def delete(message_id:str):
    if APP_DB_NAME == "mongo-db":
        result = collection.delete_one({"message_id": message_id})
        return {"success": result.deleted_count > 0}