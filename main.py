from contextlib import asynccontextmanager
from datetime import datetime
import logging

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import settings
from services.new_collector import NewsCollector
from services.ll_processor import LLMProcessor
from services.airtable_client import AirtableClient
from services.report_generator import ReportGenerator
from services.notifier import Notifier
from routers import monitoring, reports, feedback, goes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
news_collector = NewsCollector()
llm_processor = LLMProcessor()
airtable_client = AirtableClient()
report_generator = ReportGenerator()
notifier = Notifier()


async def run_monitoring_for_geo(geo: str):
    """Запуск полного цикла мониторинга для одного GEO"""
    logger.info(f"Starting monitoring for {geo}")
    
    try:
        # Шаг 1: Сбор новостей
        news_items = await news_collector.collect(geo)
        logger.info(f"Collected {len(news_items)} news for {geo}")
        
        # Шаг 2: Обработка через LLM
        processed_items = []
        for item in news_items[:20]:  # Лимит 20 новостей за раз
            classified = await llm_processor.classify_infopovod(item, geo)
            angles = await llm_processor.generate_angles(classified, geo)
            headlines = await llm_processor.generate_headlines(angles, geo)
            risks = await llm_processor.assess_risks(classified, geo)
            
            processed_items.append({
                "infopovod": classified,
                "angles": angles,
                "headlines": headlines,
                "risks": risks
            })
        
        # Шаг 3: Сохранение в Airtable
        report_id = await airtable_client.save_monitoring_results(geo, processed_items)
        
        # Шаг 4: Генерация отчёта
        report_html = await report_generator.generate_full_report(geo, processed_items)
        
        # Шаг 5: Отправка уведомления
        await notifier.send_report(geo, report_html, report_id)
        
        logger.info(f"Completed monitoring for {geo}")
        
    except Exception as e:
        logger.error(f"Error monitoring {geo}: {str(e)}", exc_info=True)
        await notifier.send_error_alert(geo, str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    for geo in settings.PRIORITY_GEO:
        scheduler.add_job(
            func=run_monitoring_for_geo,
            trigger=IntervalTrigger(days=3),
            args=[geo],
            id=f"monitoring_{geo}",
            replace_existing=True
        )
        logger.info(f"Scheduled monitoring for {geo} every 3 days")
    
    scheduler.start()
    logger.info("Scheduler started")
    
    yield
    scheduler.shutdown()
    logger.info("Scheduler stopped")


app = FastAPI(
    title="TrendHunter AI",
    description="AI-мониторинг инфоповодов и генерация идей под GEO",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["monitoring"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["feedback"])
app.include_router(goes.router, prefix="/api/v1/geos", tags=["geos"])


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TrendHunter AI - Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background: #f5f7fa; padding: 40px; }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { color: #1a202c; margin-bottom: 30px; font-size: 32px; }
            .card { background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
            .card h2 { margin-bottom: 20px; color: #2d3748; font-size: 20px; border-left: 4px solid #667eea; padding-left: 16px; }
            .geo-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }
            .geo-item { background: #f7fafc; padding: 20px; border-radius: 10px; border: 1px solid #e2e8f0; transition: all 0.3s; }
            .geo-item:hover { box-shadow: 0 4px 6px rgba(0,0,0,0.1); transform: translateY(-2px); }
            .geo-item strong { font-size: 18px; color: #2d3748; }
            .status { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 500; margin-top: 10px; }
            .status-running { background: #c6f6d5; color: #22543d; }
            .status-idle { background: #fed7d7; color: #742a2a; }
            .btn-group { display: flex; gap: 12px; flex-wrap: wrap; }
            .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-size: 14px; transition: all 0.3s; }
            .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(102,126,234,0.4); }
            .btn-secondary { background: #48bb78; }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; }
            .stat { text-align: center; padding: 16px; background: #f7fafc; border-radius: 10px; }
            .stat-value { font-size: 32px; font-weight: bold; color: #667eea; }
            .stat-label { color: #718096; margin-top: 8px; font-size: 14px; }
            .footer { text-align: center; margin-top: 40px; color: #a0aec0; font-size: 12px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 TrendHunter AI — Мониторинг инфоповодов</h1>
            
            <div class="card">
                <h2>🌍 Статус мониторинга GEO</h2>
                <div class="geo-list" id="geo-status">
                    <div class="geo-item">
                        <strong>🇩🇪 Germany</strong><br>
                        <span class="status" id="status-germany">⏳ Загрузка...</span><br>
                        <small>Последний выпуск: <span id="last-germany">—</span></small>
                    </div>
                    <div class="geo-item">
                        <strong>🇧🇷 Brazil</strong><br>
                        <span class="status" id="status-brazil">⏳ Загрузка...</span><br>
                        <small>Последний выпуск: <span id="last-brazil">—</span></small>
                    </div>
                    <div class="geo-item">
                        <strong>🇺🇸 USA</strong><br>
                        <span class="status" id="status-usa">⏳ Загрузка...</span><br>
                        <small>Последний выпуск: <span id="last-usa">—</span></small>
                    </div>
                    <div class="geo-item">
                        <strong>🇮🇳 India</strong><br>
                        <span class="status" id="status-india">⏳ Загрузка...</span><br>
                        <small>Последний выпуск: <span id="last-india">—</span></small>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>⚡ Быстрые действия</h2>
                <div class="btn-group">
                    <button onclick="runNow('Germany')" class="btn">🚀 Запустить Germany</button>
                    <button onclick="runNow('Brazil')" class="btn">🚀 Запустить Brazil</button>
                    <button onclick="runNow('USA')" class="btn">🚀 Запустить USA</button>
                    <button onclick="runNow('India')" class="btn">🚀 Запустить India</button>
                    <button onclick="viewLastReport()" class="btn btn-secondary">📄 Последний отчёт</button>
                    <button onclick="refreshStats()" class="btn">🔄 Обновить статистику</button>
                </div>
            </div>
            
            <div class="card">
                <h2>📊 Статистика</h2>
                <div class="stats-grid" id="stats">
                    <div class="stat">
                        <div class="stat-value" id="total-ideas">—</div>
                        <div class="stat-label">Всего идей</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" id="success-tests">—</div>
                        <div class="stat-label">Успешных тестов</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" id="avg-time">—</div>
                        <div class="stat-label">Среднее время (мин)</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" id="total-infopovods">—</div>
                        <div class="stat-label">Всего инфоповодов</div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p>🤖 Сгенерировано с помощью TrendHunter AI • Автоматический мониторинг каждые 3 дня</p>
            </div>
        </div>
        
        <script>
            async function runNow(geo) {
                const btn = event.target;
                btn.textContent = '⏳ Запуск...';
                btn.disabled = true;
                try {
                    const response = await fetch(`/api/v1/monitoring/run/${geo}`, { method: 'POST' });
                    const data = await response.json();
                    alert(`✅ ${data.message}\\n⏱ Ожидайте 5-10 минут`);
                    setTimeout(refreshStats, 2000);
                } catch (error) {
                    alert('❌ Ошибка запуска: ' + error.message);
                } finally {
                    btn.textContent = btn.textContent.replace('⏳ Запуск...', '🚀 Запустить ' + geo);
                    btn.disabled = false;
                }
            }
            
            async function viewLastReport() {
                window.open('/api/v1/reports/latest', '_blank');
            }
            
            async function loadStatus() {
                const geos = ['Germany', 'Brazil', 'USA', 'India'];
                for (const geo of geos) {
                    try {
                        const status = await fetch(`/api/v1/monitoring/status/${geo}`).then(r => r.json());
                        const statusElem = document.getElementById(`status-${geo.toLowerCase()}`);
                        const lastElem = document.getElementById(`last-${geo.toLowerCase()}`);
                        
                        if (status.last_run) {
                            statusElem.textContent = '✅ Активен';
                            statusElem.className = 'status status-running';
                            lastElem.textContent = new Date(status.last_run).toLocaleDateString('ru-RU');
                        } else {
                            statusElem.textContent = '⏸ Не запущен';
                            statusElem.className = 'status status-idle';
                            lastElem.textContent = '—';
                        }
                    } catch (e) {
                        console.error(`Error loading status for ${geo}:`, e);
                    }
                }
            }
            
            async function refreshStats() {
                try {
                    const stats = await fetch('/api/v1/monitoring/stats').then(r => r.json());
                    document.getElementById('total-ideas').textContent = stats.total_ideas || 0;
                    document.getElementById('success-tests').textContent = stats.success_tests || 0;
                    document.getElementById('avg-time').textContent = stats.avg_processing_time || '—';
                    document.getElementById('total-infopovods').textContent = stats.total_infopovods || 0;
                } catch (e) {
                    console.error('Error loading stats:', e);
                }
            }
            
            // Загрузка при старте
            loadStatus();
            refreshStats();
            
            // Обновление каждые 30 секунд
            setInterval(() => {
                loadStatus();
                refreshStats();
            }, 30000);
        </script>
    </body>
    </html>
    """


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.get("/api/v1/info")
async def get_info():
    return {
        "name": "TrendHunter AI",
        "version": "1.0.0",
        "description": "AI-мониторинг инфоповодов и генерация идей под GEO",
        "geos": settings.PRIORITY_GEO,
        "features": [
            "Автоматический сбор новостей",
            "Классификация и триггеры",
            "Генерация углов и идей",
            "Создание заголовков",
            "Оценка рисков",
            "Отчёты в HTML",
            "Уведомления в Telegram"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )