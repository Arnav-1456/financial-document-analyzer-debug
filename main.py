from fastapi import FastAPI, File, UploadFile, Form, HTTPException
import os
import uuid
import asyncio

from crewai import Crew, Process
from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from task import (
    analyze_financial_document_task,
    investment_analysis,
    risk_assessment,
    verification,
)
from database import (
    save_analysis_result,
    update_analysis_result,
    get_analysis_result,
    log_user_query,
)

app = FastAPI(title="Financial Document Analyzer")


def run_crew(query: str, file_path: str = "data/sample.pdf"):
    """Run the full financial analysis crew on the given document."""
    financial_crew = Crew(
        agents=[verifier, financial_analyst, investment_advisor, risk_assessor],
        tasks=[verification, analyze_financial_document_task, investment_analysis, risk_assessment],
        process=Process.sequential,
        verbose=True,
    )
    
    result = financial_crew.kickoff({'query': query, 'file_path': file_path})
    return result


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Financial Document Analyzer API is running"}


@app.post("/analyze")
async def analyze_document_endpoint(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights")
):
    """Analyze financial document synchronously and return results."""
    
    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"
    
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Save uploaded file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Validate query
        if query == "" or query is None:
            query = "Analyze this financial document for investment insights"

        # Log the user query
        log_user_query(query=query.strip(), filename=file.filename)

        # Save initial record
        save_analysis_result(task_id=file_id, filename=file.filename, query=query.strip())

        # Process the financial document with all analysts
        response = run_crew(query=query.strip(), file_path=file_path)

        # Update the database with success result
        update_analysis_result(task_id=file_id, status="success", analysis=str(response))
        
        return {
            "status": "success",
            "task_id": file_id,
            "query": query,
            "analysis": str(response),
            "file_processed": file.filename
        }
        
    except Exception as e:
        update_analysis_result(task_id=file_id, status="failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error processing financial document: {str(e)}")
    
    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass  # Ignore cleanup errors


@app.post("/analyze/async")
async def analyze_document_async_endpoint(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights")
):
    """Submit a financial document for asynchronous analysis via Celery queue.
    Returns a task_id that can be used to poll for results."""
    
    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"
    
    try:
        os.makedirs("data", exist_ok=True)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        if query == "" or query is None:
            query = "Analyze this financial document for investment insights"

        log_user_query(query=query.strip(), filename=file.filename)
        save_analysis_result(task_id=file_id, filename=file.filename, query=query.strip())

        # Submit to Celery queue
        from worker import analyze_document_task
        analyze_document_task.delay(task_id=file_id, query=query.strip(), file_path=file_path)

        return {
            "status": "queued",
            "task_id": file_id,
            "message": "Document submitted for analysis. Use GET /result/{task_id} to check status."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting document: {str(e)}")


@app.get("/result/{task_id}")
async def get_result(task_id: str):
    """Retrieve analysis results by task_id (works for both sync and async analysis)."""
    result = get_analysis_result(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": result.task_id,
        "status": result.status,
        "filename": result.filename,
        "query": result.query,
        "analysis": result.analysis,
        "error": result.error,
        "created_at": str(result.created_at),
        "completed_at": str(result.completed_at) if result.completed_at else None,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)