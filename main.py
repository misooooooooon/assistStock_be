from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from data_loader import DataLoader
from analyzer import Analyzer
from predictor import Predictor
from optimizer import Optimizer

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

@app.on_event("startup")
async def startup_event():
    # Start optimization loop in background automatically
    import asyncio
    asyncio.create_task(optimizer.run_optimization_loop())
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
    us_targets = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "AMD", "INTC", 
        "META", "NFLX", "ADBE", "CRM", "CSCO", "PEP", "AVGO", "TXN",
        "QCOM", "COST", "SBUX", "AMGN", "HON", "IBM", "ORCL", "CAT",
        "DE", "GS", "JPM", "V", "MA", "DIS", "NKE", "KO"
    ]
    
    kr_targets = {
        "005930.KS": "삼성전자 (Samsung Elec)",
        "000660.KS": "SK하이닉스 (SK Hynix)",
        "035420.KS": "NAVER", 
        "035720.KS": "카카오 (Kakao)",
        "005380.KS": "현대차 (Hyundai Motor)",
        "000270.KS": "기아 (Kia)",
        "005490.KS": "POSCO홀딩스",
        "068270.KS": "셀트리온 (Celltrion)",
        "051910.KS": "LG화학 (LG Chem)",
        "373220.KS": "LG에너지솔루션",
        "003550.KS": "LG (LG Corp)",
        "015760.KS": "한국전력 (KEPCO)",
        "032640.KS": "LG유플러스",
        "017670.KS": "SK텔레콤",
        "006400.KS": "삼성SDI",
        "105560.KS": "KB금융",
        "055550.KS": "신한지주",
        "086790.KS": "하나금융지주",
        "036570.KS": "엔씨소프트 (NCSoft)",
        "251270.KS": "넷마블 (Netmarble)"
    }
    
    # Select targets
    target_list = list(kr_targets.keys()) if market == "KR" else us_targets
    
    recommendations = []
    
    data_map = data_loader.get_multiple_stocks(target_list, period="6mo")
    
    for ticker, df in data_map.items():
        # Get Display Name
        display_name = kr_targets.get(ticker, ticker) if market == "KR" else ticker

        # 1. Technical Analysis (Optimized)
        tech_analysis = analyzer.analyze_stock(df, params=optimizer.best_params)
        
        # 2. Fundamental Analysis (New)
        raw_fundamentals = data_loader.get_fundamentals(ticker)
        fund_analysis = analyzer.analyze_fundamentals(raw_fundamentals)
        
        # 3. Combine Score
        # Tech score is usually -2 to +2. Fund score is similar.
        total_score = tech_analysis["score"] + fund_analysis["score"]
        
        if tech_analysis["signal"] == "Buy" or total_score >= 3.0:
            recommendations.append({
                "ticker": ticker,
                "name": display_name,
                "analysis": {
                    **tech_analysis,
                    "fundamental": fund_analysis
                },
                "total_score": total_score
            })
            
    # Sort by Signal (Buy > Neutral > Sell) then Total Score
    def sort_key(x):
        signal_priority = 0
        if x["analysis"]["signal"] == "Buy":
            signal_priority = 2
        elif x["analysis"]["signal"] == "Neutral":
            signal_priority = 1
        return (signal_priority, x["total_score"])

    recommendations.sort(key=sort_key, reverse=True)
            
    return {"recommendations": recommendations}

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
        
    prediction = predictor.predict_next_movement(df)
    
    # Add News Sentiment with Market context
    news = data_loader.get_news(request.ticker, market=market)
    sentiment = analyzer.analyze_news_sentiment(news)
    
    # Append sentiment to reasoning
    if sentiment["sentiment"] != "Neutral":
        prediction["reasoning"] += f" [News Sentiment: {sentiment['sentiment']} ({sentiment['score']})]"
        
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
