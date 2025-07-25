# Telegram Health Insights Pipeline

A data engineering project to automate the extraction, processing, and analysis of health-related insights from public Telegram channels in Ethiopia. The pipeline leverages Python, PostgreSQL, and dbt for a robust ELT process.

---

## Table of Contents
- [Project Overview](#project-overview)
- [Features](#features)
- [Architecture](#architecture)
- [Folder Structure](#folder-structure)
- [Getting Started](#getting-started)
- [Running the Pipeline](#running-the-pipeline)
- [Data Structure](#data-structure)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License & Contact](#license--contact)

---

## Project Overview

This pipeline follows an ELT (Extract, Load, Transform) approach to generate insights from health-related Telegram discussions in Ethiopia:

- **Extract:** Scrapes messages and media from Telegram using Python.
- **Load:** Stores raw data in a partitioned Data Lake and loads it into PostgreSQL.
- **Transform:** Uses dbt to create a dimensional (star) schema for analytics.

---

## Features

- **Telegram scraping:** Uses Telethon to extract messages and images from public channels.
- **Data Lake:** Raw JSON messages and images stored in partitioned directories.
- **Robust loading:** Python script loads data into PostgreSQL, with idempotency.
- **dbt transformations:** Staging, dimension, and fact models with tests and documentation.
- **Incremental processing:** Efficiently handles new data.
- **Quality checks:** dbt tests, custom constraints, and documentation.

---

## Architecture

```
Telegram Channels
      ↓
Python Scraper
      ↓
Data Lake (raw JSON & images)
      ↓
Python Loader
      ↓
PostgreSQL (raw.raw_telegram_messages)
      ↓
dbt Staging Models
      ↓
dbt Mart Models (Star Schema)
      ↓
Analytics & Dashboards
```

---

## Folder Structure

```
week7/
├── .env
├── docker-compose.yml
├── data/
│   ├── raw/telegram_messages/YYYY-MM-DD/channel_name/message_id.json
│   └── raw/telegram_images/YYYY-MM-DD/channel_name/image_file.jpg
├── scripts/
│   ├── telegram_scraper.py
│   └── load_to_postgres.py
├── my_project/
│   ├── dbt_project.yml
│   ├── packages.yml
│   └── models/
│       ├── staging/stg_telegram_messages.sql
│       └── marts/core/{dim_channels.sql, dim_dates.sql, fct_messages.sql}
└── ...
```

---

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.8+
- Git
- Telegram API credentials (from [my.telegram.org](https://my.telegram.org))

### Installation

**1. Clone the repo:**
```sh
git clone https://github.com/EyasuGet/Telegram-health-insights-pipeline.git
cd Telegram-health-insights-pipeline
```

**2. Python environment:**
```sh
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
```

**3. Environment variables:**
Create a `.env` file in the root with:
```
API_ID=...
API_HASH=...
PHONE_NUMBER=...
SESSION_NAME=...
POSTGRES_DB=medical_db
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
POSTGRES_HOST=localhost
POSTGRES_PORT=5431
```

**4. Docker/Postgres:**
```sh
docker-compose up -d --build
```

**5. dbt Setup:**
- In `my_project/`, run `dbt deps`.
- Configure `profiles.yml` with your Postgres connection.

---

## Running the Pipeline

**Step 1: Scrape Telegram Data**
```sh
python scripts/telegram_scraper.py
```

**Step 2: Load Data to PostgreSQL**
```sh
python scripts/load_to_postgres.py
```

**Step 3: Run dbt Transformations**
```sh
cd my_project
dbt run --full-refresh
```
- Use `dbt run` for incremental updates.

**Step 4: Test & Document**
```sh
dbt test
dbt docs generate
dbt docs serve
```

---

## Data Structure

- **Data Lake:** Partitioned by date/channel for messages and images.
- **Warehouse (Star Schema):**
  - `raw.raw_telegram_messages`: Raw messages.
  - `staging.stg_telegram_messages`: Cleaned view.
  - `marts.dim_channels`: Channel dimension.
  - `marts.dim_dates`: Date dimension.
  - `marts.fct_messages`: Fact table (metrics, FKs).

---

## Troubleshooting

- **JSON serialization errors:** Ensure custom encoder handles datetime/bytes.
- **Syntax issues:** Check for invisible characters and correct Jinja in SQL.
- **Database errors:** Align all credentials in `.env`, `docker-compose.yml`, and `profiles.yml`.
- **Schema/model not found:** Run with `--full-refresh` for first-time incremental builds.
- **Permissions:** Make sure your DB user can create schemas/tables.

---

## Contributing

Contributions welcome! Please open issues or pull requests.

---

## License & Contact

Licensed under the MIT License.

For questions, open an issue or contact the maintainer.

---