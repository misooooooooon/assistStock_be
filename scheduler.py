import asyncio
import json
import os
import time
from datetime import datetime
from tickers import get_tickers

class ReportGenerator:
    def __init__(self, data_loader, analyzer, optimizer, output_dir="backend/data_cache"):
        self.data_loader = data_loader
        self.analyzer = analyzer
        self.optimizer = optimizer
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    async def generate_market_report(self, market="KR"):
        """
        Fetches data for ALL target tickers, analyzes them, and saves a JSON report.
        """
        print(f"[{datetime.now()}] Starting Market Report Generation for {market}...")
        start_time = time.time()
        
        targets = get_tickers(market)
        recommendations = []
        
        # Batch Fetching (could still be slow, improved data_loader might be needed later for async)
        # For now, we use the existing sync data_loader but it's running in a background thread/task effectively
        
        for ticker in targets:
            try:
                # 1. Fetch Price Data
                df = self.data_loader.get_stock_data(ticker, period="6mo")
                if df.empty or len(df) < 50:
                    continue
                
                # 2. Analyze
                tech_analysis = self.analyzer.analyze_stock(df, params=self.optimizer.best_params)
                
                # 3. Fundamental Analysis
                # Optim: Only fetch fundamentals if technicals are decent or it's a major periodic scan
                # To save time, we might skip deep fundamentals for "Sell" signals, but let's do all for now to have a complete list
                raw_fundamentals = self.data_loader.get_fundamentals(ticker)
                fund_analysis = self.analyzer.analyze_fundamentals(raw_fundamentals)
                
                total_score = tech_analysis["score"] + fund_analysis["score"]
                
                # 4. News Sentiment (Optim: ONLY for high Potential stocks)
                # Fetching news for 100 stocks takes too long.
                # Only if Signal is Buy or Score >= 3
                sentiment_score = 0
                if tech_analysis["signal"] == "Buy" or total_score >= 2.0:
                    # Creating a dummy "news" object from data_loader isn't super efficient if we just want a quick check
                    # But let's do it properly for the top candidates
                    try:
                        news = self.data_loader.get_news(ticker, market=market)
                        sentiment = self.analyzer.analyze_news_sentiment(news)
                        sentiment_score = sentiment["score"]
                        # Adjust total score slightly with news
                        if sentiment["sentiment"] == "Positive":
                            total_score += 0.5
                        elif sentiment["sentiment"] == "Negative":
                            total_score -= 0.5
                    except Exception as e:
                        print(f"News fetch error for {ticker}: {e}")

                # Display Name (Simple Logic for now, can be improved with a mapping file)
                name = raw_fundamentals.get("longName", ticker)
                # For KR, try to use a preset map if available in main (or duplicating it here is simpler)
                
                recommendations.append({
                    "ticker": ticker,
                    "name": name,
                    "analysis": {
                        **tech_analysis,
                        "fundamental": fund_analysis
                    },
                    "total_score": total_score,
                    "market": market
                })
                
                # Sleep briefly to be nice to APIs if needed
                # await asyncio.sleep(0.1) 

            except Exception as e:
                print(f"Error processing {ticker}: {e}")
                
        # Sort by Score
        recommendations.sort(key=lambda x: x["total_score"], reverse=True)
        
        # Save to JSON
        output_file = os.path.join(self.output_dir, f"recommendations_{market.lower()}.json")
        result = {
            "updated_at": datetime.now().isoformat(),
            "count": len(recommendations),
            "market": market,
            "recommendations": recommendations
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        elapsed = time.time() - start_time
        print(f"[{datetime.now()}] Finished {market} Report. {len(recommendations)} stocks. Time: {elapsed:.2f}s")
        return result

    async def run_scheduler_loop(self):
        """
        Runs the report generation periodically.
        """
        while True:
            # Update both markets
            await self.generate_market_report("KR")
            await self.generate_market_report("US")
            
            # Wait for 1 hour (3600 seconds) before next update
            # Use 60 mins for production. 
            print("Scheduler sleeping for 60 minutes...")
            await asyncio.sleep(3600) 
