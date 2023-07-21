import pymongo
import pandas as pd
from typing import Optional
from pydantic import parse_obj_as

from chat_assistant.app.utils.mongodb import load_collection

from bp_katakita.config import load_config
from bp_katakita.utils.handler.model import ConversationAnalytics

# ----------------- #

CONFIG = load_config()

# Connect to the database
DB_CONFIG = CONFIG["DATABASE"]
APP_DB_NAME = CONFIG["APP_DB"]["name"]
APP_DB_PARAMS = CONFIG["APP_DB"]["params"]
APP_DB_COLLECTION_NAME = CONFIG["APP_DB"]["collections"]["conversation_analytics"]

collection = load_collection(APP_DB_NAME, APP_DB_PARAMS, APP_DB_COLLECTION_NAME)

# ----------------- #

def read_as_df(limit:int=1000, query:Optional[str]=None):
    if APP_DB_NAME == "mongo-db":
        if query is not None:
            conversation_analytics = list(collection.find(query).sort("datetime", -1).limit(limit))
        else:
            conversation_analytics = list(collection.find().sort("datetime", -1).limit(limit))
        return pd.DataFrame(conversation_analytics)

def create(conversation_analytics:ConversationAnalytics):
    if APP_DB_NAME == "mongo-db":
        session_id = conversation_analytics.session_id
        mongodb_conversation_analytics = collection.find_one({"session_id": session_id})
        if mongodb_conversation_analytics is not None:
            raise Exception(f"ConversationAnalytics {session_id} already exists")
        result = collection.insert_one(conversation_analytics.dict())
        return {"success": result.inserted_id is not None}

def read(session_id:str):
    if APP_DB_NAME == "mongo-db":
        try:
            conversation_analytics = collection.find_one({"session_id": session_id})
            return parse_obj_as(ConversationAnalytics, conversation_analytics)
        except:
            raise Exception(f"ConversationAnalytics {session_id} not found")

def update(conversation_analytics:ConversationAnalytics):
    if APP_DB_NAME == "mongo-db":
        result = collection.update_one({"session_id": conversation_analytics.session_id}, {"$set": conversation_analytics.dict()})
        return {"success": result.modified_count > 0}
     
def delete(session_id:str):
    if APP_DB_NAME == "mongo-db":
        result = collection.delete_one({"session_id": session_id})
        return {"success": result.deleted_count > 0}