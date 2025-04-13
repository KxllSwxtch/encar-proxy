import httpx
import random
from fastapi import FastAPI, Query
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

# @app.get("/api/catalog")
# async def proxy_catalog(q: str = Query(...), sr: str = Query(...)):
#     url = f"https://api-encar.habsidev.com/api/catalog?count=true&q={q}&sr={sr}"

#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)

#     return response.json()


@app.get("/api/catalog")
async def proxy_catalog(q: str = Query(...), sr: str = Query(...)):
    url = f"https://api.encar.com/search/car/list/general?count=true&q={q}&sr={sr}"

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en,ru;q=0.9,en-CA;q=0.8,la;q=0.7,fr;q=0.6,ko;q=0.5",
        "Origin": "http://www.encar.com",
        "Referer": "http://www.encar.com/",
        "User-Agent": random.choice(
            [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            ]
        ),
    }

    print(f"Making request to URL: {url}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)

            print(f"Response status: {response.status_code}")
            print(f"Response headers: {response.headers}")

            if response.status_code != 200:
                print(f"Error response content: {response.text}")
                return {
                    "error": f"API returned status code {response.status_code}",
                    "content": response.text,
                }

            try:
                return response.json()
            except Exception as e:
                print(f"JSON decode error: {str(e)}")
                print(f"Response content: {response.text}")
                return {
                    "error": "Failed to parse JSON from API",
                    "content": response.text,
                }

    except Exception as e:
        print(f"Request error: {str(e)}")
        return {"error": f"Failed to connect to API: {str(e)}"}
