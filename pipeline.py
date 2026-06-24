# 6. Task 5: Pipeline Orchestration (Dagster)
# To tie everything together into an automated, observable workflow, implement a Dagster asset/job pipeline that handles sequence control, failure logging, and step-dependency tracking.
# Workflow Definition Structure:
import os
import subprocess
from dagster import op, job, ScheduleDefinition

@op(description="Extracts raw messages and media files via Telethon.")
def scrape_telegram_data_op():
    result = subprocess.run(["python", "src/scraper.py"], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Scraper failure context: {result.stderr}")
    return "Scrape Stage Passed"

@op(description="Populates the raw data zone of PostgreSQL with new files.")
def load_raw_to_postgres_op(upstream_status):
    result = subprocess.run(["python", "src/load_to_postgres.py"], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Loading Hook failure: {result.stderr}")
    return "Load Stage Passed"

@op(description="Triggers the object detection model over download directories.")
def run_yolo_enrichment_op(upstream_status):
    result = subprocess.run(["python", "src/yolo_detect.py"], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"YOLO Processing failure: {result.stderr}")
    return "Enrichment Stage Passed"

@op(description="Executes dbt compile and models migration across schemas.")
def run_dbt_transformations_op(upstream_status):
    os.chdir("medical_warehouse")
    result = subprocess.run(["dbt", "run"], capture_output=True, text=True)
    test_result = subprocess.run(["dbt", "test"], capture_output=True, text=True)
    os.chdir("..")
    
    if result.returncode != 0 or test_result.returncode != 0:
        raise Exception(f"dbt build layer breakdown: {result.stderr} {test_result.stderr}")
    return "Transformations Stage Passed"

@job(description="Automated Production Flow Pipeline for Ethiopian Medical Warehousing")
def medical_warehouse_job():
    scraped = scrape_telegram_data_op()
    loaded = load_raw_to_postgres_op(scraped)
    enriched = run_yolo_enrichment_op(loaded)
    transformed = run_dbt_transformations_op(enriched)

daily_sync_schedule = ScheduleDefinition(
    job=medical_warehouse_job,
    cron_schedule="0 2 * * *"
)