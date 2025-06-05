import requests  # Use requests instead of httpx
import asyncio  # For running requests in a thread pool
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# CORS — разрешаем localhost:5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

proxy_config = {
    "http": "http://B01vby:GBno0x@45.118.250.2:8000",
    "https": "http://B01vby:GBno0x@45.118.250.2:8000",
}


# Function to get proper headers matching the working curlrequest.py example
def get_proper_headers():
    return {
        "accept": "*/*",
        "accept-language": "en,ru;q=0.9,en-CA;q=0.8,la;q=0.7,fr;q=0.6,ko;q=0.5",
        "origin": "https://cars.prokorea.trading",
        "priority": "u=1, i",
        "referer": "https://cars.prokorea.trading/",
        "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    }


@app.get("/api/catalog")
async def proxy_catalog(q: str = Query(...), sr: str = Query(...)):
    # Keep track of all attempts
    attempts = []

    # Manually ensure the pipe characters are encoded properly
    encoded_sr = sr.replace("|", "%7C")

    # Use the proxy endpoint instead of direct API access
    proxy_url = (
        f"https://encar-proxy.habsida.net/api/catalog?count=true&q={q}&sr={encoded_sr}"
    )

    # Backup URL if the first one fails
    backup_proxy_url = (
        f"https://encar-proxy.habsida.net/api/catalog?count=true&q={q}&sr={sr}"
    )

    # Proper headers for proxy request matching working example
    headers = get_proper_headers()

    try:
        # Define a function to make a synchronous request using requests
        def make_request(url):
            try:
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
                    return JSONResponse(
                        status_code=502,
                        content={
                            "error": "Empty response from proxy",
                            "attempts": attempts,
                        },
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


@app.get("/api/nav")
async def proxy_nav(
    q: str = Query(...), inav: str = Query(...), count: str = Query(default="true")
):
    """
    Proxy endpoint for /api/nav requests
    Handles navigation API calls with proper parameter encoding
    """
    # Keep track of all attempts
    attempts = []

    # Manually ensure special characters are encoded properly
    encoded_q = q.replace("|", "%7C")
    encoded_inav = inav.replace("|", "%7C")

    # Use the proxy endpoint for nav API
    proxy_url = f"https://encar-proxy.habsida.net/api/nav?count={count}&q={encoded_q}&inav={encoded_inav}"
    print(f"Nav Proxy URL: {proxy_url}")

    # Backup URL if the first one fails
    backup_proxy_url = (
        f"https://encar-proxy.habsida.net/api/nav?count={count}&q={q}&inav={inav}"
    )
    print(f"Nav Backup URL: {backup_proxy_url}")

    # Proper headers for proxy request matching working example
    headers = get_proper_headers()

    try:
        # Define a function to make a synchronous request using requests
        def make_request(url):
            try:
                print(f"Making nav request to: {url}")
                response = requests.get(url, headers=headers, timeout=30.0)
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "text": response.text,
                    "url": url,
                }
            except Exception as e:
                print(f"Nav request error: {str(e)}")
                return {"success": False, "error": str(e), "url": url}

        # Try first the primary proxy URL
        loop = asyncio.get_event_loop()
        response_data = await loop.run_in_executor(
            None, lambda: make_request(proxy_url)
        )

        # If first request fails, try the backup URL
        if not response_data["success"] or response_data["status_code"] != 200:
            print(f"First nav proxy attempt failed. Trying backup URL...")
            response_data = await loop.run_in_executor(
                None, lambda: make_request(backup_proxy_url)
            )

        if not response_data["success"]:
            print(f"Nav proxy request failed: {response_data['error']}")
            attempts.append(
                {"url": response_data["url"], "error": response_data["error"]}
            )
            return JSONResponse(
                status_code=502,
                content={
                    "error": f"Nav proxy request failed: {response_data['error']}",
                    "attempts": attempts,
                },
            )

        status_code = response_data["status_code"]
        response_text = response_data["text"]
        print(f"Nav proxy response status code: {status_code}")

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
                    print(f"Empty response from nav proxy")
                    return JSONResponse(
                        status_code=502,
                        content={
                            "error": "Empty response from nav proxy",
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
                    print(f"Received HTML instead of JSON from nav proxy")
                    return JSONResponse(
                        status_code=502,
                        content={
                            "error": "Received HTML instead of JSON from nav proxy",
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
                "error": f"Nav proxy returned non-200 status: {status_code}",
                "attempts": attempts,
            },
        )
    except Exception as e:
        print(f"Unexpected nav error: {str(e)}")
        return JSONResponse(
            status_code=502,
            content={"error": f"Failed to connect to nav proxy: {str(e)}"},
        )
