# Medical Telegram Data Warehouse

An end-to-end data engineering pipeline built to scrape medical-related messages, images, and data documents from Telegram channels, ingest them into a PostgreSQL database, and transform them into a clean Star Schema using dbt (Data Build Tool).

This project is part of the Week 8 challenge for the Kifiya 10 Academy.

---

## 📌 Project Architecture

The pipeline processes data through the following layers:
1. **Scraping Layer:** Python script using `Telethon` to fetch text data, images, and documents from targeted Ethiopian medical Telegram channels.
2. **Raw Ingestion:** Extracted message payloads land directly in a raw PostgreSQL database schema.
3. **Transformation Layer (dbt):**
   * `Staging` (`stg_telegram_messages`): Cleanses field types and parses raw payloads.
   * `Dimensions` (`dim_channels`, `dim_dates`): Builds conformable attributes for analysis.
   * `Facts` (`fct_messages`): Centralized operational metrics (views, message counts, signature metrics).

---

## 🛠️ Tech Stack & Prerequisites

* **Language:** Python 3.10+
* **Database:** PostgreSQL
* **Data Transformation:** dbt-core (v1.12.0) & dbt-postgres
* **Scraping Framework:** Telethon

---

## 🚀 Getting Started

### 1. Clone & Environment Setup
```bash
git clone <your-repository-url>
cd Week_8_medical-telegram-warehouse

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt