"""
Скрипт для проверки сохранения данных после batch загрузки.
"""

import asyncio

import httpx


BASE_URL = "http://localhost:8000/api/v1"


async def check_data():
    """Проверить сохранение данных."""
    
    async with httpx.AsyncClient() as client:
        print("="*80)
        print("ПРОВЕРКА СОХРАНЕНИЯ ДАННЫХ")
        print("="*80)
        
        # Проверяем вакансии
        print("\n📋 Проверка вакансий...")
        try:
            response = await client.get(f"{BASE_URL}/vacancies/stats")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Всего вакансий в системе: {data['total']}")
                
                if data['total'] > 0:
                    print("\nПримеры вакансий:")
                    for item in data['sample']:
                        print(f"  - {item['title']} (ID: {item['id']})")
                else:
                    print("⚠️ Нет вакансий в системе!")
            else:
                print(f"❌ Ошибка: {response.status_code}")
        except Exception as e:
            print(f"❌ Ошибка при проверке вакансий: {e}")
        
        # Проверяем кандидатов
        print("\n👤 Проверка кандидатов...")
        try:
            response = await client.get(f"{BASE_URL}/candidates/stats")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Всего кандидатов в системе: {data['total']}")
                
                if data['total'] > 0:
                    print("\nПримеры кандидатов:")
                    for item in data['sample']:
                        print(f"  - {item['name']} ({item['email']}, ID: {item['id']})")
                else:
                    print("⚠️ Нет кандидатов в системе!")
            else:
                print(f"❌ Ошибка: {response.status_code}")
        except Exception as e:
            print(f"❌ Ошибка при проверке кандидатов: {e}")
        
        print("\n" + "="*80)
        print("СОВЕТ:")
        print("="*80)
        print("""
Если вы только что загрузили данные через batch upload, но здесь видите 0:
1. Проверьте логи сервера - там должны быть сообщения о создании
2. Убедитесь, что сервер НЕ был перезапущен после загрузки
3. Попробуйте загрузить данные снова

Данные хранятся в памяти и при перезапуске сервера теряются!
Для постоянного хранения нужно добавить базу данных (PostgreSQL/SQLite).
        """)


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║              ПРОВЕРКА СОХРАНЕНИЯ ДАННЫХ                                ║
║                                                                        ║
║  Этот скрипт проверяет, сохранились ли вакансии и кандидаты          ║
║  после batch загрузки.                                                ║
║                                                                        ║
║  Убедитесь, что сервер запущен: python main.py                       ║
╚════════════════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(check_data())

