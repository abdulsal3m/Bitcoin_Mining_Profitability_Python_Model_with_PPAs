"""
Mining Calculator for Bitcoin Mining Dispatch Model
Handles all core mining economics calculations and profitability analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime
from config import Config

class MiningCalculator:
    """Handles core mining economics calculations"""
    
    def __init__(self):
        self.config = Config()
    
    def calculate_hashrate_from_facility(self, facility_size_mw, efficiency_w_per_th):
        """
        Calculate total hashrate based on facility size and miner efficiency
        
        Args:
            facility_size_mw (float): Facility size in MW
            efficiency_w_per_th (float): Miner efficiency in W/TH
            
        Returns:
            float: Total hashrate in TH/s
        """
        # Convert MW to W
        total_power_w = facility_size_mw * 1000000  # 1 MW = 1,000,000 W
        
        # Calculate total hashrate
        total_hashrate_th = total_power_w / efficiency_w_per_th
        
        return total_hashrate_th
    
    def calculate_hourly_revenue(self, hashrate_th, hashprice_per_th_day):
        """
        Calculate hourly mining revenue
        
        Args:
            hashrate_th (float): Hashrate in TH/s
            hashprice_per_th_day (float): Hashprice in $/TH/day
            
        Returns:
            float: Hourly revenue in USD
        """
        # Convert daily hashprice to hourly
        hourly_hashprice = hashprice_per_th_day / 24  # 24 hours in a day
        
        # Calculate revenue
        hourly_revenue = hashrate_th * hourly_hashprice
        
        return hourly_revenue
    
    def calculate_hourly_electricity_cost(self, facility_size_mw, electricity_price_per_mwh):
        """
        Calculate hourly electricity cost
        
        Args:
            facility_size_mw (float): Facility size in MW
            electricity_price_per_mwh (float): Electricity price in $/MWh
            
        Returns:
            float: Hourly electricity cost in USD
        """
        hourly_cost = facility_size_mw * electricity_price_per_mwh
        return hourly_cost
    
    def calculate_hourly_profit(self, revenue, electricity_cost):
        """
        Calculate hourly net profit
        
        Args:
            revenue (float): Hourly revenue in USD
            electricity_cost (float): Hourly electricity cost in USD
            
        Returns:
            float: Hourly net profit in USD
        """
        return revenue - electricity_cost
    
    def calculate_dispatch(self, data, facility_sizes_mw, efficiency_w_per_th, min_profit_threshold=0, fixed_price_contract=None):
        """
        Calculate dispatch decisions for all hours in the dataset, considering multiple load zones
        and fixed-price contracts.
        
        Args:
            data (pd.DataFrame): Merged electricity and hashprice data.
            facility_sizes_mw (dict): Dictionary of facility sizes per load zone (e.g., {"houston": 50}).
            efficiency_w_per_th (float): Miner efficiency in W/TH.
            min_profit_threshold (float): Minimum profit threshold to operate.
            fixed_price_contract (dict): Details of the fixed-price contract.
            
        Returns:
            pd.DataFrame: Data with dispatch decisions and profitability calculations.
        """
        print(f"Calculating dispatch for {len(data)} hours...")
        
        dispatch_data = data.copy()
        dispatch_data["hourly_revenue"] = 0.0
        dispatch_data["hourly_electricity_cost"] = 0.0
        dispatch_data["hourly_profit"] = 0.0
        dispatch_data["should_operate"] = False
        dispatch_data["actual_profit"] = 0.0
        dispatch_data["actual_revenue"] = 0.0
        dispatch_data["actual_electricity_cost"] = 0.0
        
        # Add facility parameters for reference (assuming first zone for overall hashrate)
        # This might need refinement for multi-zone total hashrate reporting
        total_hashrate_th_overall = 0
        for zone, size_mw in facility_sizes_mw.items():
            total_hashrate_th_overall += self.calculate_hashrate_from_facility(size_mw, efficiency_w_per_th)
        
        dispatch_data["efficiency_w_per_th"] = efficiency_w_per_th
        dispatch_data["hashrate_th"] = total_hashrate_th_overall

        # Apply calculations per load zone
        for zone in dispatch_data["load_zone"].unique():
            zone_data = dispatch_data[dispatch_data["load_zone"] == zone].copy()
            facility_size = facility_sizes_mw.get(zone, 0) # Get facility size for this zone
            zone_hashrate_th = self.calculate_hashrate_from_facility(facility_size, efficiency_w_per_th)

            # Calculate hourly revenue for this zone
            zone_data["hourly_revenue"] = zone_data["hashprice"].apply(
                lambda hp: self.calculate_hourly_revenue(zone_hashrate_th, hp)
            )

            # Calculate hourly electricity cost for this zone, considering fixed contract
            zone_data["hourly_electricity_cost"] = zone_data.apply(
                lambda row: self._get_electricity_cost(
                    row, facility_size, fixed_price_contract, zone
                ),
                axis=1
            )

            # Calculate hourly profit for this zone
            zone_data["hourly_profit"] = zone_data.apply(
                lambda row: self.calculate_hourly_profit(row["hourly_revenue"], row["hourly_electricity_cost"]),
                axis=1
            )

            # Make dispatch decisions for this zone
            zone_data["should_operate"] = zone_data["hourly_profit"] > min_profit_threshold

            # Calculate actual profit, revenue, and cost for this zone
            zone_data["actual_profit"] = zone_data.apply(
                lambda row: row["hourly_profit"] if row["should_operate"] else 0,
                axis=1
            )
            zone_data["actual_revenue"] = zone_data.apply(
                lambda row: row["hourly_revenue"] if row["should_operate"] else 0,
                axis=1
            )
            zone_data["actual_electricity_cost"] = zone_data.apply(
                lambda row: row["hourly_electricity_cost"] if row["should_operate"] else 0,
                axis=1
            )
            zone_data["facility_size_mw"] = facility_size # Add facility size for this zone

            # Update the main dispatch_data with calculated values for this zone
            dispatch_data.loc[zone_data.index, ["hourly_revenue", "hourly_electricity_cost", 
                                                "hourly_profit", "should_operate", 
                                                "actual_profit", "actual_revenue", 
                                                "actual_electricity_cost", "facility_size_mw"]] = zone_data[["hourly_revenue", "hourly_electricity_cost", 
                                                                                                        "hourly_profit", "should_operate", 
                                                                                                        "actual_profit", "actual_revenue", 
                                                                                                        "actual_electricity_cost", "facility_size_mw"]]

        print(f"Dispatch calculation completed")
        print(f'Operating hours: {dispatch_data["should_operate"].sum():,}')
        print(f"Total hours: {len(dispatch_data):,}")
        print(f'Capacity factor: {dispatch_data["should_operate"].mean():.2%}')
        
        return dispatch_data
    
    def _get_electricity_cost(self, row, facility_size_mw, fixed_price_contract, current_zone):
        """
        Determine the electricity cost for a given hour, considering fixed-price contracts.
        """
        electricity_price = row["electricity_price"]
        hour = row.name.hour # Get hour from datetime index
        day_of_week = row.name.dayofweek + 1 # Monday=1, Sunday=7

        if fixed_price_contract and fixed_price_contract["has_contract"] and fixed_price_contract["zone"] == current_zone:
            contract_block = fixed_price_contract["block"]
            contract_rate = fixed_price_contract["rate_per_mwh"]
            contract_size = fixed_price_contract["size_mwh"]

            is_contract_hour = False
            if contract_block == "7x24":
                is_contract_hour = True
            elif contract_block == "5x16": # Weekday 6am-10pm
                if 1 <= day_of_week <= 5 and 6 <= hour < 22:
                    is_contract_hour = True
            elif contract_block == "2x16": # Weekends 6am-10pm
                if 6 <= day_of_week <= 7 and 6 <= hour < 22:
                    is_contract_hour = True
            elif contract_block == "7x8": # All week 10pm-6am
                if 22 <= hour or hour < 6:
                    is_contract_hour = True
            
            if is_contract_hour:
                # If contract size is less than facility size, blend prices
                if contract_size < facility_size_mw:
                    contracted_cost = contract_size * contract_rate
                    real_time_cost = (facility_size_mw - contract_size) * electricity_price
                    return contracted_cost + real_time_cost
                else: # Contract size is equal to or greater than facility size (capped at facility size)
                    return facility_size_mw * contract_rate
            
        # If no contract or not a contract hour, use real-time price
        return facility_size_mw * electricity_price

    def generate_summary(self, dispatch_data):
        """
        Generate summary statistics from dispatch results
        
        Args:
            dispatch_data (pd.DataFrame): Results from calculate_dispatch
            
        Returns:
            dict: Summary statistics
        """
        print("Generating summary statistics...")
        
        # Basic metrics
        total_hours = len(dispatch_data)
        operating_hours = dispatch_data["should_operate"].sum()
        capacity_factor = operating_hours / total_hours if total_hours > 0 else 0
        
        # Financial metrics
        total_revenue = dispatch_data["actual_revenue"].sum()
        total_electricity_cost = dispatch_data["actual_electricity_cost"].sum()
        total_profit = dispatch_data["actual_profit"].sum()
        
        # Average metrics (only for operating hours)
        operating_data = dispatch_data[dispatch_data["should_operate"]]
        avg_profit_per_hour = operating_data["hourly_profit"].mean() if len(operating_data) > 0 else 0
        avg_electricity_price = dispatch_data["electricity_price"].mean()
        avg_hashprice = dispatch_data["hashprice"].mean()
        
        # Monthly analysis
        dispatch_data["month"] = dispatch_data.index.month
        monthly_profits = dispatch_data.groupby("month")["actual_profit"].sum()
        best_month = monthly_profits.idxmax() if len(monthly_profits) > 0 else None
        worst_month = monthly_profits.idxmin() if len(monthly_profits) > 0 else None
        
        # Profitability analysis
        profitable_hours = (dispatch_data["hourly_profit"] > 0).sum()
        unprofitable_hours = (dispatch_data["hourly_profit"] <= 0).sum()
        
        summary = {
            "total_hours": total_hours,
            "operating_hours": operating_hours,
            "capacity_factor": capacity_factor,
            "total_revenue": total_revenue,
            "total_electricity_cost": total_electricity_cost,
            "total_profit": total_profit,
            "avg_profit_per_hour": avg_profit_per_hour,
            "avg_electricity_price": avg_electricity_price,
            "avg_hashprice": avg_hashprice,
            "best_month": best_month,
            "worst_month": worst_month,
            "profitable_hours": profitable_hours,
            "unprofitable_hours": unprofitable_hours,
            "facility_size_mw": dispatch_data["facility_size_mw"].iloc[0] if len(dispatch_data) > 0 else 0,
            "efficiency_w_per_th": dispatch_data["efficiency_w_per_th"].iloc[0] if len(dispatch_data) > 0 else 0,
            "hashrate_th": dispatch_data["hashrate_th"].iloc[0] if len(dispatch_data) > 0 else 0
        }
        
        return summary
    
    def calculate_roi_metrics(self, dispatch_data, initial_investment=None):
        """
        Calculate return on investment metrics if initial investment is provided
        
        Args:
            dispatch_data (pd.DataFrame): Results from calculate_dispatch
            initial_investment (float): Initial investment in USD
            
        Returns:
            dict: ROI metrics
        """
        if initial_investment is None or initial_investment <= 0:
            return {}
        
        total_profit = dispatch_data["actual_profit"].sum()
        
        # Calculate time period
        time_period_days = (dispatch_data.index.max() - dispatch_data.index.min()).days
        time_period_years = time_period_days / 365.25
        
        # ROI calculations
        roi_percentage = (total_profit / initial_investment) * 100
        annualized_roi = (roi_percentage / time_period_years) if time_period_years > 0 else 0
        payback_period_years = (initial_investment / (total_profit / time_period_years)) if total_profit > 0 else float("inf")
        
        return {
            "initial_investment": initial_investment,
            "roi_percentage": roi_percentage,
            "annualized_roi": annualized_roi,
            "payback_period_years": payback_period_years,
            "time_period_years": time_period_years
        }

