import random
import urllib.parse
import requests  # Use requests instead of httpx
import asyncio  # For running requests in a thread pool
import os  # For environment variables
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Disable proxy environment variables
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""
os.environ["http_proxy"] = ""
os.environ["https_proxy"] = ""
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

app = FastAPI()

# CORS — разрешаем localhost:5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Headers matching real API requests
def get_api_headers():
    return {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "en,ru;q=0.9,en-CA;q=0.8,la;q=0.7,fr;q=0.6,ko;q=0.5",
        "accept-encoding": "gzip, deflate, br",
        "cache-control": "no-cache",
        "origin": "http://www.encar.com",
        "priority": "u=1, i",
        "referer": "http://www.encar.com/",
        "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }


@app.get("/api/catalog")
async def proxy_catalog(q: str = Query(...), sr: str = Query(...)):
    """
    Proxy endpoint for /api/catalog requests
    Uses api.encar.com search endpoint for catalog data
    """
    # Keep track of all attempts
    attempts = []

    print(f"Catalog request - q: {q}, sr: {sr}")

    # Use direct API endpoint - updated to /general
    api_url = f"https://api.encar.com/search/car/list/general?count=true&q={q}&sr={sr}"
    print(f"Catalog API URL: {api_url}")

    # Get proper headers for API requests
    headers = get_api_headers()

    try:
        # Define a function to make a synchronous request using requests
        def make_request(url):
            try:
                print(f"Making catalog request to: {url}")
                # Create session with disabled environment trust
                session = requests.Session()
                session.trust_env = False  # Disable reading proxy from environment
                session.proxies = {}  # Explicitly disable proxy

                response = session.get(
                    url,
                    headers=headers,
                    timeout=30.0,
                    allow_redirects=True,
                    verify=True,
                )
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "text": response.text,
                    "url": url,
                }
            except Exception as e:
                print(f"Catalog request error: {str(e)}")
                return {"success": False, "error": str(e), "url": url}

        # Make the API request
        loop = asyncio.get_event_loop()
        response_data = await loop.run_in_executor(None, lambda: make_request(api_url))

        if not response_data["success"]:
            print(f"Catalog API request failed: {response_data['error']}")
            attempts.append(
                {"url": response_data["url"], "error": response_data["error"]}
            )
            return JSONResponse(
                status_code=502,
                content={
                    "error": f"Catalog API request failed: {response_data['error']}",
                    "attempts": attempts,
                },
            )

        status_code = response_data["status_code"]
        response_text = response_data["text"]
        print(f"Catalog API response status code: {status_code}")

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
                    print(f"Empty response from catalog API")
                    return JSONResponse(
                        status_code=502,
                        content={
                            "error": "Empty response from catalog API",
                            "attempts": attempts,
                        },
                    )

                print(
                    f"Catalog response text sample: {response_text[:200] if response_text else 'Empty'}"
                )

                # Check if response is HTML instead of JSON
                if response_text.strip().startswith(
                    "<!DOCTYPE html>"
                ) or response_text.strip().startswith("<html"):
                    print(f"Received HTML instead of JSON from catalog API")
                    return JSONResponse(
                        status_code=502,
                        content={
                            "error": "Received HTML instead of JSON from catalog API",
                            "attempts": attempts,
                            "preview": response_text[:500],
                        },
                    )

                json_data = json.loads(response_text)
                return json_data
            except Exception as e:
                print(f"Catalog JSON decode error: {str(e)}")
                print(f"Catalog response text: {response_text[:500]}")
                return JSONResponse(
                    status_code=502,
                    content={
                        "error": f"Failed to decode catalog JSON: {str(e)}",
                        "attempts": attempts,
                        "preview": response_text[:500],
                    },
                )

        # If we get here, the request did not return 200
        return JSONResponse(
            status_code=status_code,
            content={
                "error": f"Catalog API returned non-200 status: {status_code}",
                "attempts": attempts,
            },
        )
    except Exception as e:
        print(f"Unexpected catalog error: {str(e)}")
        return JSONResponse(
            status_code=502,
            content={"error": f"Failed to connect to catalog API: {str(e)}"},
        )


@app.get("/api/nav")
async def proxy_nav(
    q: str = Query(...),
    inav: str = Query(...),
    count: str = Query(default="true"),
    cursor: str = Query(default=""),
):
    """
    Proxy endpoint for /api/nav requests
    Uses api.encar.com search endpoint for navigation data
    """
    # Keep track of all attempts
    attempts = []

    print(f"Nav request - q: {q}, inav: {inav}, count: {count}, cursor: {cursor}")

    # Use direct API endpoint - updated to /general with inav parameter
    api_url = f"https://api.encar.com/search/car/list/general?count={count}&q={q}&inav={inav}&cursor={cursor}"
    print(f"Nav API URL: {api_url}")

    # Get proper headers for API requests
    headers = get_api_headers()

    try:
        # Define a function to make a synchronous request using requests
        def make_request(url):
            try:
                print(f"Making nav request to: {url}")
                # Create session with disabled environment trust
                session = requests.Session()
                session.trust_env = False  # Disable reading proxy from environment
                session.proxies = {}  # Explicitly disable proxy

                response = session.get(
                    url,
                    headers=headers,
                    timeout=30.0,
                    allow_redirects=True,
                    verify=True,
                )
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "text": response.text,
                    "url": url,
                }
            except Exception as e:
                print(f"Nav request error: {str(e)}")
                return {"success": False, "error": str(e), "url": url}

        # Make the API request
        loop = asyncio.get_event_loop()
        response_data = await loop.run_in_executor(None, lambda: make_request(api_url))

        if not response_data["success"]:
            print(f"Nav API request failed: {response_data['error']}")
            attempts.append(
                {"url": response_data["url"], "error": response_data["error"]}
            )
            return JSONResponse(
                status_code=502,
                content={
                    "error": f"Nav API request failed: {response_data['error']}",
                    "attempts": attempts,
                },
            )

        status_code = response_data["status_code"]
        response_text = response_data["text"]
        print(f"Nav API response status code: {status_code}")

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
                    print(f"Empty response from nav API")
                    return JSONResponse(
                        status_code=502,
                        content={
                            "error": "Empty response from nav API",
                            "attempts": attempts,
                        },
                    )

                print(
                    f"Nav response text sample: {response_text[:200] if response_text else 'Empty'}"
                )

                # Check if response is HTML instead of JSON
                if response_text.strip().startswith(
                    "<!DOCTYPE html>"
                ) or response_text.strip().startswith("<html"):
                    print(f"Received HTML instead of JSON from nav API")
                    return JSONResponse(
                        status_code=502,
                        content={
                            "error": "Received HTML instead of JSON from nav API",
                            "attempts": attempts,
                            "preview": response_text[:500],
                        },
                    )

                json_data = json.loads(response_text)
                return json_data
            except Exception as e:
                print(f"Nav JSON decode error: {str(e)}")
                print(f"Nav response text: {response_text[:500]}")
                return JSONResponse(
                    status_code=502,
                    content={
                        "error": f"Failed to decode nav JSON: {str(e)}",
                        "attempts": attempts,
                        "preview": response_text[:500],
                    },
                )

        # If we get here, the request did not return 200
        return JSONResponse(
            status_code=status_code,
            content={
                "error": f"Nav API returned non-200 status: {status_code}",
                "attempts": attempts,
            },
        )
    except Exception as e:
        print(f"Unexpected nav error: {str(e)}")
        return JSONResponse(
            status_code=502,
            content={"error": f"Failed to connect to nav API: {str(e)}"},
        )
