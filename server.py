from fastapi import FastAPI, Query
from find_pdf import search_candidates
from update_existing import update_candidate
import uvicorn
from pydantic import BaseModel
from typing import List
from bson import ObjectId

app = FastAPI()

@app.post("/query")
async def search_db(jd: str):
    try:
        candidates = search_candidates(jd)
        return {"candidates": candidates}
    except Exception as e:
        return {"error": str(e)}

class UpdateRequest(BaseModel):
    ids: List[str]

@app.post("/update-db")
async def update_db(request: UpdateRequest):
    try:
        # object_ids = [ObjectId(id_str) for id_str in request.ids]
        update_candidate(request.ids)
        
        return {"message": "Database updated"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, port=8080)