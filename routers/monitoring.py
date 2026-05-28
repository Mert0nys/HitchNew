from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Dict, Any
import logging

from models.schemas import MonitoringRequest
from services.new_collector import news_collector
from services.ll_processor import llm_processor
from services.airtable_client import airtable_client
from services.report_generator import report_generator
from services.notifier import notifier

router = APIRouter()
logger = logging.getLogger(__name__)


async def run_full_pipeline(geo: str, offer_context: str = None):
    try:
        logger.info(f"Starting pipeline for {geo}")
        news = await news_collector.collect(geo)
        logger.info(f"Collected {len(news)} news for {geo}")
        
        if not news:
            logger.warning(f"No news found for {geo}")
            await notifier.send_error_alert(geo, "No news found")
            return

        all_results = []
        for idx, item in enumerate(news[:15]):  # Лимит 15 инфоповодов
            logger.info(f"Processing {idx+1}/{min(15, len(news))} for {geo}")
            classified = await llm_processor.classify_infopovod(item, geo)
            angles = await llm_processor.generate_angles(classified, geo, offer_context or "финансовые услуги, инвестиции")
            headlines = await llm_processor.generate_headlines(angles, geo)
            risks = await llm_processor.assess_risks(classified, geo)
            saved = await airtable_client.save_infopovod(
                geo=geo,
                infopovod=classified,
                angles=angles,
                headlines=headlines,
                risks=risks
            )
            
            all_results.append({
                "infopovod": classified,
                "angles": angles,
                "headlines": headlines,
                "risks": risks,
                "saved": saved
            })
        
        report_html = await report_generator.generate_full_report(geo, all_results)
        report_id = await airtable_client.save_report(geo, {"html": report_html})
        await notifier.send_complete_report(geo, report_html)
        logger.info(f"Pipeline completed for {geo}: {len(all_results)} infopovods processed")
        
    except Exception as e:
        logger.error(f"Pipeline failed for {geo}: {str(e)}", exc_info=True)
        await notifier.send_error_alert(geo, str(e))


@router.post("/run/{geo}")
async def run_monitoring(geo: str, background_tasks: BackgroundTasks, request: MonitoringRequest = None):
    if geo not in ["Germany", "Brazil", "USA", "India"]:
        raise HTTPException(status_code=400, detail=f"Unsupported GEO: {geo}")
    
    offer_context = request.offer_context if request else None
    background_tasks.add_task(run_full_pipeline, geo, offer_context)
    
    return {
        "message": f"Monitoring started for {geo}",
        "status": "running",
        "geo": geo,
        "estimated_time": "5-10 minutes"
    }


@router.get("/status/{geo}")
async def get_status(geo: str):
    status = await airtable_client.get_last_run_status(geo)
    return status


@router.get("/stats")
async def get_stats():
    stats = await airtable_client.get_global_stats()
    return stats


@router.get("/history/{geo}")
async def get_history(geo: str, limit: int = 10):
    reports = await airtable_client.get_reports(geo, limit)
    return {"geo": geo, "reports": reports}