# 🌙 mkk_luna

Асинхронный FastAPI сервис для управления организациями, зданиями и видами деятельности с геопоиском и комплексной системой тестирования.

# 🔧 Стек:
- **FastAPI** - современный веб-фреймворк
- **SQLAlchemy 2.0** - асинхронный ORM
- **PostgreSQL + asyncpg** - база данных
- **Alembic** - миграции БД
- **Docker** - контейнеризация
- **Pytest + httpx** - тестирование (80+ тестов)


##  ▶️ Запуск (Docker)
```bash
docker-compose up --build
```

## 📄 Документация:
- Swagger UI: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc

## 🔍 Проверка состояния:
- Health: http://localhost:8000/health

## 🔐 Авторизация
Заголовок для всех запросов:
```
X-API-KEY: SECRET_API_KEY
```

## 🌐 Эндпоинты
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

## ⚙️ Тестовые данные
Миграция `0002_seed` добавляет тестовые данные автоматически при старте контейнера.

## 🧪 Тестирование

Проект включает комплексную систему тестирования с покрытием **80+ тестов**.

### Запуск тестов

```bash
# 1. Запустить контейнеры
docker-compose up -d

# 2. Создать тестовую БД (один раз)
docker-compose exec db psql -U user -d postgres -c "CREATE DATABASE test_mkk_luna_db;"

# 3. Запустить все тесты
docker-compose exec api pytest -v

# С покрытием кода
docker-compose exec api pytest --cov=app --cov-report=html --cov-report=term-missing
```

### Запуск по категориям

```bash
docker-compose exec api pytest -v -m unit         # Unit тесты
docker-compose exec api pytest -v -m crud         # CRUD тесты
docker-compose exec api pytest -v -m api          # API тесты
docker-compose exec api pytest -v -m integration  # Интеграционные тесты
```

### Отладка

```bash
# Конкретный файл
docker-compose exec api pytest tests/test_crud_activity.py -v

# Конкретный тест
docker-compose exec api pytest tests/test_crud_activity.py::TestActivityCRUD::test_create_root_activity -v

# С логами
docker-compose exec api pytest -v --log-cli-level=DEBUG

# Войти в контейнер
docker-compose exec api bash
```

Отчет о покрытии сохраняется в `htmlcov/index.html`


## 🚀 Разработка

### Работа с проектом

```bash
# Запустить все сервисы
docker-compose up -d

# Просмотр логов
docker-compose logs -f api

# Перезапуск после изменений
docker-compose restart api

# Применить миграции
docker-compose exec api alembic upgrade head

# Войти в контейнер для отладки
docker-compose exec api bash
```

### Перед коммитом

```bash
# Запустить тесты с покрытием
docker-compose exec api pytest --cov=app --cov-report=term-missing
```

## 📋 Требования

- Docker
- Docker Compose

Всё остальное (Python, PostgreSQL, зависимости) упаковано в контейнеры.

## 🔒 Безопасность

- API Key аутентификация для всех endpoints (кроме `/health`)
- Валидация всех входных данных через Pydantic
- SQL Injection защита через SQLAlchemy ORM
- Логирование всех попыток доступа

## ✍️ Автор
Павел Сурсков
