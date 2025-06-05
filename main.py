import requests  # Use requests instead of httpx
import asyncio  # For running requests in a thread pool
import json
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


@app.get("/api/catalog")
async def proxy_catalog(q: str = Query(...), sr: str = Query(...)):
    # Keep track of all attempts
    attempts = []

    # Manually ensure the pipe characters are encoded properly
    encoded_sr = sr.replace("|", "%7C")
    print(f"Original sr: {sr}")
    print(f"Encoded sr: {encoded_sr}")

    # Try direct API calls using proxy
    url1 = (
        f"https://api.encar.com/search/car/list/mobile?count=true&q={q}&sr={encoded_sr}"
    )
    url2 = f"https://api.encar.com/search/car/list/general?count=true&q={q}&sr={encoded_sr}"
    url3 = (
        f"https://encar-proxy.habsida.net/api/catalog?count=true&q={q}&sr={encoded_sr}"
    )

    print(f"URL 1: {url1}")
    print(f"URL 2: {url2}")
    print(f"URL 3: {url3}")

    # Setup proxy configuration
    proxy_config = {
        "http": "http://B01vby:GBno0x@45.118.250.2:8000",
        "https": "http://B01vby:GBno0x@45.118.250.2:8000",
    }

    # Headers for Encar API
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://m.encar.com",
        "Referer": "https://m.encar.com/",
        "User-Agent": "Mozilla/5.0 (Linux; Android 12; SM-S906N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36",
    }

    # Essential cookies
    cookies = {
        "PCID": "17422557868404555606353",
        "PERSISTENT_USERTYPE": "1",
        "wcs_bt": "4b4e532670e38c:1744590425",
    }

    try:
        # Define a function to make a synchronous request using requests with proxy
        def make_request(url, use_cookies=True):
            try:
                print(f"Making request to: {url}")
                request_cookies = cookies if use_cookies else None
                response = requests.get(
                    url,
                    headers=headers,
                    cookies=request_cookies,
                    proxies=proxy_config,
                    timeout=30.0,
                    verify=True,
                )
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "text": response.text,
                    "url": url,
                }
            except Exception as e:
                print(f"Request error: {str(e)}")
                return {"success": False, "error": str(e), "url": url}

        # Try all URLs in sequence
        urls = [url1, url2, url3]
        loop = asyncio.get_event_loop()

        for i, url in enumerate(urls, 1):
            print(f"Attempt {i}: Trying {url}")

            # For the habsida proxy (url3), don't use cookies
            use_cookies = i != 3

            response_data = await loop.run_in_executor(
                None, lambda u=url, uc=use_cookies: make_request(u, uc)
            )

            attempts.append(
                {
                    "url": response_data["url"],
                    "success": response_data["success"],
                    "status_code": response_data.get("status_code"),
                    "error": response_data.get("error"),
                    "content_length": (
                        len(response_data.get("text", ""))
                        if response_data.get("text")
                        else 0
                    ),
                }
            )

            if response_data["success"] and response_data["status_code"] == 200:
                try:
                    response_text = response_data["text"]

                    if not response_text or response_text.strip() == "":
                        print(f"Empty response from attempt {i}")
                        continue

                    print(
                        f"Response sample: {response_text[:200] if response_text else 'Empty'}"
                    )

                    # Check if response is HTML instead of JSON
                    if response_text.strip().startswith(
                        "<!DOCTYPE html>"
                    ) or response_text.strip().startswith("<html"):
                        print(f"Received HTML instead of JSON from attempt {i}")
                        continue

                    json_data = json.loads(response_text)
                    print(f"Successfully got JSON from attempt {i}")
                    return json_data

                except Exception as e:
                    print(f"JSON decode error on attempt {i}: {str(e)}")
                    continue
            else:
                print(
                    f"Attempt {i} failed: Status {response_data.get('status_code')}, Error: {response_data.get('error')}"
                )

        # If we get here, all attempts failed
        return JSONResponse(
            status_code=502,
            content={"error": "All API attempts failed", "attempts": attempts},
        )

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return JSONResponse(
            status_code=502, content={"error": f"Failed to connect to API: {str(e)}"}
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

    print(f"Original q: {q}")
    print(f"Encoded q: {encoded_q}")
    print(f"Original inav: {inav}")
    print(f"Encoded inav: {encoded_inav}")

    # Use the proxy endpoint for nav API
    proxy_url = f"https://encar-proxy.habsida.net/api/nav?count={count}&q={encoded_q}&inav={encoded_inav}"
    print(f"Nav Proxy URL: {proxy_url}")

    # Setup proxy configuration
    proxy_config = {
        "http": "http://B01vby:GBno0x@45.118.250.2:8000",
        "https": "http://B01vby:GBno0x@45.118.250.2:8000",
    }

    # Headers for proxy request
    headers = {
        "accept": "application/json",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    }

    try:
        # Define a function to make a synchronous request using requests
        def make_request(url):
            try:
                print(f"Making nav request to: {url}")
                response = requests.get(
                    url, headers=headers, proxies=proxy_config, timeout=30.0
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

        # Try the proxy URL
        loop = asyncio.get_event_loop()
        response_data = await loop.run_in_executor(
            None, lambda: make_request(proxy_url)
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
