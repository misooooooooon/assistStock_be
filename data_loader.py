import yfinance as yf
import pandas as pd
import os

class DataLoader:
    def __init__(self, cache_dir="backend/data_cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def get_stock_data(self, ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """
        Fetches stock data from yfinance with caching.
        """
        cache_file = os.path.join(self.cache_dir, f"{ticker}_{period}_{interval}.pkl")
        
        # Check cache validity (15 minutes = 900 seconds)
        if os.path.exists(cache_file):
            import time
            file_age = time.time() - os.path.getmtime(cache_file)
            if file_age < 900: # 15 minutes
                # print(f"Loading {ticker} from cache")
                return pd.read_pickle(cache_file)

        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)
            
            if df.empty:
                print(f"No data found for {ticker}")
                return pd.DataFrame()
            
            # Ensure index is timezone naive or consistent
            df.index = df.index.tz_localize(None)
            
            # Save to cache
            df.to_pickle(cache_file)
            
            return df
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return pd.DataFrame()

    def get_multiple_stocks(self, tickers: list, period: str = "1y") -> dict:
        data = {}
        for ticker in tickers:
            data[ticker] = self.get_stock_data(ticker, period=period)
        return data

    def get_fundamentals(self, ticker: str) -> dict:
        """
        Fetches fundamental data (P/E, Market Cap, etc.) with 7-day caching.
        """
        import json
        cache_file = os.path.join(self.cache_dir, f"{ticker}_fundamentals.json")
        
        # Check cache validity (7 days = 604800 seconds)
        if os.path.exists(cache_file):
            import time
            file_age = time.time() - os.path.getmtime(cache_file)
            if file_age < 604800: 
                try:
                    with open(cache_file, 'r') as f:
                        return json.load(f)
                except:
                    pass

        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Extract only key indicators to save space
            fundamentals = {
                "trailingPE": info.get("trailingPE"),
                "forwardPE": info.get("forwardPE"),
                "marketCap": info.get("marketCap"),
                "profitMargins": info.get("profitMargins"),
                "revenueGrowth": info.get("revenueGrowth"),
                "sector": info.get("sector"),
                "longName": info.get("longName"),
                "dividendYield": info.get("dividendYield")
            }
            
            # Save to cache
            with open(cache_file, 'w') as f:
                json.dump(fundamentals, f)
            
            return fundamentals
        except Exception as e:
            print(f"Error fetching fundamentals for {ticker}: {e}")
            return {}

    def get_news(self, ticker: str, market: str = "US") -> dict:
        """
        Fetches news.
        If market="KR", uses Korean keywords for searching.
        """
        import json
        import requests
        import xml.etree.ElementTree as ET
        from datetime import datetime
        from dateutil import parser
        
        cache_file = os.path.join(self.cache_dir, f"{ticker}_news_v4.json") # Bump version
        sources_checked = ["Yahoo Finance"]
        
        # Check cache validity (1 hour = 3600 seconds)
        if os.path.exists(cache_file):
            import time
            file_age = time.time() - os.path.getmtime(cache_file)
            if file_age < 3600:
                try:
                    with open(cache_file, 'r') as f:
                        return json.load(f)
                except:
                    pass

        news_items = []
        
        # 1. Try Yahoo Finance (Base Layer) - Works for KS tickers too
        try:
            stock = yf.Ticker(ticker)
            yf_news = stock.news
            if yf_news:
                for item in yf_news:
                    # Parse timestamp
                    pub_time = item.get("providerPublishTime", 0)
                    iso_date = datetime.fromtimestamp(pub_time).isoformat() if pub_time else None
                    
                    news_items.append({
                        "title": item.get("title"),
                        "link": item.get("link"),
                        "source": "Yahoo Finance",
                        "published": iso_date
                    })
        except Exception as e:
            print(f"Error fetching Yahoo news for {ticker}: {e}")

        # 2. Premium Sources via Google News RSS (Aggressive Layer)
        if market == "KR":
            # Strip .KS or .KQ for cleaner search
            clean_ticker = ticker.replace(".KS", "").replace(".KQ", "")
            # Use Korean keywords
            queries = [
                f"{clean_ticker} 주가 전망",
                f"{clean_ticker} 실적 발표"
            ]
        else:
            queries = [
                f"{ticker} stock site:reuters.com OR site:bloomberg.com",
                f"{ticker} stock site:cnbc.com OR site:wsj.com OR site:ft.com"
            ]
        
        for q in queries:
            try:
                sources_checked.append(f"Search: {q}")
                # For KR, we might not want language restrictions strictly, or use hl=ko
                lang_param = "hl=ko&gl=KR&ceid=KR:ko" if market == "KR" else "hl=en-US&gl=US&ceid=US:en"
                url = f"https://news.google.com/rss/search?q={q}+when:30d&{lang_param}"
                
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    root = ET.fromstring(resp.content)
                    for item in root.findall('./channel/item')[:5]: 
                        rss_date = item.find('pubDate').text if item.find('pubDate') is not None else None
                        iso_date = parser.parse(rss_date).isoformat() if rss_date else None

                        news_items.append({
                            "title": item.find('title').text,
                            "link": item.find('link').text,
                            "source": item.find('source').text if item.find('source') is not None else "News",
                            "published": iso_date
                        })
            except Exception as e:
                print(f"Error fetching Premium news for {ticker}: {e}")

        # Deduplication based on title similarity or exact match
        seen_titles = set()
        unique_news = []
        for item in news_items:
            # Simple normalization
            clean_title = (item.get("title") or "").lower().strip()
            if clean_title not in seen_titles and clean_title:
                seen_titles.add(clean_title)
                unique_news.append(item)

        result = {
            "items": unique_news,
            "sources": sources_checked,
            "period": "30 days"
        }
            
        # Save to cache
        try:
            with open(cache_file, 'w') as f:
                json.dump(result, f)
        except:
            pass
        
        return result
