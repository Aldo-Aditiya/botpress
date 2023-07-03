from fastapi import FastAPI, Request, HTTPException
import uvicorn
from pprint import pprint
from typing import List

from bp_katakita.config import load_config
from bp_katakita.chatgpt_nlu.nlu_engine import save_intents, get_intents
from bp_katakita.chatgpt_nlu.model import NLUDataSync, NLUProcess

# ----------------- #

app = FastAPI()
CONFIG = load_config()

# ----------------- #

@app.post("/nlu/sync_data")
async def nlu_sync_data(args:NLUDataSync):
    try:
        save_intents(args)
        return {"message": "OK"}
    except Exception as e:
        print(e)
        return HTTPException(status_code=500, detail=e)

@app.post("/nlu/process")
async def nlu_process(args:NLUProcess):
    return {"message": "Hello World"}

# ----------------- #

def main():
    uvicorn.run(app, host=CONFIG["NLU_SERVER"]["host"], port=int(CONFIG["NLU_SERVER"]["port"]))

if __name__ == "__main__":
    main()