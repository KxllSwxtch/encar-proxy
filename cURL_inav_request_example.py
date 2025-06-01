import requests

headers = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "en,ru;q=0.9,en-CA;q=0.8,la;q=0.7,fr;q=0.6,ko;q=0.5",
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
}

response = requests.get(
    "https://api.encar.com/search/car/list/general?count=true&q=(And.Hidden.N._.CarType.Y.)&inav=%7CMetadata%7CSort",
    headers=headers,
)
