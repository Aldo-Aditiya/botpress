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
    answered: Optional[bool] = None

class RawChatHistory(BaseModel):
    message_id: str
    session_id: str
    bot_id: str
    datetime: datetime
    message: str
    author: str

# ----------------- #