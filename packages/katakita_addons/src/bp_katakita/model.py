from pydantic import BaseModel
from typing import List, Optional, Tuple
from datetime import datetime

# ----------------- #

class DashboardChatHistory(BaseModel):
    user_id: Optional[str] = None
    botpress_message_id: str
    botpress_conversation_id: str
    datetime: datetime
    message: str
    author: str
    topic: str=""
    answered: Optional[bool]=None

# ----------------- #