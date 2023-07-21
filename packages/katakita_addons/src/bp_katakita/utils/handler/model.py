from pydantic import BaseModel
from typing import List, Optional, Tuple
from datetime import datetime

# ----------------- #

class ChatHistory(BaseModel):
    message_id: str
    session_id: str
    bot_id: str
    datetime: datetime
    message: str
    author: str
    topic: str = ""
    answered: Optional[str] = None

class ConversationAnalytics(BaseModel):
    bot_id: str
    session_id: str
    datetime: datetime
    first_response_time: float
    avg_response_time: float
    duration: float
    wait_time: float
    sentiment: str = ""
    summary: str = ""

class RawChatHistory(BaseModel):
    message_id: str
    session_id: str
    bot_id: str
    datetime: datetime
    message: str
    author: str

# ----------------- #