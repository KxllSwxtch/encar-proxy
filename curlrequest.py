import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Referer": "https://www.intercarkorea.com/",
}

response = requests.get(
    "https://encar-proxy.habsida.net/api/catalog?count=true&q=(And.Hidden.N._.CarType.A._.SellType.%EC%9D%BC%EB%B0%98.)&sr=%7CModifiedDate%7C0%7C20",
    headers=headers,
)
