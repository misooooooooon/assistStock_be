import pandas as pd
import numpy as np

class Analyzer:
    def __init__(self):
        pass

    def calculate_rsi(self, data: pd.DataFrame, window: int = 14) -> pd.Series:
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_sma(self, data: pd.DataFrame, window: int) -> pd.Series:
        return data['Close'].rolling(window=window).mean()

    def calculate_ema(self, data: pd.DataFrame, window: int) -> pd.Series:
        return data['Close'].ewm(span=window, adjust=False).mean()

    def calculate_bollinger(self, data: pd.DataFrame, window: int = 20, dev: int = 2):
        sma = data['Close'].rolling(window=window).mean()
        std = data['Close'].rolling(window=window).std()
        upper = sma + (std * dev)
        lower = sma - (std * dev)
        return upper, lower

    def check_volume_surge(self, data: pd.DataFrame, multiplier: float = 2.0) -> bool:
        """
        Checks if the last day's volume is significantly higher than the average.
        """
        if len(data) < 20: return False
        
        avg_volume = data['Volume'].iloc[-21:-1].mean()
        last_volume = data['Volume'].iloc[-1]
        
        return last_volume > (avg_volume * multiplier)

    def analyze_stock(self, df: pd.DataFrame, params: dict = None) -> dict:
        """
        Analyzes stock using provided parameters. 
        """
        if df.empty or len(df) < 50:
            return {"signal": "Neutral", "reason": "Insufficient data"}

        if params is None:
            params = {
                "strategy_RSI": True,
                "strategy_MA": True,
                "rsi_window": 14,
                "rsi_buy": 30,
                "rsi_sell": 70,
                "ma_short": 20,
                "ma_long": 50
            }

        df['RSI'] = self.calculate_rsi(df, params.get('rsi_window', 14))
        df['SMA_Short'] = self.calculate_sma(df, params.get('ma_short', 20))
        df['SMA_Long'] = self.calculate_sma(df, params.get('ma_long', 50))
        
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        signals = []
        score = 0
        
        # --- Strategy 1: RSI ---
        if params.get('strategy_RSI', True):
            if last_row['RSI'] < params.get('rsi_buy', 30):
                signals.append(f"RSI Oversold ({last_row['RSI']:.1f})")
                score += 1
            elif last_row['RSI'] > params.get('rsi_sell', 70):
                signals.append(f"RSI Overbought ({last_row['RSI']:.1f})")
                score -= 1

        # --- Strategy 2: Moving Average Crossover ---
        if params.get('strategy_MA', True):
            prev_short = prev_row['SMA_Short']
            prev_long = prev_row['SMA_Long']
            curr_short = last_row['SMA_Short']
            curr_long = last_row['SMA_Long']

            if prev_short < prev_long and curr_short > curr_long:
                signals.append("Golden Cross (Trend Reversal)")
                score += 2
            elif prev_short > prev_long and curr_short < curr_long:
                signals.append("Dead Cross (Trend Reversal)")
                score -= 2
            
            # Trend Check
            if last_row['SMA_Short'] > last_row['SMA_Long']:
                score += 0.5
        
        # --- Strategy 3: Volume Surge ---
        if self.check_volume_surge(df):
            signals.append("Volume Surge (High Interest)")
            score += 1.5

        decision = "Neutral"
        if score >= 1.5:
            decision = "Buy"
        elif score <= -1.5:
            decision = "Sell"

        return {
            "signal": decision,
            "score": score,
            "details": signals,
            "current_price": last_row['Close'],
            "rsi": last_row['RSI'] if not pd.isna(last_row['RSI']) else 0
        }

    def analyze_fundamentals(self, info: dict) -> dict:
        """
        Analyzes fundamental data to determine if the stock is undervalued or safe.
        """
        score = 0
        insights = []
        is_undervalued = False
        is_growth = False

        if not info:
            return {"score": 0, "insights": [], "badges": []}

        # 1. P/E Ratio (Value Check)
        pe = info.get("trailingPE")
        if pe:
            if pe < 20: 
                score += 2
                insights.append(f"Low P/E Ratio ({pe:.1f}) - Potentially Undervalued")
                is_undervalued = True
            elif pe > 50:
                score -= 1
                insights.append(f"High P/E Ratio ({pe:.1f}) - Premium Priced")

        # 2. Profit Margins (Quality Check)
        pm = info.get("profitMargins")
        if pm:
            if pm > 0.2:
                score += 1.5
                insights.append(f"High Profit Margin ({pm*100:.1f}%)")
            elif pm < 0:
                score -= 2
                insights.append("Negative Profit Margin - Unprofitable")

        # 3. Revenue Growth (Growth Check)
        rg = info.get("revenueGrowth")
        if rg:
            if rg > 0.15:
                score += 1.5
                insights.append(f"Strong Revenue Growth ({rg*100:.1f}%)")
                is_growth = True
        
        # Badges
        badges = []
        if is_undervalued: badges.append("Undervalued")
        if is_growth: badges.append("High Growth")
        if pm and pm > 0.3: badges.append("Cash Cow")

        return {
            "score": score,
            "insights": insights,
            "badges": badges,
            "key_metrics": {
                "P/E": pe,
                "Market Cap": info.get("marketCap"),
                "Profit Margin": pm
            }
        }

    def analyze_news_sentiment(self, news_data: dict) -> dict:
        """
        Analyzes news headlines for sentiment w/ Korean translation.
        Returns a sentiment score (-1 to 1) and key headlines.
        """
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source='auto', target='ko')
        
        news_list = news_data.get("items", [])
        sources = news_data.get("sources", [])
        
        if not news_list:
            return {
                "sentiment": "No News", 
                "score": 0, 
                "headlines": [],
                "message": f"Searched {', '.join(sources)} for past 7 days but found no relevant news."
            }

        score = 0
        headlines = []
        
        # Keywords
        positive_words = ["surge", "jump", "high", "profit", "record", "beat", "bull", "growth", "up", "soar", "gain", "strong", "buy"]
        negative_words = ["drop", "fall", "low", "loss", "miss", "bear", "crash", "down", "weak", "plunge", "concern", "risk", "sell"]

        count = 0
        for item in news_list[:7]: # Increased to analyze top 7 news
            title_en = (item.get("title") or "").lower()
            
            # Translate to Korean
            try:
                title_ko = translator.translate(item.get("title") or "")
            except:
                title_ko = item.get("title") or ""
            
            # Update item for frontend
            item["title"] = title_ko
            item["title_en"] = item.get("title") # Keep original
            
            headlines.append(item)
            
            # Simple scoring (using English title)
            item_score = 0
            for word in positive_words:
                if word in title_en:
                    item_score += 1
            for word in negative_words:
                if word in title_en:
                    item_score -= 1
            
            score += item_score
            count += 1
            
        final_sentiment = "Neutral"
        if score >= 2:
            final_sentiment = "Positive"
        elif score <= -2:
            final_sentiment = "Negative"
            
        return {
            "sentiment": final_sentiment,
            "score": score,
            "headlines": headlines 
        }
