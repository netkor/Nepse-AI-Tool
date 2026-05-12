AI Insights app

Provides template-based signal explanations, market summaries, and daily recap generation.

Endpoints:
- GET /api/insights/signals/<id>/explain/
- GET /api/insights/market-summary/?days=1
- GET /api/insights/daily-recap/?days=1

Celery tasks:
- insights.tasks.generate_market_summary
- insights.tasks.generate_daily_recap
