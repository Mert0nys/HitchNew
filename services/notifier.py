import aiohttp
import logging
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)


class Notifier:
    async def send_report(self, geo: str, report_html: str, report_id: str) -> bool:
        success = True
        
        if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
            success = success and await self._send_telegram(geo, report_id)
        
        if settings.SLACK_WEBHOOK_URL:
            success = success and await self._send_slack(geo, report_id)
        
        return success
    
    async def send_complete_report(self, geo: str, report_html: str) -> bool:
        return await self.send_report(geo, report_html, "")
    
    async def send_error_alert(self, geo: str, error_message: str) -> bool:
        message = f"🚨 *Ошибка мониторинга {geo}*\n\n`{error_message[:200]}`"
        
        success = True
        
        if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
            success = success and await self._send_telegram_message(message)
        
        return success
    
    async def _send_telegram(self, geo: str, report_id: str) -> bool:
        message = f"""🎯 *TrendHunter AI - Новый выпуск*

📍 *GEO:* {geo}
📅 *Дата:* {__import__('datetime').datetime.now().strftime('%d.%m.%Y %H:%M')}

✅ *Мониторинг завершён*

👉 /report_{report_id} - для получения полного отчёта

---
_Сгенерировано автоматически_
"""
        return await self._send_telegram_message(message)
    
    async def _send_telegram_message(self, message: str) -> bool:
        """Отправить сообщение в Telegram"""
        if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
            logger.warning("Telegram not configured")
            return False
        
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json={
                    "chat_id": settings.TELEGRAM_CHAT_ID,
                    "text": message,
                    "parse_mode": "Markdown"
                }) as resp:
                    if resp.status == 200:
                        logger.info("Telegram notification sent")
                        return True
                    else:
                        logger.error(f"Telegram error: {resp.status}")
                        return False
            except Exception as e:
                logger.error(f"Telegram send error: {e}")
                return False
    
    async def _send_slack(self, geo: str, report_id: str) -> bool:
        if not settings.SLACK_WEBHOOK_URL:
            logger.warning("Slack not configured")
            return False
        
        message = {
            "text": f"🎯 *TrendHunter AI - Новый выпуск для {geo}*\nОтчёт готов: #{report_id[:8]}"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(settings.SLACK_WEBHOOK_URL, json=message) as resp:
                    if resp.status == 200:
                        logger.info("Slack notification sent")
                        return True
                    else:
                        logger.error(f"Slack error: {resp.status}")
                        return False
            except Exception as e:
                logger.error(f"Slack send error: {e}")
                return False


# Синглтон
notifier = Notifier()