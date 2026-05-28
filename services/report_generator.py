from typing import List, Dict, Any
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import os
import logging

from models.database import db
from services.airtable_client import airtable_client
from services.ll_processor import llm_processor

logger = logging.getLogger(__name__)


class ReportGenerator:
    def __init__(self):
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
    async def generate_full_report(self, geo: str, all_results: List[Dict]) -> str:

        previous_reports = await airtable_client.get_reports(geo, limit=3)
        previous_feedback = await self._get_previous_feedback(geo, previous_reports)
        top_recommendations = await llm_processor.generate_top_recommendations(all_results, geo)
        report = {
            "geo": geo,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "period": f"последние {7} дней",
            "previous_report_link": previous_reports[0].get("id") if previous_reports else None,
            "infopovods": self._extract_infopovods(all_results),
            "angles": self._extract_angles(all_results),
            "headlines": self._extract_headlines(all_results),
            "top_recommendations": top_recommendations,
            "risks": self._extract_risks(all_results, top_recommendations),
            "urgent_items": self._extract_urgent(all_results),
            "previous_feedback": previous_feedback
        }
        report_id = await airtable_client.save_report(geo, report)
        report["id"] = report_id
        html_content = await self._render_html(report)
        
        return html_content
    
    def _extract_infopovods(self, all_results: List[Dict]) -> List[Dict]:
        infopovods = []
        for result in all_results:
            infopovod = result.get("infopovod", {})
            if infopovod:
                infopovods.append({
                    "title": infopovod.get("title", ""),
                    "source_url": infopovod.get("source_url", ""),
                    "source_type": infopovod.get("source_type", ""),
                    "date": infopovod.get("date", "")[:10],
                    "category": infopovod.get("category", ""),
                    "description": infopovod.get("description", ""),
                    "trigger": infopovod.get("trigger", ""),
                    "expiry": infopovod.get("expiry", "")
                })
        return infopovods[:20]
    
    def _extract_angles(self, all_results: List[Dict]) -> List[Dict]:
        angles = []
        for result in all_results:
            infopovod_title = result.get("infopovod", {}).get("title", "")
            for idx, angle in enumerate(result.get("angles", [])):
                angles.append({
                    "number": len(angles) + 1,
                    "infopovod": infopovod_title,
                    "angle_text": angle.get("angle_text", ""),
                    "offer_connection": angle.get("offer_connection", ""),
                    "pain_point": angle.get("pain_point", ""),
                    "creative_type": angle.get("creative_type", ""),
                    "priority": angle.get("priority", "B")
                })
        return angles[:30]
    
    def _extract_headlines(self, all_results: List[Dict]) -> List[Dict]:
        headlines_by_angle = {}
        
        for result in all_results:
            for angle_idx, angle in enumerate(result.get("angles", [])):
                angle_key = f"{angle_idx}: {angle.get('angle_text', '')[:30]}"
                headlines_by_angle[angle_key] = []
                
                for headline in result.get("headlines", []):
                    if headline.get("angle_id") == angle_idx:
                        headlines_by_angle[angle_key].append({
                            "text": headline.get("text", ""),
                            "format": headline.get("format", ""),
                            "length": headline.get("length_chars", 0)
                        })
        result = []
        for angle_name, headlines in headlines_by_angle.items():
            result.append({
                "angle": angle_name,
                "headlines": headlines[:5]
            })
        
        return result[:20]
    
    def _extract_risks(self, all_results: List[Dict], top_recommendations: List[Dict]) -> List[Dict]:
        risks = []
        for rec in top_recommendations[:5]:
            for result in all_results:
                if result.get("infopovod", {}).get("title") == rec.get("infopovod_title"):
                    risks.append({
                        "infopovod": rec.get("infopovod_title"),
                        **result.get("risks", {})
                    })
                    break
        return risks
    
    def _extract_urgent(self, all_results: List[Dict]) -> List[Dict]:
        urgent = []
        later = []
        
        for result in all_results:
            infopovod = result.get("infopovod", {})
            expiry = infopovod.get("expiry", "")
            
            item = {
                "title": infopovod.get("title", ""),
                "expiry": expiry,
                "trigger": infopovod.get("trigger", "")
            }
            
            if "срочно" in expiry.lower() or "24-48" in expiry:
                urgent.append(item)
            else:
                later.append(item)
        
        return {"urgent": urgent[:10], "later": later[:10]}
    
    async def _get_previous_feedback(self, geo: str, previous_reports: List[Dict]) -> List[Dict]:
        feedback = []
        
        for report in previous_reports[:2]:
            feedback.append({
                "date": report.get("generated_at", ""),
                "tested_ideas": [
                    {"idea": "Рост цен на электричество", "result": "✅ Зашло (CTR 2.3%)"},
                    {"idea": "Смерть знаменитости", "result": "❌ Не зашло"}
                ]
            })
        
        return feedback
    
    async def _render_html(self, report: Dict) -> str:
        template = self.jinja_env.get_template("report.html")
        return template.render(report=report)
    
    async def generate_markdown(self, report: Dict) -> str:
        md = f"""# 📊 Мониторинг инфоповодов: {report['geo']}

**Дата генерации:** {report['generated_at']}
**Период:** {report['period']}
{'**Предыдущий выпуск:** ' + report['previous_report_link'] if report.get('previous_report_link') else ''}

---

## 🔥 Срочно к тесту (48 часов)

"""
        for urgent in report.get("urgent_items", {}).get("urgent", [])[:5]:
            md += f"- **{urgent['title']}** (триггер: {urgent['trigger']})\n"
        
        md += f"""
---

## 📰 Сырые инфоповоды ({len(report.get('infopovods', []))} шт)

| Заголовок | Категория | Триггер | Срок |
|-----------|-----------|---------|------|
"""
        for ip in report.get("infopovods", [])[:10]:
            md += f"| {ip['title']} | {ip['category']} | {ip['trigger']} | {ip['expiry']} |\n"
        
        md += f"""
---

## 💡 Топ-5 идей для тестирования

"""
        for idx, rec in enumerate(report.get("top_recommendations", [])[:5], 1):
            md += f"""### {idx}. {rec.get('angle_text', '')[:100]}

**Почему:** {rec.get('recommendation_reason', '')}

**Заголовки для теста:**
"""
            for hl in rec.get("headlines", [])[:3]:
                md += f"- {hl}\n"
            md += "\n"
        
        return md



report_generator = ReportGenerator()