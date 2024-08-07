from fastapi import FastAPI, Query
from find_pdf import search_candidates
from update_existing import update_candidate
import uvicorn
from typing import List

app = FastAPI()

@app.post("/query")
async def search_db(jd: str):
    try:
        candidates = search_candidates(jd)
        return {"candidates": candidates}
    except Exception as e:
        return {"error": str(e)}

@app.post("/update-db")
async def update_db(ids: List[str] = Query(...)):
    try:
        update_candidate(ids)
        return {"message": "Database updated"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, port=8080)