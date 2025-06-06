import requests
import asyncio
import random
import time
from typing import Dict, List, Optional, Union
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Encar Advanced Proxy", version="3.0")

# CORS — разрешаем все origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Множественные endpoints для обхода блокировки
ENDPOINTS = [
    "https://encar-proxy.habsida.net",
    # Можно добавить прямой доступ к Encar API
    "https://api.encar.com",
    # Альтернативные прокси
    "https://encar-api.proxy-rotator.com",  # Если есть такой сервис
]

# Прокси для обхода IP блокировки
PUBLIC_PROXIES = [
    # Использовать бесплатные прокси или ваши собственные
    # {"http": "http://free-proxy1.com:8080", "https": "http://free-proxy1.com:8080"},
    # {"http": "http://free-proxy2.com:3128", "https": "http://free-proxy2.com:3128"},
    # Пока используем только прямое соединение с ротацией endpoints
    {},
]

# Расширенный набор User-Agent для ротации
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
]

# Базовые заголовки
BASE_HEADERS = {
    "accept": "*/*",
    "accept-language": "en,ru;q=0.9,en-CA;q=0.8,la;q=0.7,fr;q=0.6,ko;q=0.5",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "upgrade-insecure-requests": "1",
}

# Дополнительные заголовки для обхода блокировки
BYPASS_HEADERS = [
    {
        "origin": "https://cars.prokorea.trading",
        "referer": "https://cars.prokorea.trading/",
    },
    {"origin": "https://encar.com", "referer": "https://encar.com/"},
    {"origin": "https://m.encar.com", "referer": "https://m.encar.com/"},
    {},  # Без origin/referer
]


class AdvancedEncarClient:
    """Продвинутый клиент для обхода IP блокировки и защиты"""

    def __init__(self):
        self.session = requests.Session()
        self.request_count = 0
        self.last_request_time = 0
        self.current_endpoint_index = 0
        self.current_proxy_index = 0
        self.failed_endpoints = set()

        # Базовая конфигурация сессии
        self.session.timeout = (15, 45)  # Увеличиваем таймауты
        self.session.max_redirects = 5

        # Общие заголовки сессии
        self.session.headers.update(
            {
                "Connection": "keep-alive",
                "DNT": "1",
                "Sec-GPC": "1",
            }
        )

    def _get_dynamic_headers(self) -> Dict[str, str]:
        """Генерируем динамические заголовки с агрессивной ротацией"""
        headers = BASE_HEADERS.copy()

        # Ротация User-Agent
        user_agent = random.choice(USER_AGENTS)
        headers["user-agent"] = user_agent

        # Динамический sec-ch-ua на основе UA
        if "Chrome/137" in user_agent:
            headers["sec-ch-ua"] = (
                '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"'
            )
        elif "Chrome/136" in user_agent:
            headers["sec-ch-ua"] = (
                '"Google Chrome";v="136", "Chromium";v="136", "Not/A)Brand";v="24"'
            )
        elif "Firefox" in user_agent:
            headers.pop("sec-ch-ua", None)
            headers.pop("sec-ch-ua-mobile", None)
            headers.pop("sec-ch-ua-platform", None)
        elif "Safari" in user_agent and "Chrome" not in user_agent:
            headers.pop("sec-ch-ua", None)
            headers["sec-ch-ua-platform"] = '"macOS"'
        elif "Edge" in user_agent:
            headers["sec-ch-ua"] = (
                '"Microsoft Edge";v="120", "Chromium";v="120", "Not/A)Brand";v="24"'
            )

        # Ротация bypass заголовков
        bypass_headers = random.choice(BYPASS_HEADERS)
        headers.update(bypass_headers)

        # Случайные дополнительные заголовки для маскировки
        if random.choice([True, False]):
            headers["x-requested-with"] = "XMLHttpRequest"

        if random.choice([True, False]):
            headers["accept-encoding"] = "gzip, deflate, br"

        return headers

    def _rotate_endpoint_and_proxy(self):
        """Ротация endpoint и прокси при блокировке"""
        # Помечаем текущий endpoint как проблемный
        if self.current_endpoint_index < len(ENDPOINTS):
            self.failed_endpoints.add(ENDPOINTS[self.current_endpoint_index])

        # Переходим к следующему endpoint
        self.current_endpoint_index = (self.current_endpoint_index + 1) % len(ENDPOINTS)

        # Ротация прокси
        self.current_proxy_index = (self.current_proxy_index + 1) % len(PUBLIC_PROXIES)
        proxy_config = PUBLIC_PROXIES[self.current_proxy_index]

        if proxy_config:
            self.session.proxies = proxy_config
            logger.info(f"Switched to proxy: {proxy_config.get('http', 'direct')}")
        else:
            self.session.proxies = {}
            logger.info("Switched to direct connection")

        logger.info(f"Switched to endpoint: {ENDPOINTS[self.current_endpoint_index]}")

    def _rate_limit(self):
        """Агрессивная защита от rate limiting"""
        current_time = time.time()
        min_delay = random.uniform(0.3, 0.8)  # Случайная задержка

        if current_time - self.last_request_time < min_delay:
            sleep_time = min_delay - (current_time - self.last_request_time)
            time.sleep(sleep_time)

        self.last_request_time = time.time()
        self.request_count += 1

        # Ротация каждые 5-15 запросов
        if self.request_count % random.randint(5, 15) == 0:
            self._rotate_endpoint_and_proxy()

    def _build_url(self, endpoint: str, api_path: str, params: Dict[str, str]) -> str:
        """Строим URL для разных типов endpoints"""
        param_string = "&".join([f"{k}={v}" for k, v in params.items()])

        if "encar-proxy.habsida.net" in endpoint:
            return f"{endpoint}/api/{api_path}?{param_string}"
        elif "api.encar.com" in endpoint:
            # Прямой доступ к Encar API
            return f"{endpoint}/{api_path}?{param_string}"
        else:
            # Другие прокси сервисы
            return f"{endpoint}/api/{api_path}?{param_string}"

    async def make_request(
        self, api_path: str, params: Dict[str, str], max_retries: int = 6
    ) -> Dict:
        """Выполняет запрос с агрессивным обходом блокировки"""

        original_params = params.copy()

        for attempt in range(max_retries):
            try:
                # Rate limiting
                self._rate_limit()

                # Выбираем endpoint
                endpoint = ENDPOINTS[self.current_endpoint_index % len(ENDPOINTS)]

                # Пропускаем заблокированные endpoints
                if endpoint in self.failed_endpoints and len(
                    self.failed_endpoints
                ) < len(ENDPOINTS):
                    self._rotate_endpoint_and_proxy()
                    endpoint = ENDPOINTS[self.current_endpoint_index % len(ENDPOINTS)]

                # Строим URL
                url = self._build_url(endpoint, api_path, params)

                # Получаем свежие заголовки
                headers = self._get_dynamic_headers()

                logger.info(f"Attempt {attempt + 1}/{max_retries}")
                logger.info(f"Endpoint: {endpoint}")
                logger.info(f"URL: {url}")
                logger.info(f"UA: {headers['user-agent'][:60]}...")
                logger.info(f"Proxy: {self.session.proxies}")

                # Выполняем запрос в отдельном потоке
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, lambda: self.session.get(url, headers=headers)
                )

                logger.info(f"Response status: {response.status_code}")

                if response.status_code == 200:
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "text": response.text,
                        "headers": dict(response.headers),
                        "url": url,
                        "endpoint": endpoint,
                        "attempt": attempt + 1,
                    }
                elif response.status_code == 403:
                    logger.warning(f"IP blocked (403) - rotating endpoint and proxy")
                    self._rotate_endpoint_and_proxy()

                    # Если все endpoints заблокированы, очищаем список и пробуем снова
                    if len(self.failed_endpoints) >= len(ENDPOINTS):
                        logger.info(
                            "All endpoints blocked, clearing failed list and trying again"
                        )
                        self.failed_endpoints.clear()

                    # Пробуем разные параметры кодирования
                    if attempt < max_retries - 2:
                        if "encoded" not in str(params):
                            # Пробуем другую кодировку параметров
                            params = {
                                k: v.replace("%7C", "|") if isinstance(v, str) else v
                                for k, v in original_params.items()
                            }
                        else:
                            params = original_params.copy()

                    continue
                elif response.status_code in [429, 503, 502]:
                    logger.warning(
                        f"Server overloaded ({response.status_code}) - waiting"
                    )
                    await asyncio.sleep(2 ** min(attempt, 4))  # Exponential backoff
                    self._rotate_endpoint_and_proxy()
                    continue
                else:
                    logger.warning(
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "text": response.text,
                        "error": f"HTTP {response.status_code}",
                        "url": url,
                        "endpoint": endpoint,
                        "attempt": attempt + 1,
                    }

            except requests.exceptions.Timeout as e:
                logger.error(f"Timeout error: {str(e)}")
                if attempt == max_retries - 1:
                    return {
                        "success": False,
                        "error": f"Timeout: {str(e)}",
                        "url": "unknown",
                    }
                await asyncio.sleep(1)
                self._rotate_endpoint_and_proxy()
                continue

            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error: {str(e)}")
                if attempt == max_retries - 1:
                    return {
                        "success": False,
                        "error": f"Connection error: {str(e)}",
                        "url": "unknown",
                    }
                await asyncio.sleep(2)
                self._rotate_endpoint_and_proxy()
                continue

            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                if attempt == max_retries - 1:
                    return {
                        "success": False,
                        "error": f"Unexpected error: {str(e)}",
                        "url": "unknown",
                    }
                await asyncio.sleep(1)
                continue

        return {
            "success": False,
            "error": "Max retries exceeded, all endpoints blocked",
            "url": "unknown",
        }


# Глобальный клиент
client = AdvancedEncarClient()


async def handle_api_request(endpoint: str, params: Dict[str, str]) -> JSONResponse:
    """Универсальный обработчик API запросов с обходом блокировки"""

    # Кодируем параметры (пробуем разные варианты)
    encoded_params = {}
    for key, value in params.items():
        if isinstance(value, str):
            encoded_params[key] = value.replace("|", "%7C")
        else:
            encoded_params[key] = value

    attempts = []

    # Основной запрос
    response_data = await client.make_request(endpoint, encoded_params)
    attempts.append(
        {
            "url": response_data.get("url", "unknown"),
            "endpoint": response_data.get("endpoint", "unknown"),
            "success": response_data.get("success", False),
            "status_code": response_data.get("status_code"),
            "attempt": response_data.get("attempt", 1),
        }
    )

    # Если не удалось, пробуем с исходными параметрами
    if not response_data.get("success") or response_data.get("status_code") != 200:
        logger.info("Encoded params failed, trying original...")
        response_data = await client.make_request(endpoint, params)
        attempts.append(
            {
                "url": response_data.get("url", "unknown"),
                "endpoint": response_data.get("endpoint", "unknown"),
                "success": response_data.get("success", False),
                "status_code": response_data.get("status_code"),
                "attempt": response_data.get("attempt", 1),
            }
        )

    if not response_data.get("success"):
        return JSONResponse(
            status_code=502,
            content={
                "error": f"All bypass attempts failed: {response_data.get('error')}",
                "attempts": attempts,
                "debug": {
                    "endpoint": endpoint,
                    "params": params,
                    "failed_endpoints": list(client.failed_endpoints),
                },
            },
        )

    status_code = response_data["status_code"]
    response_text = response_data["text"]

    if status_code != 200:
        return JSONResponse(
            status_code=status_code,
            content={
                "error": f"API returned status {status_code}",
                "attempts": attempts,
                "preview": response_text[:500] if response_text else None,
            },
        )

    # Проверяем и парсим JSON
    try:
        if not response_text or response_text.strip() == "":
            return JSONResponse(
                status_code=502,
                content={"error": "Empty response from API", "attempts": attempts},
            )

        # Проверяем на HTML вместо JSON
        if response_text.strip().startswith(("<!DOCTYPE", "<html")):
            return JSONResponse(
                status_code=502,
                content={
                    "error": "Received HTML instead of JSON",
                    "attempts": attempts,
                    "preview": response_text[:500],
                },
            )

        import json

        json_data = json.loads(response_text)

        # Добавляем мета-информацию
        if isinstance(json_data, dict):
            json_data["_meta"] = {
                "proxy_info": {
                    "attempts": len(attempts),
                    "successful_endpoint": response_data["endpoint"],
                    "successful_url": response_data["url"],
                    "response_size": len(response_text),
                    "total_requests": client.request_count,
                }
            }

        return json_data

    except json.JSONDecodeError as e:
        return JSONResponse(
            status_code=502,
            content={
                "error": f"JSON decode error: {str(e)}",
                "attempts": attempts,
                "preview": response_text[:500] if response_text else None,
            },
        )


@app.get("/api/catalog")
async def proxy_catalog(q: str = Query(...), sr: str = Query(...)):
    """Прокси для каталога автомобилей с обходом IP блокировки"""
    return await handle_api_request("catalog", {"count": "true", "q": q, "sr": sr})


@app.get("/api/nav")
async def proxy_nav(
    q: str = Query(...), inav: str = Query(...), count: str = Query(default="true")
):
    """Прокси для навигации с обходом IP блокировки"""
    return await handle_api_request("nav", {"count": count, "q": q, "inav": inav})


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "client": {
            "request_count": client.request_count,
            "current_endpoint": ENDPOINTS[
                client.current_endpoint_index % len(ENDPOINTS)
            ],
            "failed_endpoints": list(client.failed_endpoints),
            "available_endpoints": len(ENDPOINTS),
            "current_proxy": client.current_proxy_index,
        },
    }


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "Encar Advanced Proxy",
        "version": "3.0",
        "endpoints": ["/api/catalog", "/api/nav", "/health"],
        "features": [
            "IP blacklist bypass",
            "Multiple endpoint rotation",
            "User-Agent rotation",
            "Proxy rotation",
            "Aggressive rate limiting protection",
            "Retry logic with exponential backoff",
            "Advanced error handling",
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
