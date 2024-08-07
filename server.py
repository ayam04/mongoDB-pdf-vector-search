from fastapi import FastAPI
from find_pdf import search_candidates
import uvicorn

app = FastAPI()

@app.post("/query")
async def search_db(jd: str):
    try:
        candidates = search_candidates(jd)
        return {"candidates": candidates}
    except Exception as e:
        return {"error": str(e)}

@app.post("/update-db")
async def update_db():
    pass

if __name__ == "__main__":
    uvicorn.run(app, port=8080)