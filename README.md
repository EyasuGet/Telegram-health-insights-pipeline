# Telegram Health Insights Pipeline

A data engineering project to automate the extraction, processing, and analysis of health-related insights from public Ethiopian Telegram channels.

The pipeline leverages **Python** for scraping, **PostgreSQL** as a data warehouse, **dbt** for robust data transformation, **YOLOv8** for image enrichment, **FastAPI** for analytical APIs, and **Dagster** for orchestration.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Architecture](#architecture)
- [Folder Structure](#folder-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables (.env)](#environment-variables-env)
  - [Docker Setup (PostgreSQL)](#docker-setup-postgresql)
  - [dbt Setup](#dbt-setup)
  - [Running the Pipeline](#running-the-pipeline)
- [Data Structure](#data-structure)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License & Contact](#license--contact)

---

## Project Overview

This pipeline follows an **ELT (Extract, Load, Transform)** approach to generate insights from health-related Telegram discussions in Ethiopia. It's designed to answer key business questions by:

- **Extracting:** Scraping messages and media from specified public Telegram channels.
- **Loading:** Storing raw data in a partitioned Data Lake and subsequently loading it into a PostgreSQL database.
- **Transforming:** Using dbt to clean, restructure, and model the data into a dimensional (star) schema optimized for analytics.
- **Enriching:** Applying YOLOv8 for object detection on images to add visual content insights.
- **Exposing:** Providing an analytical API (FastAPI) for querying insights.
- **Orchestrating:** Managing the entire workflow with Dagster for reliability and observability.

---

## Features

- **Telegram Scraping:** Utilizes Telethon to extract messages (text, metadata) and images from public channels.
- **Data Lake:** Raw JSON messages and images are stored in a partitioned directory structure (`data/raw/`).
- **Robust Loading:** Python scripts handle loading raw data into PostgreSQL, ensuring idempotency and sanitizing problematic characters (`\u0000`).
- **dbt Transformations:** Implements a layered data model (`raw`, `staging`, `marts`) using dbt, including:
  - Staging models for cleaning and light restructuring.
  - Dimensional models (`dim_channels`, `dim_dates`) and fact tables (`fct_messages`, `fct_image_detections`) forming a star schema.
  - Built-in and custom dbt tests for data quality and integrity.
  - Comprehensive dbt documentation generation.
- **Data Enrichment (YOLOv8):** Applies a pre-trained YOLOv8 model to detect objects in scraped images, linking these visual insights to the message data.
- **Analytical API (FastAPI):** Exposes key business insights through RESTful endpoints, querying the dbt-transformed data marts.
- **Pipeline Orchestration (Dagster):** Automates the entire ELT workflow, providing a robust, observable, and schedulable pipeline.

---

## Architecture

```mermaid
graph TD
    subgraph Data Source
        A[Telegram Channels]
    end

    subgraph Data Ingestion (Extract & Load)
        B(Python Scraper<br><i>(telegram_scraper.py)</i>)
        C[(Data Lake: Raw JSON & Images)]
        D(Python Loader<br><i>(load_to_postgres.py)</i>)
        F(Python YOLO Detector<br><i>(yolo_detector.py)</i>)
        G[(Processed Data: yolo_detections.jsonl)]
        H(Python Loader<br><i>(load_yolo_to_pg.py)</i>)
    end

    subgraph Data Warehouse (PostgreSQL)
        E[(raw.raw_telegram_messages)]
        I[(raw.raw_yolo_detections)]
        J[dbt Staging Models<br><i>(staging.stg_telegram_messages)</i>]
        K[dbt Staging Models<br><i>(staging.stg_yolo_detections)</i>]
        L[dbt Mart Models<br><i>(dim_channels, dim_dates)</i>]
        M[dbt Mart Models<br><i>(fct_messages)</i>]
        N[dbt Mart Models<br><i>(fct_image_detections)</i>]
    end

    subgraph Consumption & Orchestration
        O[Analytical API<br><i>(FastAPI)</i>]
        P[Analytics & Dashboards]
        Q[Dagster Orchestrator<br><i>(Job & Schedule)</i>]
    end

    A -- "Scrapes Data" --> B
    B -- "Stores Raw Data" --> C
    C -- "Loads Raw Messages" --> D
    D -- "Loads to DB" --> E
    C -- "Processes Images" --> F
    F -- "Stores Detections" --> G
    G -- "Loads Detections" --> H
    H -- "Loads to DB" --> I

    E -- "Transforms" --> J
    I -- "Transforms" --> K
    J -- "Builds Dims & Facts" --> L
    J -- "Builds Message Facts" --> M
    K -- "Builds Image Detection Facts" --> N

    L -- "Provides Context" --> M
    L -- "Provides Context" --> N
    M -- "Enriches Image Facts" --> N

    O -- "Queries Marts" --> L
    O -- "Queries Marts" --> M
    O -- "Queries Marts" --> N
    L --> P
    M --> P
    N --> P

    Q -- "Triggers Pipeline Runs" --> B
    Q -- "Triggers Pipeline Runs" --> D
    Q -- "Triggers Pipeline Runs" --> F
    Q -- "Triggers Pipeline Runs" --> H
    Q -- "Triggers Pipeline Runs" --> J
    Q -- "Triggers Pipeline Runs" --> K
    Q -- "Triggers Pipeline Runs" --> L
    Q -- "Triggers Pipeline Runs" --> M
    Q -- "Triggers Pipeline Runs" --> N
```

---

## Folder Structure

```
week7/
├── .env                  # Environment variables (API keys, DB credentials)
├── .gitignore            # Files/folders to ignore in Git
├── docker-compose.yml    # Docker setup for PostgreSQL and application container
├── README.md             # Project documentation
├── data/                 # Data lake (raw & processed) and logs
│   ├── raw/
│   │   ├── telegram_messages/YYYY-MM-DD/channel_name/message_id.json
│   │   └── telegram_images/YYYY-MM-DD/channel_name/image_file.jpg
│   └── processed/        # Processed data (e.g., YOLO detections)
│       ├── yolo_detections.jsonl
│       └── processed_images.log
├── scripts/               # Python scripts for loading, and YOLO
│   ├── telegram_scraper.py
│   ├── load_to_postgres.py
│   ├── yolo_detector.py
│   └── load_yolo_to_pg.py
├── src/              # Python scripts for scraping
│   ├── telegram_scraper.py
├── api/                  # FastAPI application for analytical endpoints
│   ├── main.py
│   ├── database.py
│   ├── schemas.py
│   └── crud.py
├── orchestration/        # Dagster orchestration code
│   ├── __init__.py
│   ├── ops.py
│   └── definitions.py
└── my_project/           # dbt project directory
    ├── dbt_project.yml
    ├── packages.yml
    ├── models/
    │   ├── staging/
    │   │   ├── stg_telegram_messages.sql
    │   │   └── stg_yolo_detections.sql
    │   └── marts/core/
    │       ├── dim_channels.sql
    │       ├── dim_dates.sql
    │       ├── fct_messages.sql
    │       └── fct_image_detections.sql
    │   └── schema.yml
    ├── tests/
    │   └── positive_value.sql
    └── ... (target/, dbt_packages/, logs/)
```

---

## Getting Started

### Prerequisites

- **Docker & Docker Compose:** For running PostgreSQL.
- **Python 3.8+:** For scripting and dbt.
- **Git:** For cloning the repository.
- **Telegram API credentials:** `api_id` and `api_hash` obtained from [my.telegram.org](https://my.telegram.org).

### Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/EyasuGet/Telegram-health-insights-pipeline.git
    cd Telegram-health-insights-pipeline
    ```

2. **Set up Python environment:**

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

    Sample `requirements.txt`:

    ```
    telethon
    python-dotenv
    psycopg2-binary
    dbt-postgres
    ultralytics # For YOLO
    fastapi # For API
    uvicorn[standard] # For API
    dagster # For orchestration
    dagster-webserver # For Dagster UI
    ```

3. **Configure Environment Variables:**

    Create a `.env` file in the project root (`week7/`) and populate it with your credentials:

    ```
    # Telegram API Credentials (from my.telegram.org)
    API_ID=YOUR_TELEGRAM_API_ID
    API_HASH=YOUR_TELEGRAM_API_HASH
    PHONE_NUMBER=+251XXXXXXXXX # Your phone number with country code, e.g., +251911223344
    SESSION_NAME=telegram_scraper # Name for Telethon session file

    # PostgreSQL Database Credentials (for Docker Compose and dbt)
    POSTGRES_DB=medical_db
    POSTGRES_USER=""
    POSTGRES_PASSWORD=""

    # PostgreSQL Host & Port (for Python scripts & dbt on host)
    POSTGRES_HOST=localhost
    POSTGRES_PORT=5431
    ```

4. **Docker Setup (PostgreSQL):**

    Your `docker-compose.yml` sets up a PostgreSQL database. Bring up the Docker containers:

    ```bash
    docker-compose up -d --build
    ```

    Wait a moment for the db container to start and initialize the database.

5. **dbt Setup:**

    - Navigate to your dbt project directory:

        ```bash
        cd my_project
        ```

    - Run `dbt deps` to install dbt packages (like dbt_utils).
    - Configure `profiles.yml` (usually `~/.dbt/profiles.yml`) with your PostgreSQL connection details, ensuring it uses environment variables.
    - Ensure `dbt_project.yml` is updated with `on-run-start` hooks for schema creation (`raw`, `staging`, `marts`) and the vars for `surrogate_key_treat_nulls_as_empty_strings: True`.
    - Update `my_project/models/schema.yml` with definitions for all sources and models, including the new YOLO-related ones.

---

### Running the Pipeline

Ensure your Docker containers are running (`docker-compose up -d`) and your Python virtual environment is activated (`source .venv/bin/activate`).

1. **Scrape Telegram Data:**

    ```bash
    python scripts/telegram_scraper.py
    ```
    Follow prompts for Telegram authentication on first run.

2. **Load Raw Messages to PostgreSQL:**

    ```bash
    python scripts/load_to_postgres.py
    ```

3. **Run YOLO Object Detection on Images:**

    ```bash
    python scripts/yolo_detector.py
    ```
    This will download YOLOv8 model weights on first run (requires internet).

4. **Load YOLO Detections to PostgreSQL:**

    ```bash
    python scripts/load_yolo_to_pg.py
    ```

5. **Run dbt Transformations:**

    Navigate to your dbt project directory:

    ```bash
    cd my_project
    dbt run --full-refresh
    ```

    Use `--full-refresh` for the very first run of the entire pipeline or after significant schema changes. For subsequent incremental updates, use `dbt run`.

6. **Run dbt Tests & Generate Docs:**

    From your dbt project directory (`my_project/`):

    ```bash
    dbt test              # Run data quality tests
    dbt docs generate     # Generate static HTML documentation
    dbt docs serve        # Serve the documentation locally (usually on http://localhost:8080)
    ```

7. **Run Analytical API:**

    From your project root (`week7/`):

    ```bash
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
    ```

    Access API docs at [http://localhost:8000/docs](http://localhost:8000/docs).

8. **Launch Dagster UI (for Orchestration):**

    From your project root (`week7/`):

    ```bash
    dagster dev -m orchestration.definitions
    ```

    Access Dagster UI at [http://localhost:3000](http://localhost:3000). Here, you can manually launch runs and enable the daily schedule.

---

## Data Structure

- **Data Lake:** Raw data is stored in `data/raw/` (messages and images) and `data/processed/` (YOLO detections), partitioned by date and channel.

- **Data Warehouse (PostgreSQL - Star Schema):**
  - `raw.raw_telegram_messages`: Raw messages.
  - `raw.raw_yolo_detections`: Raw YOLO detection results.
  - `staging.stg_telegram_messages`: Cleaned message view.
  - `staging.stg_yolo_detections`: Cleaned YOLO detections view.
  - `marts.dim_channels`: Channel dimension (PK: channel_id).
  - `marts.dim_dates`: Date dimension (PK: date_key).
  - `marts.fct_messages`: Message fact table (PK: message_pk), linking to dim_channels and dim_dates.
  - `marts.fct_image_detections`: Image detection fact table (PK: image_detection_pk), linking to fct_messages.

---

## Troubleshooting

- **JSON serialization errors (TypeError, UntranslatableCharacter):**
  - Ensure `CustomEncoder` in `scripts/telegram_scraper.py` and `scripts/load_to_postgres.py` handles `datetime`, `bytes`, and `\u0000` characters.

- **dbt Compilation Errors (invalid syntax for function call expression):**
  - Often caused by invisible characters (BOM, tabs) or incorrect spacing in Jinja blocks (`{{ config()`). Use `hexdump -C <file.sql>` to inspect.

- **dbt UndefinedTable or relation does not exist:**
  - Ensure `dbt run` completed successfully.
  - For incremental models' first run, use `dbt run --full-refresh --select <model_name>`.
  - Verify `on-run-start` hooks create all necessary schemas (`raw`, `staging`, `marts`).
  - Check `profiles.yml` `dbname` matches your actual PostgreSQL database.
  - For cross-database references on PostgreSQL, remove `database:` from sources in `dbt_project.yml`.

- **API AttributeError or TypeError:**
  - Ensure `import psycopg2.extras` in `api/crud.py`.
  - Verify `APIResponse` in `api/schemas.py` inherits from `typing.Generic`.

- **YOLO model download issues:**  
  - Ensure internet access for `yolo_detector.py`'s first run.

- **YOLO 0 new detections unexpectedly:**  
  - Delete `data/processed/processed_images.log` to force re-processing.

- **Dagster ImportError (no known parent package):**
  - Run Dagster from project root using `dagster dev -m orchestration.definitions`.

- **Dagster DagsterInvalidDefinitionError:**  
  - Check Dagster op definitions in `orchestration/ops.py` (ensure inputs are defined) and job chaining in `orchestration/definitions.py` (pass op results as arguments).

- **Dagster ZoneInfoNotFoundError:**  
  - Correct timezone string in `orchestration/definitions.py` (e.g., `Africa/Addis_Ababa`).

- **subprocess.CalledProcessError in Dagster:**  
  - Check logs for underlying script errors (e.g., python: can't open file). Verify script paths and cwd in `orchestration/ops.py`.

- **General:**  
  - Always review detailed logs (`data/*.log`, `my_project/logs/dbt.log`, Uvicorn/Dagster console output) for specific error messages.

---

## Contributing

Contributions are welcome! Please open issues or submit pull requests for improvements, bug fixes, or new features.

---

## Contact

For questions or suggestions, please open an issue on GitHub
