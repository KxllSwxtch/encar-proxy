import random
import urllib.parse
import requests  # Use requests instead of httpx
import asyncio  # For running requests in a thread pool
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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

    # Use the proxy endpoint instead of direct API access
    proxy_url = (
        f"https://encar-proxy.habsida.net/api/catalog?count=true&q={q}&sr={encoded_sr}"
    )
    print(f"Proxy URL: {proxy_url}")

    # Backup URL if the first one fails
    backup_proxy_url = (
        f"https://encar-proxy.habsida.net/api/catalog?count=true&q={q}&sr={sr}"
    )
    print(f"Backup URL: {backup_proxy_url}")

    # Simple headers for proxy request
    headers = {
        "accept": "application/json",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    }

    try:
        # Define a function to make a synchronous request using requests
        def make_request(url):
            try:
                print(f"Making request to: {url}")
                response = requests.get(url, headers=headers, timeout=30.0)
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "text": response.text,
                    "url": url,
                }
            except Exception as e:
                print(f"Request error: {str(e)}")
                return {"success": False, "error": str(e), "url": url}

        # Try first the primary proxy URL
        loop = asyncio.get_event_loop()
        response_data = await loop.run_in_executor(
            None, lambda: make_request(proxy_url)
        )

        # If first request fails, try the backup URL
        if not response_data["success"] or response_data["status_code"] != 200:
            print(f"First proxy attempt failed. Trying backup URL...")
            response_data = await loop.run_in_executor(
                None, lambda: make_request(backup_proxy_url)
            )

        if not response_data["success"]:
            print(f"Proxy request failed: {response_data['error']}")
            attempts.append(
                {"url": response_data["url"], "error": response_data["error"]}
            )
            return JSONResponse(
                status_code=502,
                content={
                    "error": f"Proxy request failed: {response_data['error']}",
                    "attempts": attempts,
                },
            )

        status_code = response_data["status_code"]
        response_text = response_data["text"]
        print(f"Proxy response status code: {status_code}")

        attempts.append(
            {
                "url": response_data["url"],
                "status_code": status_code,
                "content_length": len(response_text) if response_text else 0,
            }
        )

        if status_code == 200:
            try:
                import json

                if not response_text or response_text.strip() == "":
                    print(f"Empty response from proxy")
                    return JSONResponse(
                        status_code=502,
                        content={
                            "error": "Empty response from proxy",
                            "attempts": attempts,
                        },
                    )

                print(
                    f"Response text sample: {response_text[:200] if response_text else 'Empty'}"
                )

                # Check if response is HTML instead of JSON
                if response_text.strip().startswith(
                    "<!DOCTYPE html>"
                ) or response_text.strip().startswith("<html"):
                    print(f"Received HTML instead of JSON from proxy")
                    return JSONResponse(
                        status_code=502,
                        content={
                            "error": "Received HTML instead of JSON from proxy",
                            "attempts": attempts,
                            "preview": response_text[:500],
                        },
                    )

                json_data = json.loads(response_text)
                return json_data
            except Exception as e:
                print(f"JSON decode error: {str(e)}")
                print(f"Response text: {response_text[:500]}")
                return JSONResponse(
                    status_code=502,
                    content={
                        "error": f"Failed to decode JSON: {str(e)}",
                        "attempts": attempts,
                        "preview": response_text[:500],
                    },
                )

        # If we get here, the request did not return 200
        return JSONResponse(
            status_code=status_code,
            content={
                "error": f"Proxy returned non-200 status: {status_code}",
                "attempts": attempts,
            },
        )
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return JSONResponse(
            status_code=502, content={"error": f"Failed to connect to proxy: {str(e)}"}
        )
