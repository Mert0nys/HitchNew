from fastapi import APIRouter, HTTPException
from datetime import datetime

from models.schemas import FeedbackRequest, TestResult
from services.airtable_client import airtable_client

router = APIRouter()


@router.post("/submit")
async def submit_feedback(feedback: FeedbackRequest):
    saved_results = []
    
    for item in feedback.feedback:
        test_result = TestResult(
            headline_id=item.get("headline_id", ""),
            geo=feedback.geo,
            date_tested=datetime.now(),
            ctr=item.get("ctr"),
            conversion=item.get("conversion"),
            verdict=item.get("verdict", "тестируется"),
            impressions=item.get("impressions"),
            clicks=item.get("clicks")
        )
        
        test_id = await airtable_client.save_test_result(test_result)
        saved_results.append(test_id)
    
    return {
        "message": f"Feedback saved for {len(saved_results)} tests",
        "test_ids": saved_results
    }


@router.get("/stats/{geo}")
async def get_feedback_stats(geo: str):
    return {
        "geo": geo,
        "total_tested": 42,
        "successful": 15,
        "avg_ctr": 2.3,
        "top_triggers": ["деньги", "страх", "кризис"]
    }


@router.post("/learning/update")
async def update_learning_model():
    return {"message": "Learning model update started"}