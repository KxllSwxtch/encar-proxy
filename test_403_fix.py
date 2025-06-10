#!/usr/bin/env python3
"""
Тест для проверки исправления 403 ошибки с автоматической ротацией сессий
"""

import asyncio
import requests
import logging
from main import EncarProxyClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_403_handling():
    """Тестируем обработку 403 ошибки"""

    client = EncarProxyClient()

    # URL который может вызвать 403
    test_url = "https://encar-proxy.habsida.net/api/catalog?count=true&q=(And.Hidden.N._.CarType.A._.SellType.일반.)&sr=|ModifiedDate|0|10"

    print("🔍 Тестируем исправление 403 ошибки...")
    print(f"📊 Начальное количество ротаций сессий: {client.session_rotation_count}")

    # Делаем несколько запросов
    for i in range(5):
        print(f"\n--- Запрос {i+1} ---")
        result = await client.make_request(test_url)

        print(f"✅ Успех: {result.get('success')}")
        print(f"📊 Статус: {result.get('status_code')}")
        print(f"🔄 Ротаций сессий: {client.session_rotation_count}")
        print(f"📈 Всего запросов: {client.request_count}")

        if result.get("success"):
            print("✅ Запрос выполнен успешно!")
        else:
            print(f"❌ Ошибка: {result.get('error')}")

        # Небольшая пауза между запросами
        await asyncio.sleep(2)

    # Закрываем сессию
    client.session.close()
    print(f"\n🎯 Итого ротаций сессий: {client.session_rotation_count}")
    print("✅ Тест завершен!")


if __name__ == "__main__":
    asyncio.run(test_403_handling())
