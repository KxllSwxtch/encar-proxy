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
    # Ensure query is properly URL encoded
    encoded_q = urllib.parse.quote(q, safe="()")
    print(f"Original sr: {sr}")
    print(f"Encoded sr: {encoded_sr}")
    print(f"Original q: {q}")
    print(f"Encoded q: {encoded_q}")

    # Use the new proxy endpoint URL with encoded parameters
    url = f"https://encar-proxy.habsida.net/api/catalog?count=true&q={encoded_q}&sr={encoded_sr}"
    print(f"URL: {url}")

    # Try alternate URL if needed
    alternate_url = (
        f"https://encar-proxy.habsida.net/api/catalog?count=true&q={q}&sr={sr}"
    )
    print(f"Alternate URL (without manual encoding): {alternate_url}")

    # Try direct Encar API as a third fallback
    direct_url = f"https://api.encar.com/search/car/list/mobile?count=true&q={encoded_q}&sr={encoded_sr}"
    print(f"Direct URL (to original API): {direct_url}")

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://m.encar.com",
        "Referer": "https://m.encar.com/index.html",
        "Content-Type": "application/json",
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
        def make_request(request_url):
            try:
                print(f"Trying request to URL: {request_url}")
                response = requests.get(
                    request_url,
                    headers=headers,
                    cookies=cookies,
                    allow_redirects=True,
                    timeout=20.0,
                )
                return {
                    "status_code": response.status_code,
                    "text": response.text,
                    "success": True,
                    "url": request_url,
                }
            except Exception as e:
                return {"success": False, "error": str(e), "url": request_url}

        # Run the first request in a thread pool
        loop = asyncio.get_event_loop()
        response_data = await loop.run_in_executor(None, lambda: make_request(url))

        # If first request fails or returns empty, try alternate URL
        if not response_data["success"] or (
            response_data["success"]
            and response_data["status_code"] == 200
            and not response_data["text"].strip()
        ):
            print(f"First request failed or returned empty. Trying alternate URL...")
            response_data = await loop.run_in_executor(
                None, lambda: make_request(alternate_url)
            )

            # If second request fails or returns empty, try direct URL
            if not response_data["success"] or (
                response_data["success"]
                and response_data["status_code"] == 200
                and not response_data["text"].strip()
            ):
                print(
                    f"Second request failed or returned empty. Trying direct Encar API..."
                )
                response_data = await loop.run_in_executor(
                    None, lambda: make_request(direct_url)
                )

        if not response_data["success"]:
            print(f"Request error: {response_data['error']}")
            attempts.append(
                {"url": response_data["url"], "error": response_data["error"]}
            )
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
                "url": response_data["url"],
                "status_code": response_status,
                "content_length": len(response_text) if response_text else 0,
            }
        )

        if response_status == 200:
            try:
                import json

                if not response_text or response_text.strip() == "":
                    print(f"Empty response received from server")
                    return JSONResponse(
                        status_code=502,
                        content={
                            "error": "Empty response received from server",
                            "attempts": attempts,
                        },
                    )

                # Log the response for debugging
                print(f"Response content (first 200 chars): {response_text[:200]}...")

                # Check if response is HTML instead of JSON (could indicate redirect or error page)
                if response_text.strip().startswith(
                    "<!DOCTYPE html>"
                ) or response_text.strip().startswith("<html"):
                    print("Received HTML instead of JSON")
                    return JSONResponse(
                        status_code=502,
                        content={
                            "error": "Received HTML instead of JSON",
                            "attempts": attempts,
                            "response_preview": response_text[:200],
                        },
                    )

                try:
                    json_data = json.loads(response_text)

                    # If JSON parsed but contains error field
                    if (
                        isinstance(json_data, dict)
                        and "error" in json_data
                        and json_data["error"]
                    ):
                        print(f"API returned error in JSON: {json_data['error']}")
                        return JSONResponse(
                            status_code=502,
                            content={
                                "error": f"API error: {json_data['error']}",
                                "attempts": attempts,
                            },
                        )

                    return json_data
                except json.JSONDecodeError as je:
                    # Specific JSON decoding error
                    print(f"JSON decode error: {str(je)}")
                    print(f"Raw response content: {response_text[:500]}")
                    return JSONResponse(
                        status_code=502,
                        content={
                            "error": f"Failed to decode JSON: {str(je)}",
                            "attempts": attempts,
                            "response_preview": response_text[:200],
                        },
                    )
            except Exception as e:
                print(f"Unexpected error processing response: {str(e)}")
                print(f"Raw response content: {response_text[:500]}")
                return JSONResponse(
                    status_code=502,
                    content={
                        "error": f"Unexpected error: {str(e)}",
                        "attempts": attempts,
                        "response_preview": (
                            response_text[:200] if response_text else ""
                        ),
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
