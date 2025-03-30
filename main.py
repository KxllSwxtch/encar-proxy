from fastapi import FastAPI, Query
import httpx
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS — разрешаем localhost:5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/catalog")
async def proxy_catalog(q: str = Query(...), sr: str = Query(...)):
    url = f"https://api-encar.habsidev.com/api/catalog?count=true&q={q}&sr={sr}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    return response.json()