import httpx
import random
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
    attempts = []

    urls = [
        f"https://api.encar.com/search/car/list/mobile?count=true&q={q}&sr={sr}",
        f"https://api.encar.com/search/car/list/mobile?count=true&q={q}&sr={sr}",
        f"https://api.encar.com/search/car/list/general?count=true&q={q}&sr={sr}",
    ]

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
        async with httpx.AsyncClient(
            proxies=proxies, headers=headers, cookies=cookies, timeout=30.0
        ) as client:
            for i, url in enumerate(urls, 1):
                try:
                    print(f"[Attempt {i}] GET {url}")
                    response = await client.get(url)
                    print(f"[Attempt {i}] Status: {response.status_code}")

                    if response.status_code == 200:
                        return response.json()
                    else:
                        attempts.append(
                            {
                                "url": url,
                                "status": response.status_code,
                                "text": response.text[:300],  # обрезаем для логов
                            }
                        )

                except Exception as e:
                    traceback.print_exc()
                    attempts.append({"url": url, "error": str(e)})

        return JSONResponse(
            status_code=502,
            content={"error": "All API attempts failed", "attempts": attempts},
        )

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500, content={"error": f"Fatal proxy error: {str(e)}"}
        )
