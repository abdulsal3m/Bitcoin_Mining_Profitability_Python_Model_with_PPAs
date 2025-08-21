"""
Dispatch Optimizer for Bitcoin Mining Dispatch Model
Handles dispatch logic, optimization algorithms, and backtesting
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config import Config

class DispatchOptimizer:
    """Handles dispatch optimization and backtesting logic"""
    
    def __init__(self):
        self.config = Config()
    
    def simple_threshold_dispatch(self, data, min_profit_threshold=0):
        """
        Simple threshold-based dispatch strategy
        
        Args:
            data (pd.DataFrame): Data with hourly_profit column
            min_profit_threshold (float): Minimum profit to operate
            
        Returns:
            pd.Series: Boolean series indicating when to operate
        """
        return data['hourly_profit'] > min_profit_threshold
    
    def percentile_based_dispatch(self, data, percentile_threshold=50):
        """
        Dispatch based on profit percentile (operate during top X% of profitable hours)
        
        Args:
            data (pd.DataFrame): Data with hourly_profit column
            percentile_threshold (float): Percentile threshold (0-100)
            
        Returns:
            pd.Series: Boolean series indicating when to operate
        """
        profit_threshold = np.percentile(data['hourly_profit'], percentile_threshold)
        return data['hourly_profit'] > profit_threshold
    
    def rolling_average_dispatch(self, data, window_hours=24, threshold_multiplier=1.0):
        """
        Dispatch based on rolling average profitability
        
        Args:
            data (pd.DataFrame): Data with hourly_profit column
            window_hours (int): Rolling window size in hours
            threshold_multiplier (float): Multiplier for rolling average threshold
            
        Returns:
            pd.Series: Boolean series indicating when to operate
        """
        rolling_avg = data['hourly_profit'].rolling(window=window_hours, center=True).mean()
        threshold = rolling_avg * threshold_multiplier
        return data['hourly_profit'] > threshold
    
    def peak_hours_dispatch(self, data, avoid_peak_hours=True, peak_hours=None):
        """
        Dispatch strategy that considers peak/off-peak hours
        
        Args:
            data (pd.DataFrame): Data with datetime index
            avoid_peak_hours (bool): Whether to avoid operating during peak hours
            peak_hours (list): List of peak hour integers (0-23)
            
        Returns:
            pd.Series: Boolean series indicating when to operate
        """
        if peak_hours is None:
            peak_hours = self.config.ERCOT_CONFIG['peak_hours']
        
        # Basic profitability check
        profitable = data['hourly_profit'] > 0
        
        if avoid_peak_hours:
            # Avoid peak hours unless highly profitable
            is_peak = data.index.hour.isin(peak_hours)
            peak_threshold = data['hourly_profit'].quantile(0.75)  # Top 25% profits
            
            # Operate if: (profitable and not peak) OR (highly profitable and peak)
            dispatch = (profitable & ~is_peak) | (data['hourly_profit'] > peak_threshold)
        else:
            # Simple profitability-based dispatch
            dispatch = profitable
        
        return dispatch
    
    def optimize_dispatch_strategy(self, data, strategies=None):
        """
        Test multiple dispatch strategies and return the best one
        
        Args:
            data (pd.DataFrame): Data with profitability calculations
            strategies (list): List of strategy functions to test
            
        Returns:
            dict: Results from the best strategy
        """
        if strategies is None:
            strategies = [
                ('Simple Threshold', lambda d: self.simple_threshold_dispatch(d, 0)),
                ('Percentile 60%', lambda d: self.percentile_based_dispatch(d, 60)),
                ('Percentile 70%', lambda d: self.percentile_based_dispatch(d, 70)),
                ('Rolling Average', lambda d: self.rolling_average_dispatch(d, 24, 1.1)),
                ('Avoid Peak Hours', lambda d: self.peak_hours_dispatch(d, True))
            ]
        
        results = []
        
        for strategy_name, strategy_func in strategies:
            # Apply strategy
            dispatch_decisions = strategy_func(data)
            
            # Calculate performance
            performance = self.evaluate_dispatch_performance(data, dispatch_decisions)
            performance['strategy_name'] = strategy_name
            
            results.append(performance)
        
        # Find best strategy (highest total profit)
        best_strategy = max(results, key=lambda x: x['total_profit'])
        
        return {
            'best_strategy': best_strategy,
            'all_results': results
        }
    
    def evaluate_dispatch_performance(self, data, dispatch_decisions):
        """
        Evaluate the performance of a dispatch strategy
        
        Args:
            data (pd.DataFrame): Data with profitability calculations
            dispatch_decisions (pd.Series): Boolean series of dispatch decisions
            
        Returns:
            dict: Performance metrics
        """
        # Apply dispatch decisions
        actual_profit = data['hourly_profit'] * dispatch_decisions
        actual_revenue = data['hourly_revenue'] * dispatch_decisions
        actual_cost = data['hourly_electricity_cost'] * dispatch_decisions
        
        # Calculate metrics
        total_profit = actual_profit.sum()
        total_revenue = actual_revenue.sum()
        total_cost = actual_cost.sum()
        operating_hours = dispatch_decisions.sum()
        total_hours = len(data)
        capacity_factor = operating_hours / total_hours if total_hours > 0 else 0
        
        # Efficiency metrics
        avg_profit_per_operating_hour = actual_profit[dispatch_decisions].mean() if operating_hours > 0 else 0
        profit_margin = (total_profit / total_revenue) if total_revenue > 0 else 0
        
        return {
            'total_profit': total_profit,
            'total_revenue': total_revenue,
            'total_cost': total_cost,
            'operating_hours': operating_hours,
            'total_hours': total_hours,
            'capacity_factor': capacity_factor,
            'avg_profit_per_operating_hour': avg_profit_per_operating_hour,
            'profit_margin': profit_margin
        }
    
    def backtest_strategy(self, data, strategy_func, start_date=None, end_date=None):
        """
        Backtest a dispatch strategy over a specific period
        
        Args:
            data (pd.DataFrame): Historical data
            strategy_func (callable): Strategy function
            start_date (str): Start date for backtest
            end_date (str): End date for backtest
            
        Returns:
            dict: Backtest results
        """
        # Filter data if dates provided
        if start_date or end_date:
            if start_date:
                data = data[data.index >= pd.to_datetime(start_date)]
            if end_date:
                data = data[data.index <= pd.to_datetime(end_date)]
        
        if len(data) == 0:
            raise ValueError("No data available for the specified date range")
        
        # Apply strategy
        dispatch_decisions = strategy_func(data)
        
        # Evaluate performance
        performance = self.evaluate_dispatch_performance(data, dispatch_decisions)
        
        # Add backtest-specific metrics
        performance.update({
            'backtest_start': data.index.min(),
            'backtest_end': data.index.max(),
            'backtest_days': (data.index.max() - data.index.min()).days,
            'data_points': len(data)
        })
        
        return performance
    
    def rolling_backtest(self, data, strategy_func, window_days=30, step_days=7):
        """
        Perform rolling backtests to assess strategy stability
        
        Args:
            data (pd.DataFrame): Historical data
            strategy_func (callable): Strategy function
            window_days (int): Size of each backtest window
            step_days (int): Step size between backtests
            
        Returns:
            pd.DataFrame: Rolling backtest results
        """
        results = []
        
        start_date = data.index.min()
        end_date = data.index.max()
        
        current_start = start_date
        
        while current_start + timedelta(days=window_days) <= end_date:
            current_end = current_start + timedelta(days=window_days)
            
            # Extract window data
            window_data = data[(data.index >= current_start) & (data.index < current_end)]
            
            if len(window_data) > 0:
                # Run backtest
                try:
                    performance = self.backtest_strategy(window_data, strategy_func)
                    performance['window_start'] = current_start
                    performance['window_end'] = current_end
                    results.append(performance)
                except Exception as e:
                    print(f"Error in rolling backtest for window {current_start} to {current_end}: {e}")
            
            # Move to next window
            current_start += timedelta(days=step_days)
        
        return pd.DataFrame(results)
    
    def calculate_risk_metrics(self, data, dispatch_decisions):
        """
        Calculate risk metrics for a dispatch strategy
        
        Args:
            data (pd.DataFrame): Data with profitability calculations
            dispatch_decisions (pd.Series): Boolean series of dispatch decisions
            
        Returns:
            dict: Risk metrics
        """
        # Daily profit series
        daily_profits = (data['hourly_profit'] * dispatch_decisions).resample('D').sum()
        
        # Risk metrics
        profit_volatility = daily_profits.std()
        max_daily_loss = daily_profits.min()
        max_daily_gain = daily_profits.max()
        
        # Value at Risk (95% confidence)
        var_95 = daily_profits.quantile(0.05)
        
        # Sharpe-like ratio (profit/volatility)
        avg_daily_profit = daily_profits.mean()
        risk_adjusted_return = avg_daily_profit / profit_volatility if profit_volatility > 0 else 0
        
        # Downside metrics
        negative_days = (daily_profits < 0).sum()
        total_days = len(daily_profits)
        downside_probability = negative_days / total_days if total_days > 0 else 0
        
        return {
            'profit_volatility': profit_volatility,
            'max_daily_loss': max_daily_loss,
            'max_daily_gain': max_daily_gain,
            'var_95': var_95,
            'risk_adjusted_return': risk_adjusted_return,
            'downside_probability': downside_probability,
            'negative_days': negative_days,
            'total_days': total_days
        }

