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

    # First attempt with fixed parameter format
    url1 = (
        f"https://api.encar.com/search/car/list/mobile?count=true&q={q}&sr={encoded_sr}"
    )
    print(f"First attempt URL: {url1}")

    # Second attempt with a different format
    url2 = f"https://api.encar.com/search/car/list/mobile?count=true&q={q}&sr={encoded_sr}&inav=%7CMetadata%7CSort"
    print(f"Second attempt URL: {url2}")

    # Third attempt with the general API
    url3 = f"https://api.encar.com/search/car/list/general?count=true&q={q}&sr={encoded_sr}"
    print(f"Third attempt URL: {url3}")

    # Updated headers based on working example
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en,ru;q=0.9,en-CA;q=0.8,la;q=0.7,fr;q=0.6,ko;q=0.5",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    }

    # Updated cookies from working example
    cookies = {
        "_fwb": "149obMtFqYvsYFp4lRjqlx4.1742255786649",
        "PCID": "17422557868404555606353",
        "OAX": "2/DEzWfYtq4ACa0C",
        "_gcl_au": "1.1.1560849720.1742255791",
        "afUserId": "0cf63be6-1bf1-4b76-9c29-ce865a7fd4ec-p",
        "_fbp": "fb.1.1742283940583.491664745307218287",
        "PERSISTENT_USERTYPE": "1",
        "RecentViewTruck": "36847390%2C39312108",
        "_ga_J4YYNJRLFF": "GS1.1.1744244462.1.0.1744244462.0.0.0",
        "cto_bundle": "1LE52V9mS052NExsVjlWMm5wOVFVdXUxNVFwMVg1UERnMFVERlJNVGdvbFZXZzFIUnllTEQ5aU5CV3dUUXFvWUZqd3RpaTNUdnpJcXo0YWF4T3ZyU1ZNUW1JR3BESEpEOWFKWVZ6VVF4UDhHYVFBY3NKUW03Y09kNm1hM3lodXZvQnMzUkFhbDBTUUhOVGFNSUlLJTJGREJieVpha3JlV2dPVWpYJTJCZ2xLY3BOanhKTFk0WFQ0JTJCQjh4RWh2RnRPMW14R2UyMkt4a0ZCVFhPYjFlSGZMSHAwTGpkbXNpMiUyRjlQV1VPaDhlT1N0dzdRT3BMT093enQwSlNaS1RSSiUyQld3dHJiYnlUMg",
        "_ga_SX6YBF7MKB": "GS1.1.1744588528.1.1.1744591710.0.0.0",
        "_ga_BQ7RK9J6BZ": "GS1.1.1744588528.1.1.1744591710.60.0.908362741",
        "_ga": "GA1.2.1829220692.1742255787",
        "_ga_WY0RWR65ED": "GS1.2.1746066150.64.0.1746066150.0.0.0",
        "AF_SYNC": "1746524983263",
        "RecentViewAllCar": "39100255%2C38133481%2C39381947%2C39548077%2C39529020%2C39472783%2C39464793%2C39177474%2C38758375%2C39401306%2C39350349%2C39104684%2C39403048%2C38125806%2C39244713%2C39268215%2C39227835%2C39414836%2C39294778%2C39282790%2C39429785%2C39164949%2C39342977%2C39431476%2C38527026%2C39415514%2C39269461%2C39009059%2C39115145%2C38897602",
        "RecentViewCar": "39100255%2C38133481%2C39381947%2C39548077%2C39529020%2C39472783%2C39464793%2C39177474%2C38758375%2C39401306%2C39350349%2C39104684%2C39403048%2C38125806%2C39244713%2C39268215%2C39227835%2C39414836%2C39294778%2C39282790",
        "wcs_bt": "4b4e532670e38c:1744590425",
    }

    try:
        # Define a function to make a synchronous request using requests
        def make_request(url):
            try:
                print(f"Making request to: {url}")
                response = requests.get(
                    url,
                    headers=headers,
                    cookies=cookies,
                    allow_redirects=True,
                    timeout=30.0,
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

        # Try each URL in sequence
        for attempt, url in enumerate([url1, url2, url3], 1):
            # Run the synchronous request in a thread pool
            loop = asyncio.get_event_loop()
            response_data = await loop.run_in_executor(None, lambda: make_request(url))

            if not response_data["success"]:
                print(f"Attempt {attempt} failed: {response_data['error']}")
                attempts.append({"url": url, "error": response_data["error"]})
                continue

            status_code = response_data["status_code"]
            response_text = response_data["text"]
            print(f"Attempt {attempt} status code: {status_code}")

            attempts.append(
                {
                    "url": url,
                    "status_code": status_code,
                    "content_length": len(response_text) if response_text else 0,
                }
            )

            if status_code == 200:
                try:
                    import json

                    if not response_text or response_text.strip() == "":
                        print(f"Empty response from {url}")
                        continue

                    print(
                        f"Response text sample: {response_text[:200] if response_text else 'Empty'}"
                    )

                    # Check if response is HTML instead of JSON
                    if response_text.strip().startswith(
                        "<!DOCTYPE html>"
                    ) or response_text.strip().startswith("<html"):
                        print(f"Received HTML instead of JSON from {url}")
                        continue

                    json_data = json.loads(response_text)
                    return json_data
                except Exception as e:
                    print(f"JSON decode error on attempt {attempt}: {str(e)}")
                    continue

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
