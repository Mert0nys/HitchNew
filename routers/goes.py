from fastapi import APIRouter, HTTPException
from typing import List, Dict

from config import settings

router = APIRouter()


@router.get("/")
async def get_geos() -> List[Dict]:
    return [
        {
            "code": geo,
            "name": geo,
            "status": "active",
            "last_run": None,
            "next_run": None
        }
        for geo in settings.PRIORITY_GEO
    ]


@router.get("/{geo}/sources")
async def get_geo_sources(geo: str):
    sources = {
        "Germany": ["Spiegel", "Bild", "FAZ", "Twitter DE"],
        "Brazil": ["G1", "UOL", "O Globo", "Twitter BR"],
        "USA": ["NY Times", "WSJ", "Bloomberg", "Twitter US"],
        "India": ["Times of India", "The Hindu", "Economic Times"]
    }
    
    if geo not in sources:
        raise HTTPException(status_code=404, detail="GEO not found")
    
    return {"geo": geo, "sources": sources[geo]}


@router.post("/{geo}/offer")
async def update_offer_context(geo: str, offer_context: Dict):
    return {
        "message": f"Offer context updated for {geo}",
        "context": offer_context.get("text", "")
    }


@router.get("/{geo}/settings")
async def get_geo_settings(geo: str):
    return {
        "geo": geo,
        "monitoring_interval_hours": settings.MONITORING_INTERVAL_HOURS,
        "max_news_per_run": settings.MAX_NEWS_PER_GEO,
        "news_days_back": settings.NEWS_DAYS_BACK,
        "language": {
            "Germany": "de",
            "Brazil": "pt",
            "USA": "en",
            "India": "hi"
        }.get(geo, "en")
    }