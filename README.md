# AI Cryptocurrency Trading Bot

Python-based trading system that uses machine learning to generate signals and evaluate strategies over historical market data.

## Why This Project
Manual strategy testing is slow and inconsistent. This project automates ingestion, feature engineering, model evaluation, and backtesting to create a repeatable decision pipeline.

## Impact
- Processed 10,000+ historical market intervals in backtesting runs
- Reduced manual strategy testing time through automated evaluation workflows
- Improved experiment consistency with reusable pipelines and metrics

## Core Features
- Market data ingestion via API
- Feature engineering and time-series analysis
- ML-driven signal generation and forecasting
- Backtesting with configurable risk management
- Performance analytics (returns, drawdown, win/loss behavior)

## System Design
End-to-end modular architecture:
1. Ingestion Layer: pulls historical/near-real-time market data
2. Processing Layer: cleaning, normalisation, feature generation
3. Modeling Layer: train/evaluate prediction models
4. Strategy Layer: transforms signals into trading decisions
5. Evaluation Layer: backtesting plus performance metrics

## Tech Stack
- Python
- Pandas and NumPy
- scikit-learn (or equivalent ML tooling)
- API integrations for market data

## Quick Start
```bash
git clone https://github.com/mahir2002/trading-bot.git
cd trading-bot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

## Example Outputs
- Strategy performance summary table
- Equity curve chart
- Drawdown analysis chart

## Screenshots
Add screenshots in docs/images and reference them here:
- docs/images/equity-curve.png
- docs/images/backtest-metrics.png

## Roadmap
- Add walk-forward validation
- Add model versioning and experiment tracking
- Add paper-trading mode
