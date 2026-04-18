# Device Analytics Service

Репозиторий: [github.com/hikara33/device-analytics-service](https://github.com/hikara33/device-analytics-service)

REST API на **FastAPI** для приёма показаний `{x, y, z}` с устройств, сохранения в **PostgreSQL** и анализа по модулю вектора \(m = \sqrt{x^2+y^2+z^2}\): минимум, максимум, число точек, сумма, медиана. Доступна фильтрация по времени и режим «за всё время». Реализованы пользователи и привязка устройств: агрегированная статистика по пользователю и по каждому устройству отдельно.

Асинхронный пересчёт через **Celery** (**Redis** как брокер и backend результатов). Развёртывание: **Docker Compose**.

## Стек

| Компонент | Технология |
|-----------|------------|
| API | FastAPI, Uvicorn |
| БД | PostgreSQL, SQLAlchemy 2 |
| Очередь задач | Celery, Redis |
| Нагрузочное тестирование | Locust |

## Быстрый старт (Docker)

```bash
git clone https://github.com/hikara33/device-analytics-service.git
cd device-analytics-service
docker compose up --build -d
```

- API: `http://localhost:8000`
- OpenAPI: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

Сервисы: `web` (API), `worker` (Celery), `db` (PostgreSQL), `redis`. На хосте PostgreSQL проброшен на порт **5433** (если занят 5432).

## Локальная разработка

1. PostgreSQL и Redis доступны локально; БД `analytics` создана.
2. `cp .env.example .env`, при необходимости поправить `DATABASE_URL` (для контейнерной БД с хоста — порт `5433`).
3. Виртуальное окружение и зависимости:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4. API:

```bash
uvicorn app.main:app --reload
```

5. Worker (отдельный терминал):

```bash
celery -A app.celery_app worker --loglevel=info
```

Запуск из корня репозитория. Если порт `8000` занят контейнером `device_analytics_api`, остановите его: `docker compose stop web`, либо используйте `--port 8001`.

## Переменные окружения

| Переменная | Назначение |
|------------|------------|
| `DATABASE_URL` | Строка SQLAlchemy, обязательна |
| `REDIS_URL` | Redis для Celery (по умолчанию `redis://localhost:6379/0`) |
| `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Если не заданы, берутся из `REDIS_URL` |
| `API_V1_PREFIX` | Префикс маршрутов (по умолчанию `/api/v1`) |

Шаблон: `.env.example`.

## Эндпоинты

| Метод | Путь | Описание |
|--------|------|----------|
| POST | `/api/v1/devices/{device_id}/samples` | Тело: `x`, `y`, `z`, опционально `recorded_at` |
| GET | `/api/v1/devices/{device_id}/stats` | Query: `from`, `to` (ISO datetime), опционально |
| POST | `/api/v1/devices/{device_id}/stats/async` | Задача Celery, ответ `202` и `task_id` |
| POST | `/api/v1/users` | `{ "username": "..." }` |
| POST | `/api/v1/users/{user_id}/devices` | `{ "device_id": "..." }` |
| GET | `/api/v1/users/{user_id}/stats` | Агрегат по всем устройствам пользователя |
| GET | `/api/v1/users/{user_id}/stats/per-device` | По каждому устройству |
| POST | `/api/v1/users/{user_id}/stats/async` | Агрегат асинхронно (Celery) |
| GET | `/api/v1/tasks/{task_id}` | Статус и результат задачи |

Префикс `/api/v1` задаётся настройкой `API_V1_PREFIX`.

## Нагрузочное тестирование

```bash
locust -f locustfile.py --headless -u 25 -r 8 -t 45s --host=http://127.0.0.1:8000
```

Пример сохранённого прогона: `benchmarks/load_test_results.txt` (около 129 req/s при 25 пользователях, 45 с, без ошибок в данном прогоне).

## Структура каталогов

```
app/
  main.py
  core/config.py
  db/
  models/
  schemas/
  services/stats.py
  api/v1/
  tasks/
  celery_app.py
locustfile.py
docker-compose.yml
Dockerfile
```
