from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4


class InMemoryDB:
    def __init__(self):
        self.infopovods: Dict[str, Dict] = {}
        self.angles: Dict[str, Dict] = {}
        self.headlines: Dict[str, Dict] = {}
        self.tests: Dict[str, Dict] = {}
        self.reports: Dict[str, Dict] = {}
    
    def create_infopovod(self, data: Dict) -> str:
        infopovod_id = str(uuid4())
        data["id"] = infopovod_id
        data["created_at"] = datetime.now().isoformat()
        data["updated_at"] = datetime.now().isoformat()
        self.infopovods[infopovod_id] = data
        return infopovod_id
    
    def create_angle(self, data: Dict) -> str:
        angle_id = str(uuid4())
        data["id"] = angle_id
        data["created_at"] = datetime.now().isoformat()
        self.angles[angle_id] = data
        return angle_id
    
    def create_headline(self, data: Dict) -> str:
        headline_id = str(uuid4())
        data["id"] = headline_id
        data["created_at"] = datetime.now().isoformat()
        self.headlines[headline_id] = data
        return headline_id
    
    def create_report(self, geo: str, data: Dict) -> str:
        report_id = str(uuid4())
        data["id"] = report_id
        data["geo"] = geo
        data["generated_at"] = datetime.now().isoformat()
        self.reports[report_id] = data
        return report_id
    
    def get_infopovods_by_geo(self, geo: str, limit: int = 30) -> List[Dict]:
        return [i for i in self.infopovods.values() if i.get("geo") == geo][:limit]
    
    def get_angles_by_infopovod(self, infopovod_id: str) -> List[Dict]:
        return [a for a in self.angles.values() if a.get("infopovod_id") == infopovod_id]
    
    def get_headlines_by_angle(self, angle_id: str) -> List[Dict]:
        return [h for h in self.headlines.values() if h.get("angle_id") == angle_id]
    
    def get_recent_reports(self, geo: str = None, limit: int = 5) -> List[Dict]:
        reports = list(self.reports.values())
        if geo:
            reports = [r for r in reports if r.get("geo") == geo]
        reports.sort(key=lambda x: x.get("generated_at", ""), reverse=True)
        return reports[:limit]

db = InMemoryDB()