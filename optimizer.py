import random
import json
import os
import numpy as np
from typing import List, Dict
from analyzer import Analyzer
from data_loader import DataLoader

class Optimizer:
    def __init__(self, data_loader: DataLoader, analyzer: Analyzer):
        self.data_loader = data_loader
        self.analyzer = analyzer
        self.history_file = "backend/optimization_history.json"
        self.dna_file = "backend/best_dna.json"
        
        # Load best DNA if exists
        self.best_params = self._load_dna()
        self.best_score = -1000.0

    async def run_optimization_loop(self):
        import asyncio
        print("Background Optimization Loop Started...")
        while True:
            try:
                # Run heavy simulation in a separate thread to not block FastAPI
                await asyncio.to_thread(self.run_simulation, "SPY", 5) # Run 5 generations periodically
                print("Optimization cycle finished. Sleeping for 1 hour...")
                await asyncio.sleep(3600) # Sleep 1 hour
            except Exception as e:
                print(f"Optimization loop error: {e}")
                await asyncio.sleep(60) # Retry after 1 min on error

    def _load_dna(self):
        if os.path.exists(self.dna_file):
            try:
                with open(self.dna_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        # Default DNA
        return {
            "strategy_RSI": True,
            "strategy_MA": True,
            "strategy_BB": False,
            "rsi_window": 14,
            "rsi_buy": 30,
            "rsi_sell": 70,
            "ma_short": 20,
            "ma_long": 50,
            "bb_window": 20,
            "bb_dev": 2
        }

    def run_simulation(self, ticker="SPY", generations=10):
        """
        Runs a Genetic Algorithm to evolve the best trading parameters.
        Total evaluations = population_size * generations.
        To meet '100 upgrades', we can run 10 generations with pop=10, or 100 generations with pop=10.
        Let's do Population=20, Generations=5 -> 100 evaluations.
        Or for deep optimization: Population=10, Generations=10.
        """
        POPULATION_SIZE = 10
        GENERATIONS = generations # User requested 100 upgrades, we can treat each generation as an upgrade step if we keep best.
        
        print(f"Starting Genetic Optimization for {ticker} ({GENERATIONS} gens x {POPULATION_SIZE} pop)...")
        
        # 1. Load Data (cached)
        df = self.data_loader.get_stock_data(ticker, period="2y") # Use longer period for backtest
        if df.empty:
            print("No data for optimization")
            return

        # 2. Initialize Population
        population = [self._mutate(self.best_params) for _ in range(POPULATION_SIZE)]
        
        history = []

        for gen in range(GENERATIONS):
            # Evaluate Fitness
            scores = []
            for individual in population:
                score = self._backtest(df, individual)
                scores.append((score, individual))
            
            # Sort by score desc
            scores.sort(key=lambda x: x[0], reverse=True)
            
            # Record best of this generation
            gen_best_score, gen_best_params = scores[0]
            print(f"Gen {gen+1} Best: {gen_best_score:.2f}%")
            
            if gen_best_score > self.best_score:
                self.best_score = gen_best_score
                self.best_params = gen_best_params
                self._save_dna(self.best_params)
                print(f"  >>> NEW ALL-TIME BEST! Saved to disk.")

            history.append({
                "generation": gen,
                "best_score": gen_best_score,
                "best_params": gen_best_params
            })

            # Selection & Crossover (Elitism: keep top 2)
            new_population = [x[1] for x in scores[:2]] 
            
            while len(new_population) < POPULATION_SIZE:
                # Tournament Selection
                p1 = random.choice(scores[:5])[1]
                p2 = random.choice(scores[:5])[1]
                child = self._crossover(p1, p2)
                child = self._mutate(child)
                new_population.append(child)
            
            population = new_population

        self._save_history(history)
        print("Optimization Complete.")
        return self.best_params

    def _backtest(self, df, params):
        # Quick Vectorized Backtest or Loop
        # For complexity management, we use a loop but keep it simple
        capital = 10000.0
        position = 0.0 # shares
        
        # Pre-calculate indicators to speed up loop
        # We need to use Analyzer logic but efficient way
        # Actually Analyzer.analyze_stock is for single row. 
        # For backtest, we should pre-calc columns.
        
        df_test = df.copy()
        try:
            df_test['RSI'] = self.analyzer.calculate_rsi(df_test, int(params['rsi_window']))
            df_test['SMA_Short'] = self.analyzer.calculate_sma(df_test, int(params['ma_short']))
            df_test['SMA_Long'] = self.analyzer.calculate_sma(df_test, int(params['ma_long']))
            
            if params['strategy_BB']:
                u, l = self.analyzer.calculate_bollinger(df_test, int(params['bb_window']), int(params['bb_dev']))
                df_test['BB_Upper'] = u
                df_test['BB_Lower'] = l
        except:
            return -100 # Invalid params punishment

        # Logic
        # Buy if Score >= 1.5, Sell if Score <= -1.5
        # We simulate row by row
        
        for i in range(50, len(df_test)):
            row = df_test.iloc[i]
            prev = df_test.iloc[i-1]
            
            score = 0
            
            # RSI
            if params['strategy_RSI']:
                if row['RSI'] < params['rsi_buy']: score += 1
                elif row['RSI'] > params['rsi_sell']: score -= 1
                
            # MA
            if params['strategy_MA']:
                if prev['SMA_Short'] < prev['SMA_Long'] and row['SMA_Short'] > row['SMA_Long']: score += 2
                elif prev['SMA_Short'] > prev['SMA_Long'] and row['SMA_Short'] < row['SMA_Long']: score -= 2
            
            # BB
            if params['strategy_BB']:
                if row['Close'] < row['BB_Lower']: score += 1.5
                elif row['Close'] > row['BB_Upper']: score -= 1.5
                
            # Execute
            price = row['Close']
            if score >= 1.5 and position == 0:
                position = capital / price
                capital = 0
            elif score <= -1.5 and position > 0:
                capital = position * price
                position = 0
                
        final_value = capital + (position * df_test['Close'].iloc[-1] if position > 0 else 0)
        roi = ((final_value - 10000) / 10000) * 100
        return roi

    def _crossover(self, p1, p2):
        child = {}
        for k in p1.keys():
            child[k] = p1[k] if random.random() > 0.5 else p2[k]
        return child

    def _mutate(self, params):
        p = params.copy()
        if random.random() < 0.3: p['rsi_window'] = random.randint(5, 30)
        if random.random() < 0.3: p['rsi_buy'] = random.randint(10, 40)
        if random.random() < 0.3: p['rsi_sell'] = random.randint(60, 90)
        if random.random() < 0.3: p['ma_short'] = random.randint(5, 50)
        if random.random() < 0.3: p['ma_long'] = random.randint(50, 200)
        if random.random() < 0.3: p['strategy_BB'] = not p['strategy_BB']
        return p

    def _save_dna(self, params):
        with open(self.dna_file, 'w') as f:
            json.dump(params, f, indent=4)

    def _save_history(self, history):
        with open(self.history_file, 'w') as f:
            json.dump({
                "best_params": self.best_params,
                "best_score": self.best_score,
                "history": history
            }, f, indent=4)
