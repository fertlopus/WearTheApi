from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def main_page():
    return {
        "version": "v1",
        "application": "WearThe API for recommendations"
    }