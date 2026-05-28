from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from models.database import db
from models.schemas import TestResult

logger = logging.getLogger(__name__)


class AirtableClient:
    def __init__(self, use_airtable: bool = False):
        self.use_airtable = use_airtable
    
    async def save_infopovod(self, geo: str, infopovod: Dict, angles: List[Dict], 
                             headlines: List[Dict], risks: Dict) -> Dict:
        infopovod["geo"] = geo
        infopovod_id = db.create_infopovod(infopovod)
        saved_angles = []
        for angle in angles:
            angle["infopovod_id"] = infopovod_id
            angle_id = db.create_angle(angle)
            saved_angles.append({"id": angle_id, **angle})
            for headline in headlines:
                if headline.get("angle_id") == angles.index(angle):
                    headline["angle_id"] = angle_id
                    db.create_headline(headline)

        risks["infopovod_id"] = infopovod_id
        
        return {
            "infopovod_id": infopovod_id,
            "angles_count": len(saved_angles),
            "headlines_count": len(headlines)
        }
    
    async def save_test_result(self, test_result: TestResult) -> str:
        test_id = db.create_test(test_result.model_dump())
        return test_id
    
    async def get_last_run_status(self, geo: str) -> Dict:
        reports = db.get_recent_reports(geo, limit=1)
        if reports:
            last_report = reports[0]
            return {
                "geo": geo,
                "last_run": last_report.get("generated_at"),
                "status": "completed",
                "report_id": last_report.get("id")
            }
        return {"geo": geo, "status": "never_run"}
    
    async def get_global_stats(self) -> Dict:
        total_infopovods = len(db.infopovods)
        total_angles = len(db.angles)
        total_headlines = len(db.headlines)
        successful_tests = sum(1 for t in db.tests.values() if t.get("verdict") == "зашло")
        avg_processing_time = 15
        
        return {
            "total_ideas": total_angles,
            "total_infopovods": total_infopovods,
            "total_headlines": total_headlines,
            "success_tests": successful_tests,
            "avg_processing_time": avg_processing_time
        }
    
    async def get_recent_infopovods(self, geo: str = None, limit: int = 30) -> List[Dict]:
        return db.get_infopovods_by_geo(geo, limit) if geo else list(db.infopovods.values())[:limit]
    
    async def get_infopovod_with_relations(self, infopovod_id: str) -> Dict:
        infopovod = db.infopovods.get(infopovod_id)
        if not infopovod:
            return {}
        
        angles = db.get_angles_by_infopovod(infopovod_id)
        
        for angle in angles:
            angle["headlines"] = db.get_headlines_by_angle(angle["id"])
        
        infopovod["angles"] = angles
        return infopovod
    
    async def save_report(self, geo: str, report_data: Dict) -> str:
        report_id = db.create_report(geo, report_data)
        return report_id
    
    async def get_reports(self, geo: str = None, limit: int = 10) -> List[Dict]:
        return db.get_recent_reports(geo, limit)

airtable_client = AirtableClient(use_airtable=False)