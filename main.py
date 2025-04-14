import httpx
import random
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

    # First try using the working format from test.py
    url1 = f"https://api.encar.com/search/car/list/mobile?count=true&q={q}&sr={sr}"
    print(f"First attempt URL: {url1}")

    # Second try with client sr parameter
    url2 = f"https://api.encar.com/search/car/list/mobile?count=true&q={q}&sr={sr}"
    print(f"Second attempt URL: {url2}")

    # Third try with the general endpoint
    url3 = f"https://api.encar.com/search/car/list/general?count=true&q={q}&sr={sr}"
    print(f"Third attempt URL: {url3}")

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en,ru;q=0.9",
        "Origin": "https://car.encar.com",
        "Referer": "https://car.encar.com/",
        "Sec-Ch-Ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    }

    cookies = {
        "AWSALBCORS": "uME2vZ7sKPnYN0fdwyK/KEmgcDh2KFM4JdRtWnbr1LWwNqjuXJzHuSAPkaxay//jbpfjpfWo8vrfNEpa60X5/Ft5872yPRYNWQVzS8s5o4x9kKkCkSi/ECamUTIt",
        "cto_bundle": "gyv4dF9mS052NExsVjlWMm5wOVFVdXUxNVFwYkE0ZkVGb3hHSDVVZSUyRm1heUVM...",
        "PCID": "17422557868404555606353",
        "PERSISTENT_USERTYPE": "1",
        "wcs_bt": "4b4e532670e38c:1744590425",
        "RecentViewAllCar": "39100255%2C39282790%2C39429785%2C39164949",
        "RecentViewCar": "39100255%2C39282790%2C39429785%2C39164949",
        "RecentViewTruck": "36847390%2C39312108",
    }

    proxies = {
        "http://": "http://B01vby:GBno0x@45.118.250.2:8000",
        "https://": "http://B01vby:GBno0x@45.118.250.2:8000",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Set proxies after client creation
            client.proxies = proxies

            # Try all URLs in sequence
            for attempt, url in enumerate([url1, url2, url3], 1):
                try:
                    print(f"Trying attempt {attempt} with URL: {url}")
                    response = await client.get(url, headers=headers, cookies=cookies)
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
