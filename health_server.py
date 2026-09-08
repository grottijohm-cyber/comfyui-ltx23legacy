import os
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/ping")
def ping():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.getenv("PORT_HEALTH") or os.getenv("PORT") or "80")
    uvicorn.run(app, host="0.0.0.0", port=port)
