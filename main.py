import httpx
import random
import urllib.parse
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
    # https://encar-proxy.habsida.net/api/catalog
    # f"https://api.encar.com/search/car/list/mobile?count=true&q={q}&sr={encoded_sr}"

    url1 = (
        f"https://encar-proxy.habsida.net/api/catalog?count=true&q={q}&sr={encoded_sr}"
    )
    print(f"First attempt URL: {url1}")

    # Second attempt with a different format
    url2 = f"https://encar-proxy.habsida.net/api/catalog?count=true&q={q}&sr={encoded_sr}&inav=%7CMetadata%7CSort"
    print(f"Second attempt URL: {url2}")

    # Third attempt with the general API
    url3 = (
        f"https://encar-proxy.habsida.net/api/catalog?count=true&q={q}&sr={encoded_sr}"
    )
    print(f"Third attempt URL: {url3}")

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en,ru;q=0.9,en-CA;q=0.8,la;q=0.7,fr;q=0.6,ko;q=0.5",
        "Origin": "https://korean-cars-catalogue.com",
        "Referer": "https://korean-cars-catalogue.com/",
        "User-Agent": random.choice(
            [
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
                "Mozilla/5.0 (iPad; CPU OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
            ]
        ),
    }

    # cookies = {
    #     "PCID": "17422557868404555606353",
    #     "PERSISTENT_USERTYPE": "1",
    #     "wcs_bt": "4b4e532670e38c:1744590425",
    # }

    try:
        # Simple client without any complex options
        async with httpx.AsyncClient(timeout=20.0) as client:
            # Try all URLs in sequence
            for attempt, url in enumerate([url1, url2, url3], 1):
                try:
                    print(f"Trying attempt {attempt} with URL: {url}")
                    response = await client.get(
                        url, headers=headers, follow_redirects=True
                    )
                    print(f"Attempt {attempt} response status: {response.status_code}")

                    attempts.append(
                        {
                            "url": url,
                            "status_code": response.status_code,
                            "content_length": (
                                len(response.text) if response.text else 0
                            ),
                        }
                    )

                    if response.status_code == 200:
                        try:
                            json_data = response.json()
                            return json_data
                        except Exception as e:
                            print(f"JSON decode error on attempt {attempt}: {str(e)}")
                            continue
                except Exception as e:
                    print(f"Request error on attempt {attempt}: {str(e)}")
                    attempts.append({"url": url, "error": str(e)})
                    continue

            # If we get here, all attempts failed
            return JSONResponse(
                status_code=502,
                content={"error": "All API attempts failed", "attempts": attempts},
            )

    except Exception as e:
        print(f"Client creation error: {str(e)}")
        return JSONResponse(
            status_code=502, content={"error": f"Failed to connect to API: {str(e)}"}
        )
