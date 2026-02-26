"""Celery worker for processing financial document analysis tasks asynchronously."""
import os
from celery import Celery
from crewai import Crew, Process
from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from task import (
    analyze_financial_document_task,
    investment_analysis,
    risk_assessment,
    verification,
)
from database import save_analysis_result, update_analysis_result

# Redis broker URL (default to localhost)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "financial_analyzer",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # Process one task at a time per worker
)


@celery_app.task(bind=True, name="analyze_document")
def analyze_document_task(self, task_id: str, query: str, file_path: str):
    """
    Celery task to run the financial analysis crew asynchronously.
    
    Args:
        task_id: Unique identifier for this analysis task
        query: The user's analysis query
        file_path: Path to the uploaded PDF file
    """
    try:
        # Update status to processing
        update_analysis_result(task_id, status="processing")

        # Build and run the crew
        financial_crew = Crew(
            agents=[verifier, financial_analyst, investment_advisor, risk_assessor],
            tasks=[verification, analyze_financial_document_task, investment_analysis, risk_assessment],
            process=Process.sequential,
            verbose=True,
        )

        result = financial_crew.kickoff({'query': query, 'file_path': file_path})

        # Save successful result
        update_analysis_result(task_id, status="success", analysis=str(result))
        return {"status": "success", "task_id": task_id, "analysis": str(result)}

    except Exception as exc:
        # Save error
        update_analysis_result(task_id, status="failed", error=str(exc))
        raise self.retry(exc=exc, max_retries=1, countdown=30)

    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
