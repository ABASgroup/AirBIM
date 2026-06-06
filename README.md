<img width="1600" height="409" alt="Снимок экрана 2026-06-06 125839" src="https://github.com/user-attachments/assets/13ee3889-e8cc-4c61-adae-8c28e9b96591" />

<h1 align="center">AirBIM</h1>

<div align="center">
  <img src="https://img.shields.io/badge/статус-в%20разработке-blue?style=for-the-badge" alt="Статус">
    <img src="https://img.shields.io/badge/статус-Python | React-green?style=for-the-badge" alt="Стек">
</div>

<p align="center">Веб-приложение для совместной и одиночной работы с <b>облаками точек</b> и <b>BIM</b>, которое позволяет автоматически находить и анализировать отклонения, фиксировать прогресс и получать готовую документацию на месте</p>
<p align="center">AirBIM использует ИИ-алгоритмы для автоматической обработки, аналитики, сопоставления, что позволяет добиваться высокой точности измерений</p>

## ✨ Возможности
*	Управление рабочими пространствами, проектами и этапами, и их файлами
*	Совместная работа в одном пространстве
*	Добавление людей в свое командное пространство и управление ими
*	Автоматическая конвертация файлов для использования
*	Проведение сравнения план-факт на основе проектной модели (BIM) и реального скана (облако точек) с выявлением отклонений
*	Проведение отслеживания прогресса между разными этапами на основе их сканов
*	Отслеживание прогресса текущих процессов (задач) в реальном времени
*	Запись и документация проведенных операций с возможностью скачивания отчетов (`.pdf` и `.xlsx`)
*	Просмотр облаков точек (загруженных, отображающих прогресс работ или отклонения) с возможностью редактирвания
*	Удобная установка с помощью Docker
*	Быстрая обработка мощными алгоритмами

Поддерживается формат `.ifc` для BIM-моделей и `.laz` для данных сканирования (LiDAR-формат)



## 🚀 Начало работы

### Установка
**ВАЖНО**: перед установкой удостоверьтесь, что вам был предоставлен `.github_token` для доступа к пакету обработки данных

**ИСПОЛЬЗОВАНИЕ GPU ВЕРСИИ ПРИЛОЖЕНИЯ ТРЕБУЕТ ЗНАЧИТЕЛЬНЫХ ВЫЧИСЛИТЕЛЬНЫХ РЕСУРСОВ**

1. Клонировать репозиторий
```bash
git@github.com:ABASgroup/AirBIM.git
```

2. Создать/получить `.env` файл по образцу из `example.env`

3. Запустить приложение одной из команд
_PowerShell (Windows)_
```powershell
# запуск
.\airbim.ps1 start
# режим разработки
.\airbim.ps1 start --dev
# режим с использованием GPU
.\airbim.ps1 start --dev --gpu
```

_Bash_
```bash
# запуск
./airbim.sh start
# режим разработки
./airbim.sh start --dev
# режим с использованием GPU
./airbim.sh start --dev --gpu
```

### Использование
Вы можете получить доступ к любой части приложения, ориентируясь на ваши Docker-котейнеры

Стандартные URL при локальном развертывании (порты меняются в зависимости от `.env`):
- Фронтенд (клиент, основное приложение)
```http://localhost:5173```

- Бэкенд
```http://localhost:8000```

- Автоматически генерируемая документация API
```http://localhost:8000/docs```


### Другие команды

## 🔨 Используемые технологии
| Технология | Назначение |
|---|---|
| <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React" align="center"> | UI-библиотека |
| <img src="https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite" align="center"> | Сборщик |
| <img src="https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white" alt="Tailwind CSS" align="center"> | CSS-фреймворк |
| <img src="https://img.shields.io/badge/React_Router-CA4245?style=for-the-badge&logo=reactrouter&logoColor=white" alt="React Router" align="center"> | Маршрутизация |
| <img src="https://img.shields.io/badge/React_Hook_Form-EC5990?style=for-the-badge&logo=reacthookform&logoColor=white" alt="React Hook Form" align="center"> | Управление формами |
| <img src="https://img.shields.io/badge/Three.js-000000?style=for-the-badge&logo=three.js&logoColor=white" alt="Three.js" align="center"> | 3D-рендеринг |
| <img src="https://img.shields.io/badge/web--ifc-F7821B?style=for-the-badge&logo=ifc&logoColor=white" alt="web-ifc" align="center"> | IFC-парсер |
| <img src="https://img.shields.io/badge/Axios-5A29E4?style=for-the-badge&logo=axios&logoColor=white" alt="Axios" align="center"> | HTTP-клиент |
| <img src="https://img.shields.io/badge/Floating_UI-512BD4?style=for-the-badge&logo=float&logoColor=white" alt="Floating UI" align="center"> | Поповеры и тултипы |
| <img src="https://img.shields.io/badge/Font_Awesome-528DD7?style=for-the-badge&logo=fontawesome&logoColor=white" alt="Font Awesome" align="center"> | Иконки |
| <img src="https://img.shields.io/badge/ESLint-4B32C3?style=for-the-badge&logo=eslint&logoColor=white" alt="ESLint" align="center"> | Линтер |
| <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" align="center"> | Язык разработки |
| <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" align="center"> | Web-фреймворк |
| <img src="https://img.shields.io/badge/Uvicorn-3178C6?style=for-the-badge&logo=uvicorn&logoColor=white" alt="Uvicorn" align="center"> | ASGI-сервер |
| <img src="https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white" alt="Pydantic" align="center"> | Валидация данных |
| <img src="https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white" alt="SQLAlchemy" align="center"> | ORM |
| <img src="https://img.shields.io/badge/Alembic-338833?style=for-the-badge&logo=alembic&logoColor=white" alt="Alembic" align="center"> | Миграции БД |
| <img src="https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white" alt="Celery" align="center"> | Очередь задач |
| <img src="https://img.shields.io/badge/Flower-FF6F00?style=for-the-badge&logo=flower&logoColor=white" alt="Flower" align="center"> | Мониторинг Celery |
| <img src="https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white" alt="JWT" align="center"> | Аутентификация |
| <img src="https://img.shields.io/badge/Argon2-5C2D91?style=for-the-badge&logo=hash&logoColor=white" alt="Argon2" align="center"> | Хеширование паролей |
| <img src="https://img.shields.io/badge/ReportLab-FF6B6B?style=for-the-badge&logo=adobeacrobatreader&logoColor=white" alt="ReportLab" align="center"> | Генерация PDF-отчётов |
| <img src="https://img.shields.io/badge/OpenPyXL-217346?style=for-the-badge&logo=microsoftexcel&logoColor=white" alt="OpenPyXL" align="center"> | Генерация Excel-отчётов |
| <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" align="center"> | Контейнеризация |
| <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" align="center"> | База данных |
| <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis" align="center"> | Кэш / брокер сообщений |
| <img src="https://img.shields.io/badge/MinIO-C72E49?style=for-the-badge&logo=minio&logoColor=white" alt="MinIO" align="center"> | S3-совместимое хранилище |
| <img src="https://img.shields.io/badge/Micromamba-00CC96?style=for-the-badge&logo=anaconda&logoColor=white" alt="Micromamba" align="center"> | Управление окружениями |
| <img src="https://img.shields.io/badge/PDAL-4B8BBE?style=for-the-badge&logo=cloud&logoColor=white" alt="PDAL" align="center"> | Обработка облаков точек |
| <img src="https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white" alt="NumPy" align="center"> | Научные вычисления |


## 📦 Docker-инфраструктура

```mermaid
graph TB
    subgraph "Frontend"
        Nginx["Nginx (prod)"]
        Vite["Vite Dev Server"]
    end

    subgraph "Backend"
        API["FastAPI"]
        WorkerDefault["Celery Worker<br/>queue: default"]
        WorkerConv["Celery Worker<br/>queue: converter<br/>+ PotreeConverter"]
        WorkerProc["Celery Worker<br/>queue: processing"]
        Beat["Celery Beat<br/>periodic tasks"]
        Flower["Celery Flower<br/>monitoring"]
    end

    subgraph "Infrastructure"
        DB[("PostgreSQL 15<br/>database")]
        Cache[("Redis<br/>cache")]
        Broker[("Redis<br/>broker")]
        MinIO[("MinIO<br/>S3-совместимое<br/>хранилище")]
    end

    Nginx -->|"/api/"| API
    Vite -->|"/api/" proxy| API

    API --> DB
    API --> MinIO
    API --> Cache

    Beat --> Broker
    WorkerDefault --> Broker
    WorkerConv --> Broker
    WorkerProc --> Broker

    WorkerDefault --> DB
    WorkerConv --> DB
    WorkerProc --> DB

    WorkerConv --> MinIO
    WorkerProc --> MinIO

    Flower --> Broker
```

| Сервис | Образ | Назначение |
|---|---|---|
| `backend` | `python:3.12-slim` + `uvicorn` | FastAPI приложение, REST API |
| `worker` | `python:3.12-slim` + `celery` | Очередь задач `default` |
| `worker-converter` | `python:3.12-slim` + `PotreeConverter` | Очередь `converter` — конвертация LAS/LAZ в Potree |
| `worker-processing` | `micromamba` + `PDAL` | Очередь `processing` — обработка и тяжелые операции |
| `beat` | `python:3.12-slim` + `celery beat` | Периодические задачи |
| `flower` | `python:3.12-slim` + `flower` | Веб-мониторинг Celery |
| `database` | `postgres:15-alpine` | Реляционная БД |
| `cache` | `redis:latest` | Кэширование |
| `broker` | `redis:latest` | Брокер сообщений для Celery |
| `storage` | `quay.io/minio/minio` | S3-совместимое объектное хранилище |

---

## ⚙️ Архитектура

### Слои backend

```
api/routers/       ← HTTP-обработчики (FastAPI routes)
services/          ← Бизнес-логика
repositories/      ← Data Access Layer (SQLAlchemy async)
models/            ← ORM-модели (SQLAlchemy)
schemas/           ← Pydantic-схемы (request/response)
infrastructure/    ← интерфейсы для взаимодействия с подсистемами приложения (Celery, database, storage)
core/              ← конфиги, зависимости, исключения, безопасность и т.д.
tasks/             ← Celery-задачи по очередям и назначениям
migrations/        ← Alembic и миграции БД
utils/             ← функции общего пользования (convert, files, report_generation)
```

## 📝 Документация и ресурсы
Наша проектная находится в отдельном репозитории - [вот здесь](https://github.com/ABASgroup/docs)

Мы периодически актуализируем информацию

### Дополнительные ресурсы
Макет в Figma - [ссылка](https://www.figma.com/site/11jr6IOGESwsjsrA6LKKrL/AirBIM2?node-id=0-1&p=f&t=QF4RBP7pC8rFu4tm-0)

ER-диаграмма - [ссылка](https://dbdiagram.io/d/AirBIM-6990a710bd82f5fce2b8cdfc)



