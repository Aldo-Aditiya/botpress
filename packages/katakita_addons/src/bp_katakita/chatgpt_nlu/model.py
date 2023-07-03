from pydantic import BaseModel
from typing import List, Optional

class Slot(BaseModel):
    name: str
    id: str
    entities: List[str]
    color: int

class Intent(BaseModel):
    name: str
    slots: List[Slot]
    entities: Optional[List] = []
    contexts: List[str]
    utterances: dict

class NLUDataSync(BaseModel):
    intents: List[Intent]
    bot_id: str

class NLUProcess(BaseModel):
    input: str
    bot_id: str