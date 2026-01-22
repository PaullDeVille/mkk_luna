# Тесты для проекта mkk_luna

Комплексный набор тестов для асинхронного FastAPI приложения.

## Структура тестов

```
tests/
├── __init__.py                     # Инициализация тестового модуля
├── README.md                       # Эта документация
├── test_crud_activity.py           # Тесты CRUD операций для видов деятельности
├── test_crud_building.py           # Тесты CRUD операций для зданий
├── test_crud_organization.py       # Тесты CRUD операций для организаций
├── test_api_activities.py          # Тесты API endpoints видов деятельности
├── test_api_buildings.py           # Тесты API endpoints зданий
├── test_api_organizations.py       # Тесты API endpoints организаций
├── test_security.py                # Тесты безопасности и интеграционные тесты
└── test_models.py                  # Тесты моделей данных
```

## Типы тестов

### Unit тесты (маркер: `@pytest.mark.unit`)
- Тесты отдельных компонентов
- Тесты моделей
- Тесты утилит

### CRUD тесты (маркер: `@pytest.mark.crud`)
- Тесты операций создания, чтения, обновления и удаления
- Тесты бизнес-логики

### API тесты (маркер: `@pytest.mark.api`)
- Тесты HTTP endpoints
- Тесты валидации запросов
- Тесты авторизации

### Интеграционные тесты (маркер: `@pytest.mark.integration`)
- Тесты полных workflow
- Тесты взаимодействия компонентов

## Установка зависимостей

```bash
pip install -r requirements.txt
```

Основные тестовые зависимости:
- `pytest` - фреймворк тестирования
- `pytest-asyncio` - поддержка асинхронных тестов
- `httpx` - HTTP клиент для тестирования FastAPI
- `pytest-cov` - покрытие кода тестами
- `faker` - генерация тестовых данных

## Запуск тестов

### Запуск всех тестов
```bash
pytest
```

### Запуск с подробным выводом
```bash
pytest -v
```

### Запуск конкретного файла
```bash
pytest tests/test_crud_activity.py
```

### Запуск тестов по маркерам
```bash
# Только unit тесты
pytest -m unit

# Только CRUD тесты
pytest -m crud

# Только API тесты
pytest -m api

# Только интеграционные тесты
pytest -m integration
```

### Запуск с покрытием кода
```bash
pytest --cov=app --cov-report=html
```

После выполнения откройте `htmlcov/index.html` для просмотра отчета.

### Запуск с логами
```bash
pytest -v --log-cli-level=INFO
```

## Конфигурация

### pytest.ini
Конфигурация pytest находится в корне проекта:
- Путь к тестам: `tests/`
- Режим asyncio: автоматический
- Маркеры тестов
- Настройки покрытия кода

### conftest.py
Файл содержит fixtures для тестов:
- `db_session` - сессия тестовой базы данных
- `client` - HTTP клиент для тестирования API
- `sample_building` - тестовое здание
- `sample_activity` - тестовый вид деятельности
- `sample_organization` - тестовая организация
- `api_headers` - заголовки с валидным API ключом
- `invalid_api_headers` - заголовки с невалидным API ключом

## Тестовая база данных

Тесты используют отдельную тестовую базу данных PostgreSQL.

### Настройка тестовой БД

1. Создайте тестовую базу данных:
```bash
createdb test_mkk_luna_db
```

2. Обновите URL в `conftest.py` если необходимо:
```python
TEST_DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/test_mkk_luna_db"
```

### Docker

Для запуска тестовой базы данных в Docker:
```bash
docker run -d \
  --name test_postgres \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=pass \
  -e POSTGRES_DB=test_mkk_luna_db \
  -p 5433:5432 \
  postgres:15
```

Не забудьте обновить порт в `TEST_DATABASE_URL` на 5433.

## Примеры тестов

### Асинхронный CRUD тест
```python
@pytest.mark.crud
async def test_create_activity(db_session: AsyncSession):
    activity = await create_activity(db_session, "Еда", None)
    assert activity.id is not None
    assert activity.name == "Еда"
```

### API тест
```python
@pytest.mark.api
async def test_get_activities(client: AsyncClient, api_headers: dict):
    response = await client.get("/api/v1/activities", headers=api_headers)
    assert response.status_code == 200
```

### Интеграционный тест
```python
@pytest.mark.integration
async def test_full_workflow(client: AsyncClient, api_headers: dict):
    # Создание
    create_response = await client.post("/api/v1/organizations", ...)
    # Получение
    get_response = await client.get(f"/api/v1/organizations/{org_id}", ...)
    # Проверка
    assert get_response.status_code == 200
```

## Покрытие кода

Целевое покрытие: > 80%

Текущее покрытие проверяется командой:
```bash
pytest --cov=app --cov-report=term-missing
```

## CI/CD

Тесты автоматически запускаются при:
- Push в репозиторий
- Создании Pull Request

## Troubleshooting

### Ошибка подключения к БД
Убедитесь, что PostgreSQL запущен и доступен:
```bash
psql -U user -d test_mkk_luna_db -c "SELECT 1"
```

### Тесты зависают
Проверьте, что не осталось активных транзакций:
```bash
# Перезапустите PostgreSQL или завершите активные подключения
```

### Ошибки импорта
Убедитесь, что все зависимости установлены:
```bash
pip install -r requirements.txt
```

## Лучшие практики

1. **Изоляция тестов**: Каждый тест должен быть независимым
2. **Fixtures**: Используйте fixtures для переиспользуемых данных
3. **Async/await**: Всегда используйте async для асинхронных операций
4. **Маркеры**: Помечайте тесты соответствующими маркерами
5. **Документация**: Добавляйте docstrings к тестам
6. **Assertions**: Используйте понятные сообщения в assertions

## Добавление новых тестов

1. Создайте файл `test_*.py` в директории `tests/`
2. Добавьте необходимые маркеры
3. Используйте существующие fixtures из `conftest.py`
4. Следуйте стилю именования: `test_<что_тестируем>_<ожидаемый_результат>`
5. Запустите тесты и проверьте покрытие

## Контакты

При возникновении вопросов или проблем создайте issue в репозитории проекта.
