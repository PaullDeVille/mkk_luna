# mkk_luna (FastAPI + SQLAlchemy Async + Alembic + Docker)

## Запуск (Docker)
```bash
docker-compose up --build
```

API:
- Swagger UI: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health

## Авторизация
Заголовок для всех запросов:
```
X-API-KEY: SECRET_API_KEY
```

## Примечание про "асинхронность"
- Все хендлеры FastAPI сделаны `async def`
- Работа с БД через `AsyncSession` и драйвер `asyncpg`
- Alembic выполняет миграции через async engine (`async_engine_from_config`)

## Эндпоинты
- `GET /api/v1/buildings` — список зданий
- `GET /api/v1/buildings/{building_id}/organizations` — организации в здании
- `GET /api/v1/activities` — список деятельностей
- `POST /api/v1/activities` — создать деятельность (max depth 3)
- `GET /api/v1/activities/{activity_id}/organizations` — организации по деятельности (включая дочерние)
- `GET /api/v1/activities/search/by-name/organizations?name=...` — поиск организаций по названию вида деятельности (включая дочерние)
- `GET /api/v1/organizations/{org_id}` — организация по id
- `GET /api/v1/organizations/search/by-name?name=...` — поиск по названию организации
- `POST /api/v1/organizations` — создать организацию
- `GET /api/v1/organizations/geo/rectangular-area?lat=..&lon=..&width_m=..&height_m=..` — поиск в прямоугольной области относительно точки

## Тестовые данные
Миграция `0002_seed` добавляет тестовые данные автоматически при старте контейнера.

## Автор
Павел Сурсков
