from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from data_loader import DataLoader
from analyzer import Analyzer
from predictor import Predictor
from optimizer import Optimizer
from scheduler import ReportGenerator
import json
import os

app = FastAPI(title="Stock Investment Advisor", version="1.0.0")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity (or specific Vercel URL later)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize modules
data_loader = DataLoader()
analyzer = Analyzer()
optimizer = Optimizer(data_loader, analyzer)
report_generator = ReportGenerator(data_loader, analyzer, optimizer)

@app.on_event("startup")
async def startup_event():
    # Start optimization loop in background automatically
    import asyncio
    asyncio.create_task(optimizer.run_optimization_loop())
    # Start Scheduler Loop
    asyncio.create_task(report_generator.run_scheduler_loop())
predictor = Predictor()

class StockRequest(BaseModel):
    ticker: str
    period: str = "1mo"

@app.get("/")
def read_root():
    return {"message": "Welcome to Stock Investment Advisor API"}

@app.get("/recommendations")
def get_recommendations(market: str = "KR"):
    """
    Returns stock recommendations based on market (KR/US).
    Default is KR.
    """
    """
    Returns stock recommendations based on market (KR/US).
    Reads from pre-calculated JSON file for instant response.
    """
    try:
        file_path = f"backend/data_cache/recommendations_{market.lower()}.json"
        
        # If cache exists, return it
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {"recommendations": data["recommendations"], "updated_at": data["updated_at"]}
                
        # Fallback if no cache (First run)
        return {"recommendations": [], "message": "Analyzing data in background... Please wait for the next update."}
        
    except Exception as e:
        print(f"Error reading cache: {e}")
        return {"recommendations": [], "error": str(e)}

@app.post("/predict")
def predict_stock(request: StockRequest):
    """
    Predicts the short-term outlook for a specific stock.
    Request body: { ticker: "...", market: "KR"|"US" }
    """
    # Simple market detection from ticker
    market = "KR" if ".KS" in request.ticker or ".KQ" in request.ticker else "US"
    
    df = data_loader.get_stock_data(request.ticker, period="6mo")
    if df.empty:
        return {"error": "Stock data not found"}

    # 1. Analyze News Sentiment FIRST
    news = data_loader.get_news(request.ticker, market=market)
    sentiment = analyzer.analyze_news_sentiment(news)
    
    # 2. Predict with Sentiment adjustment
    prediction = predictor.predict_next_movement(df, sentiment_score=sentiment['score'])
    
    # Append detailed sentiment info string if needed (already handled in predictor logic, but keeping this for safety or extra detail)
    # The predictor now adds the adjustment note, so we don't strictly need to append more, 
    # but we can keep the source/score info if not present.
    # predictor.py adds: "News Sentiment (3) adjusted target by 1.5%."
        
    return {
        "ticker": request.ticker, 
        "prediction": prediction,
        "news_sentiment": sentiment,
        "market": market
    }

@app.post("/optimization/run")
def run_optimization(background_tasks: BackgroundTasks):
    """
    Triggers the self-optimization loop (Genetic Algorithm).
    Runs for 10 generations with Population 10 = 100 evaluations.
    """
    background_tasks.add_task(optimizer.run_simulation, "SPY", 10)
    return {"message": "Optimization (Evolution) started in background"}

@app.get("/optimization/status")
def get_optimization_status():
    """
    Returns the status of the self-optimization loop.
    """
    return {
        "best_params": optimizer.best_params, 
        "best_score": optimizer.best_score
    }

@app.post("/admin/update")
def trigger_update(background_tasks: BackgroundTasks, market: str = "KR"):
    """
    Manually triggers the market analysis report.
    """
    background_tasks.add_task(report_generator.generate_market_report, market)
    return {"message": f"Market analysis for {market} triggered in background."}
