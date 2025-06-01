import requests

headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en,ru;q=0.9,en-CA;q=0.8,la;q=0.7,fr;q=0.6,ko;q=0.5",
    "origin": "https://car.encar.com",
    "priority": "u=1, i",
    "referer": "https://car.encar.com/",
    "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
}

response = requests.get(
    "https://api.encar.com/search/car/list/mobile?count=true&q=(And.Hidden.N._.CarType.A.)&sr=%7CMobileModifiedDate%7C0%7C200&inav=%7CMetadata%7CSort&cursor=",
    headers=headers,
)
