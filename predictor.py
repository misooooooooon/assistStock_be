import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

class Predictor:
    def __init__(self):
        self.model = LinearRegression()

    def predict_next_movement(self, df: pd.DataFrame, days_ahead=7, sentiment_score=0):
        """
        Predicts the price trend for the next 7 days.
        Returns graph-ready data and text reasoning.
        sentiment_score: -5 to +5 range from news analysis.
        """
        if len(df) < 30:
            return {"error": "Insufficient Data"}

        # Train on last 30 days
        recent_data = df.tail(30).reset_index(drop=True)
        X = np.array(recent_data.index).reshape(-1, 1)
        y = recent_data['Close'].values

        self.model.fit(X, y)

        # Future indices
        last_index = X[-1][0]
        future_indices = np.array([last_index + i for i in range(1, days_ahead + 1)]).reshape(-1, 1)
        predictions = self.model.predict(future_indices)
        
        # Apply Sentiment Adjustment
        # factor: +1 score -> +0.5% boost. Max +2.5% boost at score +5.
        sentiment_factor = 1 + (sentiment_score * 0.005) 
        predictions = predictions * sentiment_factor
        
        slope = self.model.coef_[0]
        r_sq = self.model.score(X, y)

        # Logic for reasoning
        reasoning = []
        if slope > 0:
            strength = "Strong" if slope > (y[-1] * 0.005) else "Moderate" # rough heuristic
            reasoning.append(f"{strength} Upward Trend detected (Slope: {slope:.2f}).")
        else:
            strength = "Strong" if slope < -(y[-1] * 0.005) else "Moderate"
            reasoning.append(f"{strength} Downward Trend detected (Slope: {slope:.2f}).")

        if r_sq > 0.5:
            reasoning.append(f"Price movement is consistent (R²: {r_sq:.2f}).")
        else:
            reasoning.append(f"Price movement is volatile (R²: {r_sq:.2f}).")
            
        if sentiment_score != 0:
            impact = "Positive" if sentiment_score > 0 else "Negative"
            reasoning.append(f"News Sentiment ({sentiment_score}) adjusted target by {(sentiment_factor-1)*100:.1f}%.")

        # Format data for Recharts: [{day: 'Day 1', price: 100, type: 'History'}, ...]
        graph_data = []
        
        # Add slight overlap/history
        for i in range(len(recent_data)):
            graph_data.append({
                "day": f"D-{30-i}",
                "price": round(recent_data['Close'].iloc[i], 2),
                "type": "History"
            })
            
        for i, pred in enumerate(predictions):
            graph_data.append({
                "day": f"D+{i+1}",
                "price": round(pred, 2),
                "type": "Forecast"
            })

        return {
            "outlook": "Bullish" if predictions[-1] > y[-1] else "Bearish", # Outlook based on final adjusted price
            "current_price": y[-1],
            "predicted_price_7d": predictions[-1], 
            "graph_data": graph_data,
            "reasoning": " ".join(reasoning)
        }
