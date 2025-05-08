import random
import urllib.parse
import requests
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio

app = FastAPI()

# CORS — разрешаем localhost:5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:5173"],
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
    # Keep track of all attempts
    attempts = []

    # Manually ensure the pipe characters are encoded properly
    encoded_sr = sr.replace("|", "%7C")
    print(f"Original sr: {sr}")
    print(f"Encoded sr: {encoded_sr}")

    # Use the new proxy endpoint URL
    url = (
        f"https://encar-proxy.habsida.net/api/catalog?count=true&q={q}&sr={encoded_sr}"
    )
    print(f"URL: {url}")

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://m.encar.com",
        "Referer": "https://m.encar.com/index.html",
        "User-Agent": random.choice(
            [
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
                "Mozilla/5.0 (iPad; CPU OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
            ]
        ),
    }

    cookies = {
        "PCID": "17422557868404555606353",
        "PERSISTENT_USERTYPE": "1",
        "wcs_bt": "4b4e532670e38c:1744590425",
    }

    try:
        # Using requests in a separate thread to avoid blocking
        def make_request():
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    cookies=cookies,
                    allow_redirects=True,
                    timeout=20.0,
                )
                return {
                    "status_code": response.status_code,
                    "text": response.text,
                    "success": True,
                }
            except Exception as e:
                return {"success": False, "error": str(e)}

        # Run the request in a thread pool
        loop = asyncio.get_event_loop()
        response_data = await loop.run_in_executor(None, make_request)

        if not response_data["success"]:
            print(f"Request error: {response_data['error']}")
            attempts.append({"url": url, "error": response_data["error"]})
            return JSONResponse(
                status_code=502,
                content={
                    "error": f"Request failed: {response_data['error']}",
                    "attempts": attempts,
                },
            )

        response_status = response_data["status_code"]
        response_text = response_data["text"]
        print(f"Response status: {response_status}")

        attempts.append(
            {
                "url": url,
                "status_code": response_status,
                "content_length": len(response_text) if response_text else 0,
            }
        )

        if response_status == 200:
            try:
                import json

                json_data = json.loads(response_text)
                return json_data
            except Exception as e:
                print(f"JSON decode error: {str(e)}")
                return JSONResponse(
                    status_code=502,
                    content={
                        "error": f"Failed to decode JSON: {str(e)}",
                        "attempts": attempts,
                    },
                )

        # If we get here, the request did not return 200
        return JSONResponse(
            status_code=502,
            content={
                "error": f"API request failed with status {response_status}",
                "attempts": attempts,
            },
        )

    except Exception as e:
        print(f"Client creation error: {str(e)}")
        return JSONResponse(
            status_code=502, content={"error": f"Failed to connect to API: {str(e)}"}
        )
