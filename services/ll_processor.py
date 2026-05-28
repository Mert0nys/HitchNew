import json
from typing import List, Dict, Any
import httpx
import logging
import re

from config import settings

logger = logging.getLogger(__name__)


class LLMProcessor:
    def __init__(self):
        self.use_local = getattr(settings, 'USE_LOCAL_LLM', True)
        self.local_url = getattr(settings, 'LOCAL_LLM_URL', 'http://localhost:11434')
        self.local_model = getattr(settings, 'LOCAL_LLM_MODEL', 'mistral')
        self.openai_key = settings.OPENAI_API_KEY
        
        logger.info(f"LLM Processor initialized - Local mode: {self.use_local}, Model: {self.local_model}")
    
    async def _call_openai(self, prompt: str, temperature: float = 0.3) -> str:
        if not self.openai_key:
            raise Exception("OpenAI API key not configured")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.OPENAI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.LLM_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "response_format": {"type": "json_object"}
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenAI error: {response.text}")
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def _call_local_llm(self, prompt: str, temperature: float = 0.3) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.local_url}/api/generate",
                    json={
                        "model": self.local_model,
                        "prompt": f"Ты маркетинговый аналитик. Ответь только JSON без пояснений.\n\n{prompt}",
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": 500
                        }
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"Local LLM error: {response.status_code}")
                
                data = response.json()
                result = data.get("response", "").strip()
                
                if result.startswith("```json"):
                    result = result[7:]
                if result.startswith("```"):
                    result = result[3:]
                if result.endswith("```"):
                    result = result[:-3]
                
                result = result.strip()
                if not (result.startswith('{') or result.startswith('[')):
                    # Пытаемся извлечь JSON из текста
                    json_match = re.search(r'(\{.*\}|\[.*\])', result, re.DOTALL)
                    if json_match:
                        result = json_match.group()
                    else:
                        logger.warning(f"Response is not JSON, using fallback")
                        return self._get_fallback_response(prompt)
                
                return result
                
            except Exception as e:
                logger.error(f"Local LLM error: {e}")
                raise
    
    async def _call_llm(self, prompt: str, temperature: float = 0.3) -> str:
        if getattr(settings, 'USE_MOCK_LLM', False):
            return self._get_fallback_response(prompt)
        
        if not self.use_local and self.openai_key:
            try:
                return await self._call_openai(prompt, temperature)
            except Exception as e:
                logger.warning(f"OpenAI failed: {e}, falling back to local")
        
        try:
            return await self._call_local_llm(prompt, temperature)
        except Exception as e:
            logger.warning(f"Local LLM failed: {e}, using fallback")
            return self._get_fallback_response(prompt)
    
    def _get_fallback_response(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        
        if "классифицируй" in prompt_lower or "classify" in prompt_lower:
            return json.dumps({
                "title": "Тестовая новость",
                "category": "экономика",
                "trigger": "деньги",
                "expiry": "неделя",
                "description": "Это тестовое описание для проверки работы системы"
            }, ensure_ascii=False)
        elif "углы" in prompt_lower or "angles" in prompt_lower:
            return json.dumps([{
                "angle_text": "Как использовать эту новость для заработка",
                "offer_connection": "Связать с финансовыми услугами",
                "pain_point": "Страх упустить возможность",
                "creative_type": "новостной",
                "priority": "A"
            }], ensure_ascii=False)
        elif "заголовки" in prompt_lower or "headlines" in prompt_lower:
            return json.dumps([
                {"text": "Срочно! Важная новость для вашего бизнеса", "format": "шок"},
                {"text": "Как это повлияет на ваши финансы?", "format": "вопрос"},
                {"text": "3 факта, которые нужно знать сегодня", "format": "цифра"}
            ], ensure_ascii=False)
        elif "риски" in prompt_lower or "risks" in prompt_lower:
            return json.dumps({
                "legal_risks": [],
                "ban_risks": [],
                "audience_negativity_risk": "низкий",
                "reputation_risk": "низкий",
                "expiration": "7 дней"
            }, ensure_ascii=False)
        else:
            return json.dumps({"result": "success"}, ensure_ascii=False)
    
    def _get_language(self, geo: str) -> str:
        langs = {
            "Germany": "немецкий",
            "Brazil": "португальский",
            "USA": "английский",
            "India": "хинди"
        }
        return langs.get(geo, "русский")
    
    async def classify_infopovod(self, news_item: Dict[str, Any], geo: str) -> Dict[str, Any]:
        language = self._get_language(geo)
        
        prompt = f"""Проанализируй эту новость для маркетинга в {geo}.

Новость: {news_item.get('title', '')}
Текст: {news_item.get('raw_content', '')[:500]}

Верни только JSON:
{{
  "title": "Краткий заголовок на {language} (макс 100 символов)",
  "category": "экономика",
  "trigger": "деньги",
  "expiry": "неделя", 
  "description": "2 предложения на {language} почему это важно"
}}"""
        
        try:
            response = await self._call_llm(prompt, settings.LLM_TEMPERATURE_CLASSIFY)
            result = json.loads(response)
        except Exception as e:
            logger.error(f"Classification error: {e}")
            result = {
                "title": news_item.get('title', 'Новость')[:100],
                "category": "экономика",
                "trigger": "деньги",
                "expiry": "неделя",
                "description": f"Важная новость из {geo}"
            }
        
        result["source_url"] = news_item.get("source_url", "")
        result["source_type"] = str(news_item.get("source_type", ""))
        result["date"] = str(news_item.get("date", ""))
        result["raw_content"] = news_item.get("raw_content", "")
        result["geo"] = geo
        
        return result
    
    async def generate_angles(self, infopovod: Dict[str, Any], geo: str, offer_context: str = "финансовые услуги") -> List[Dict[str, Any]]:
        language = self._get_language(geo)
        
        prompt = f"""Сгенерируй 3 маркетинговых угла.

Новость: {infopovod.get('title', '')}
GEO: {geo}
Триггер: {infopovod.get('trigger', 'деньги')}

Верни JSON массив из 3 объектов с полями:
- angle_text (текст угла на {language})
- offer_connection (как связать с {offer_context})
- pain_point (боль аудитории)
- creative_type (новостной/эмоциональный)
- priority (A/B/C)"""
        
        try:
            response = await self._call_llm(prompt, settings.LLM_TEMPERATURE_GENERATE)
            
            data = json.loads(response)
            if isinstance(data, list):
                angles = data
            elif isinstance(data, dict) and "angles" in data:
                angles = data["angles"]
            else:
                angles = []
            
            for angle in angles:
                angle["infopovod_id"] = infopovod.get("title", "")
            
            return angles[:3]
            
        except Exception as e:
            logger.error(f"Angle generation error: {e}")
            return [{
                "angle_text": f"Как {infopovod.get('category', 'новость')} влияет на ваши финансы",
                "offer_connection": f"Связать с {offer_context}",
                "pain_point": "Страх потерять деньги",
                "creative_type": "новостной",
                "priority": "A",
                "infopovod_id": infopovod.get("title", "")
            }]
    
    async def generate_headlines(self, angles: List[Dict[str, Any]], geo: str) -> List[Dict[str, Any]]:
        if not angles:
            return []
        
        language = self._get_language(geo)
        all_headlines = []
        
        for idx, angle in enumerate(angles[:3]):
            prompt = f"""Сгенерируй 3 заголовка.

Угол: {angle.get('angle_text', '')}
Формат: вопрос, шок, цифра, интрига
Язык: {language}

Верни ТОЛЬКО JSON массив, например:
[{{"text": "заголовок1", "format": "шок"}}, {{"text": "заголовок2", "format": "вопрос"}}]"""
            
            try:
                response = await self._call_llm(prompt, 0.9)
                
                response = response.strip()
                
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                elif '```' in response:
                    response = response.split('```')[1].split('```')[0]
                
                response = response.strip()
                
                try:
                    data = json.loads(response)
                except json.JSONDecodeError:
                    match = re.search(r'\[.*\]', response, re.DOTALL)
                    if match:
                        data = json.loads(match.group())
                    else:
                        raise ValueError("No JSON array found")
                
                if isinstance(data, list):
                    headlines = data
                elif isinstance(data, dict) and "headlines" in data:
                    headlines = data["headlines"]
                else:
                    headlines = []
                
                for hl in headlines:
                    if isinstance(hl, dict):
                        hl["angle_id"] = idx
                        hl["angle_text"] = angle.get('angle_text', '')
                        hl["length_chars"] = len(hl.get("text", ""))
                        all_headlines.append(hl)
                    else:
                        all_headlines.append({
                            "text": str(hl),
                            "format": "интрига",
                            "angle_id": idx,
                            "angle_text": angle.get('angle_text', ''),
                            "length_chars": len(str(hl))
                        })
                
            except Exception as e:
                logger.error(f"Headline error for angle {idx}: {e}")
                all_headlines.append({
                    "text": f"{angle.get('angle_text', 'Важная новость')[:50]}",
                    "format": "шок",
                    "length_chars": 50,
                    "angle_id": idx,
                    "angle_text": angle.get('angle_text', '')
                })
        
        return all_headlines
    
    async def assess_risks(self, infopovod: Dict[str, Any], geo: str) -> Dict[str, Any]:
        prompt = f"""Оцени риски для новости в {geo}.

Новость: {infopovod.get('title', '')}

Верни JSON: {{"legal_risks": [], "ban_risks": [], "audience_negativity_risk": "низкий", "reputation_risk": "низкий", "expiration": "7 дней"}}"""
        
        try:
            response = await self._call_llm(prompt, 0.2)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Risk assessment error: {e}")
            return {
                "legal_risks": [],
                "ban_risks": [],
                "audience_negativity_risk": "низкий",
                "reputation_risk": "низкий",
                "expiration": "7 дней"
            }
    
    async def generate_top_recommendations(self, all_results: List[Dict[str, Any]], geo: str, limit: int = 5) -> List[Dict[str, Any]]:
        recommendations = []
        
        for i, result in enumerate(all_results[:limit]):
            infopovod = result.get("infopovod", {})
            angles = result.get("angles", [])
            
            if angles:
                recommendations.append({
                    "infopovod_title": infopovod.get("title", "")[:60],
                    "angle_text": angles[0].get("angle_text", "")[:80],
                    "recommendation_reason": f"Основано на триггере: {infopovod.get('trigger', 'деньги')}",
                    "headlines": ["Заголовок для теста 1", "Заголовок для теста 2", "Заголовок для теста 3"],
                    "freshness_score": 8,
                    "trigger_strength": 7,
                    "offer_fit": 8
                })
        
        return recommendations


llm_processor = LLMProcessor()