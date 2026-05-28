from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from typing import Optional

from services.airtable_client import airtable_client
from services.report_generator import report_generator

router = APIRouter()


@router.get("/latest", response_class=HTMLResponse)
async def get_latest_report(geo: Optional[str] = None):
    reports = await airtable_client.get_reports(geo, limit=1)
    
    if not reports:
        raise HTTPException(status_code=404, detail="No reports found")
    
    latest = reports[0]
    html_content = latest.get("html", "<h1>Отчёт недоступен</h1>")
    
    return HTMLResponse(content=html_content)


@router.get("/{report_id}", response_class=HTMLResponse)
async def get_report(report_id: str):
    reports = await airtable_client.get_reports(limit=100)
    
    for report in reports:
        if report.get("id") == report_id:
            return HTMLResponse(content=report.get("html", "<h1>Отчёт не найден</h1>"))
    
    raise HTTPException(status_code=404, detail="Report not found")


@router.get("/{geo}/latest", response_class=HTMLResponse)
async def get_geo_latest_report(geo: str):
    return await get_latest_report(geo)


@router.get("/{geo}/export/markdown")
async def export_markdown(geo: str):
    reports = await airtable_client.get_reports(geo, limit=1)
    if not reports:
        raise HTTPException(status_code=404, detail="No reports found")
    return {"message": "Markdown export - функция в разработке"}