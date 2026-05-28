import asyncio
import aiohttp
import feedparser
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from urllib.parse import quote
import logging

from config import settings
from models.schemas import SourceTypeEnum, RawNewsItem

logger = logging.getLogger(__name__)


class NewsCollector:
    def __init__(self):
        self.sources_config = {
            "Germany": {
                "rss": [
                    "https://www.spiegel.de/schlagzeilen/index.rss",
                    "https://www.bild.de/rssfeeds/volltext/volltext.rss",
                    "https://www.faz.net/rss/aktuell/",
                    "https://www.zeit.de/index/rss",
                    "https://www.tagesschau.de/xml/rss2"
                ],
                "keywords": ["Deutschland", "Wirtschaft", "Steuern", "Banken", "Krise"],
                "lang": "de"
            },
            "Brazil": {
                "rss": [
                    "https://g1.globo.com/rss/g1/",
                    "https://www.uol.com.br/rss/noticias.xml",
                    "https://oglobo.globo.com/rss/",
                    "https://noticias.r7.com/rss.xml",
                    "https://exame.com/rss/"
                ],
                "keywords": ["Brasil", "economia", "impostos", "bancos", "crise"],
                "lang": "pt"
            },
            "USA": {
                "rss": [
                    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
                    "http://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml",
                    "https://www.wsj.com/xml/rss/3_7085.xml",
                    "https://feeds.bloomberg.com/markets/news.rss",
                    "https://www.cnbc.com/id/100003114/device/rss/rss.html"
                ],
                "keywords": ["US", "economy", "taxes", "banks", "crisis", "inflation"],
                "lang": "en"
            },
            "India": {
                "rss": [
                    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
                    "https://www.thehindu.com/news/feeder/default.rss",
                    "https://www.business-standard.com/rss/latest.rss",
                    "https://economictimes.indiatimes.com/rssfeeddefault.cms"
                ],
                "keywords": ["India", "economy", "tax", "banks", "crisis", "budget"],
                "lang": "hi"
            }
        }
    
    async def collect(self, geo: str) -> List[Dict]:
        if geo not in self.sources_config:
            logger.warning(f"No sources configured for {geo}")
            return []
        
        tasks = []
        config = self.sources_config[geo]
        
        for rss_url in config["rss"]:
            tasks.append(self._fetch_rss(rss_url, geo))
        
        if settings.GOOGLE_API_KEY and settings.GOOGLE_SEARCH_ENGINE_ID:
            tasks.append(self._fetch_google_news(geo, config["keywords"], config["lang"]))
        
        if settings.TWITTER_BEARER_TOKEN:
            for keyword in config["keywords"][:3]:
                tasks.append(self._fetch_twitter(keyword, config["lang"], geo))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_news = []
        seen_titles = set()
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error in task: {result}")
                continue
            if not isinstance(result, list):
                continue
                
            for item in result:
                title_key = item["title"].lower()[:100]
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    all_news.append(item)
        
        all_news.sort(key=lambda x: x.get("date", datetime.min), reverse=True)
        return all_news[:settings.MAX_NEWS_PER_GEO]
    
    async def _fetch_rss(self, url: str, geo: str) -> List[Dict]:
        try:
            feed = feedparser.parse(url)
            items = []
            
            for entry in feed.entries[:10]:
                pub_date = None
                if entry.get("published_parsed"):
                    pub_date = datetime(*entry.published_parsed[:6])
                elif entry.get("updated_parsed"):
                    pub_date = datetime(*entry.updated_parsed[:6])
                else:
                    pub_date = datetime.now() - timedelta(hours=12)
                
                if (datetime.now() - pub_date).days > settings.NEWS_DAYS_BACK:
                    continue
                
                items.append({
                    "title": entry.title,
                    "source_url": entry.link,
                    "source_type": SourceTypeEnum.RSS,
                    "date": pub_date,
                    "raw_content": entry.get("summary", "")[:1000],
                    "geo_hint": geo
                })
            
            logger.info(f"Fetched {len(items)} items from {url}")
            return items
            
        except Exception as e:
            logger.error(f"RSS parse error {url}: {e}")
            return []
    
    async def _fetch_google_news(self, geo: str, keywords: List[str], lang: str) -> List[Dict]:
        if not settings.GOOGLE_API_KEY:
            return []
        
        items = []
        async with aiohttp.ClientSession() as session:
            for keyword in keywords[:3]:
                try:
                    url = "https://www.googleapis.com/customsearch/v1"
                    params = {
                        "key": settings.GOOGLE_API_KEY,
                        "cx": settings.GOOGLE_SEARCH_ENGINE_ID,
                        "q": f"{keyword} {geo} news",
                        "dateRestrict": f"d{settings.NEWS_DAYS_BACK}",
                        "sort": "date",
                        "num": 5
                    }
                    
                    async with session.get(url, params=params) as resp:
                        data = await resp.json()
                        
                        for item in data.get("items", []):
                            items.append({
                                "title": item.get("title", ""),
                                "source_url": item.get("link", ""),
                                "source_type": SourceTypeEnum.GOOGLE_NEWS,
                                "date": datetime.now() - timedelta(hours=6),
                                "raw_content": item.get("snippet", ""),
                                "geo_hint": geo
                            })
                            
                except Exception as e:
                    logger.error(f"Google News error for {keyword}: {e}")
                    continue
        
        return items
    
    async def _fetch_twitter(self, keyword: str, lang: str, geo: str) -> List[Dict]:
        if not settings.TWITTER_BEARER_TOKEN:
            return []
        
        items = []
        async with aiohttp.ClientSession() as session:
            try:
                url = "https://api.twitter.com/2/tweets/search/recent"
                headers = {"Authorization": f"Bearer {settings.TWITTER_BEARER_TOKEN}"}
                params = {
                    "query": f"{keyword} lang:{lang} -is:retweet",
                    "max_results": 10,
                    "tweet.fields": "created_at,public_metrics"
                }
                
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        for tweet in data.get("data", []):
                            items.append({
                                "title": tweet["text"][:100],
                                "source_url": f"https://twitter.com/i/web/status/{tweet['id']}",
                                "source_type": SourceTypeEnum.TWITTER,
                                "date": datetime.fromisoformat(tweet["created_at"].replace("Z", "+00:00")),
                                "raw_content": tweet["text"],
                                "geo_hint": geo
                            })
                    else:
                        logger.warning(f"Twitter API error: {resp.status}")
                        
            except Exception as e:
                logger.error(f"Twitter error for {keyword}: {e}")
        
        return items
    
    async def _fetch_telegram(self, channels: List[str]) -> List[Dict]:
        # TODO:
        return []


news_collector = NewsCollector()