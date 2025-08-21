"""
Visualizer for Bitcoin Mining Dispatch Model
Handles all data visualization and chart generation
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os
from config import Config

class Visualizer:
    """Handles data visualization and chart generation"""
    
    def __init__(self):
        self.config = Config()
        self.colors = self.config.VISUALIZATION_CONFIG["colors"]
        
        # Set matplotlib style
        plt.style.use(self.config.VISUALIZATION_CONFIG["chart_style"])
        
        # Create output directory
        os.makedirs(self.config.DATA_CONFIG["output_directory"], exist_ok=True)
    
    def create_dispatch_chart(self, dispatch_data, save_path=None):
        """
        Create a chart showing dispatch decisions over time
        
        Args:
            dispatch_data (pd.DataFrame): Data with dispatch decisions
            save_path (str): Path to save the chart
        """
        if save_path is None:
            save_path = os.path.join(self.config.DATA_CONFIG["output_directory"], "dispatch_schedule.png")
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.config.VISUALIZATION_CONFIG["figure_size"], 
                                       dpi=self.config.VISUALIZATION_CONFIG["dpi"])
        
        # Top plot: Dispatch decisions
        dispatch_binary = dispatch_data["should_operate"].astype(int)
        ax1.fill_between(dispatch_data.index, 0, dispatch_binary, 
                        color=self.colors["profit"], alpha=0.7, label="Operating")
        ax1.fill_between(dispatch_data.index, dispatch_binary, 1, 
                        color=self.colors["loss"], alpha=0.3, label="Offline")
        
        ax1.set_ylabel("Operating Status")
        ax1.set_title("Bitcoin Mining Dispatch Schedule")
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 1)
        
        # Bottom plot: Hourly profit
        colors = [self.colors["profit"] if profit > 0 else self.colors["loss"] 
                 for profit in dispatch_data["hourly_profit"]]
        
        ax2.bar(dispatch_data.index, dispatch_data["hourly_profit"], 
               color=colors, alpha=0.7, width=pd.Timedelta(hours=0.8))
        ax2.axhline(y=0, color="black", linestyle="-", alpha=0.5)
        ax2.set_ylabel("Hourly Profit ($)")
        ax2.set_xlabel("Date")
        ax2.set_title("Hourly Profitability")
        ax2.grid(True, alpha=0.3)
        
        # Format x-axis
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dispatch_data) // 10)))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        plt.savefig(save_path, bbox_inches="tight")
        plt.close()
        
        print(f"Dispatch chart saved to: {save_path}")
    
    def create_profitability_chart(self, dispatch_data, save_path=None):
        """
        Create a chart showing profitability analysis
        
        Args:
            dispatch_data (pd.DataFrame): Data with profitability calculations
            save_path (str): Path to save the chart
        """
        if save_path is None:
            save_path = os.path.join(self.config.DATA_CONFIG["output_directory"], "profitability_analysis.png")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12), 
                                                     dpi=self.config.VISUALIZATION_CONFIG["dpi"])
        
        # 1. Cumulative profit over time
        cumulative_profit = dispatch_data["actual_profit"].cumsum()
        ax1.plot(dispatch_data.index, cumulative_profit, color=self.colors["profit"], linewidth=2)
        ax1.set_title("Cumulative Profit Over Time")
        ax1.set_ylabel("Cumulative Profit ($)")
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # 2. Daily profit distribution
        daily_profits = dispatch_data["actual_profit"].resample("D").sum()
        ax2.hist(daily_profits, bins=30, color=self.colors["neutral"], alpha=0.7, edgecolor="black")
        ax2.axvline(daily_profits.mean(), color=self.colors["profit"], linestyle="--", 
                   label=f"Mean: ${daily_profits.mean():.2f}")
        ax2.set_title("Daily Profit Distribution")
        ax2.set_xlabel("Daily Profit ($)")
        ax2.set_ylabel("Frequency")
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Monthly profitability
        monthly_profits = dispatch_data["actual_profit"].resample("M").sum()
        bars = ax3.bar(range(len(monthly_profits)), monthly_profits.values, 
                      color=self.colors["profit"], alpha=0.7)
        ax3.set_title("Monthly Profitability")
        ax3.set_xlabel("Month")
        ax3.set_ylabel("Monthly Profit ($)")
        ax3.set_xticks(range(len(monthly_profits)))
        ax3.set_xticklabels([date.strftime("%Y-%m") for date in monthly_profits.index], rotation=45)
        ax3.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, value in zip(bars, monthly_profits.values):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f"${value:,.0f}", ha="center", va="bottom")
        
        # 4. Capacity factor by hour of day
        hourly_capacity = dispatch_data.groupby(dispatch_data.index.hour)["should_operate"].mean()
        ax4.bar(hourly_capacity.index, hourly_capacity.values, 
               color=self.colors["neutral"], alpha=0.7)
        ax4.set_title("Capacity Factor by Hour of Day")
        ax4.set_xlabel("Hour of Day")
        ax4.set_ylabel("Capacity Factor")
        ax4.set_xticks(range(0, 24, 2))
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, bbox_inches="tight")
        plt.close()
        
        print(f"Profitability chart saved to: {save_path}")
    
    def create_price_comparison_chart(self, dispatch_data, save_path=None):
        """
        Create a chart comparing electricity prices and hashprices
        
        Args:
            dispatch_data (pd.DataFrame): Data with price information
            save_path (str): Path to save the chart
        """
        if save_path is None:
            save_path = os.path.join(self.config.DATA_CONFIG["output_directory"], "price_comparison.png")
        
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12), 
                                           dpi=self.config.VISUALIZATION_CONFIG["dpi"])
        
        # 1. Electricity prices over time
        ax1.plot(dispatch_data.index, dispatch_data["electricity_price"], 
                color=self.colors["electricity"], linewidth=1.5, label="Electricity Price")
        ax1.set_title("Electricity Prices Over Time")
        ax1.set_ylabel("Price ($/MWh)")
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Hashprices over time
        ax2.plot(dispatch_data.index, dispatch_data["hashprice"], 
                color=self.colors["hashprice"], linewidth=1.5, label="Hashprice")
        ax2.set_title("Hashprices Over Time")
        ax2.set_ylabel("Hashprice ($/TH/day)")
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Price correlation scatter plot
        ax3.scatter(dispatch_data["electricity_price"], dispatch_data["hashprice"], 
                   alpha=0.6, color=self.colors["neutral"], s=20)
        ax3.set_xlabel("Electricity Price ($/MWh)")
        ax3.set_ylabel("Hashprice ($/TH/day)")
        ax3.set_title("Electricity Price vs Hashprice Correlation")
        ax3.grid(True, alpha=0.3)
        
        # Add correlation coefficient
        correlation = dispatch_data["electricity_price"].corr(dispatch_data["hashprice"])
        ax3.text(0.05, 0.95, f"Correlation: {correlation:.3f}", 
                transform=ax3.transAxes, bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))
        
        # Format x-axis for time series plots
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dispatch_data) // 10)))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        plt.savefig(save_path, bbox_inches="tight")
        plt.close()
        
        print(f"Price comparison chart saved to: {save_path}")
    
    def create_summary_dashboard(self, dispatch_data, summary_stats, save_path=None):
        """
        Create a comprehensive summary dashboard
        
        Args:
            dispatch_data (pd.DataFrame): Data with all calculations
            summary_stats (dict): Summary statistics
            save_path (str): Path to save the chart
        """
        if save_path is None:
            save_path = os.path.join(self.config.DATA_CONFIG["output_directory"], "summary_dashboard.png")
        
        fig = plt.figure(figsize=(20, 16), dpi=self.config.VISUALIZATION_CONFIG["dpi"])
        
        # Create a grid layout
        gs = fig.add_gridspec(4, 4, hspace=0.3, wspace=0.3)
        
        # 1. Key metrics text box
        ax1 = fig.add_subplot(gs[0, :2])
        ax1.axis("off")
        
        # 2. Cumulative profit
        ax2 = fig.add_subplot(gs[0, 2:])
        cumulative_profit = dispatch_data["actual_profit"].cumsum()
        ax2.plot(dispatch_data.index, cumulative_profit, color=self.colors["profit"], linewidth=2)
        ax2.set_title("Cumulative Profit")
        ax2.set_ylabel("Profit ($)")
        ax2.grid(True, alpha=0.3)
        
        # 3. Dispatch schedule
        ax3 = fig.add_subplot(gs[1, :])
        dispatch_binary = dispatch_data["should_operate"].astype(int)
        ax3.fill_between(dispatch_data.index, 0, dispatch_binary, 
                        color=self.colors["profit"], alpha=0.7)
        ax3.set_title("Dispatch Schedule (Green = Operating)")
        ax3.set_ylabel("Status")
        ax3.grid(True, alpha=0.3)
        
        # 4. Price trends
        ax4 = fig.add_subplot(gs[2, :2])
        ax4_twin = ax4.twinx()
        
        line1 = ax4.plot(dispatch_data.index, dispatch_data["electricity_price"], 
                        color=self.colors["electricity"], label="Electricity Price")
        line2 = ax4_twin.plot(dispatch_data.index, dispatch_data["hashprice"], 
                             color=self.colors["hashprice"], label="Hashprice")
        
        ax4.set_ylabel("Electricity Price ($/MWh)", color=self.colors["electricity"])
        ax4_twin.set_ylabel("Hashprice ($/TH/day)", color=self.colors["hashprice"])
        ax4.set_title("Price Trends")
        ax4.grid(True, alpha=0.3)
        
        # 5. Hourly capacity factor
        ax5 = fig.add_subplot(gs[2, 2:])
        hourly_capacity = dispatch_data.groupby(dispatch_data.index.hour)["should_operate"].mean()
        ax5.bar(hourly_capacity.index, hourly_capacity.values, color=self.colors["neutral"], alpha=0.7)
        ax5.set_title("Capacity Factor by Hour")
        ax5.set_xlabel("Hour of Day")
        ax5.set_ylabel("Capacity Factor")
        
        # 6. Monthly profits
        ax6 = fig.add_subplot(gs[3, :2])
        monthly_profits = dispatch_data["actual_profit"].resample("M").sum()
        ax6.bar(range(len(monthly_profits)), monthly_profits.values, color=self.colors["profit"], alpha=0.7)
        ax6.set_title("Monthly Profits")
        ax6.set_xlabel("Month")
        ax6.set_ylabel("Profit ($)")
        if len(monthly_profits) > 0:
            ax6.set_xticks(range(len(monthly_profits)))
            ax6.set_xticklabels([date.strftime("%Y-%m") for date in monthly_profits.index], rotation=45)
        
        # 7. Profit distribution
        ax7 = fig.add_subplot(gs[3, 2:])
        daily_profits = dispatch_data["actual_profit"].resample("D").sum()
        ax7.hist(daily_profits, bins=20, color=self.colors["neutral"], alpha=0.7, edgecolor="black")
        ax7.axvline(daily_profits.mean(), color=self.colors["profit"], linestyle="--", 
                   label=f"Mean: ${daily_profits.mean():.2f}")
        ax7.set_title("Daily Profit Distribution")
        ax7.set_xlabel("Daily Profit ($)")
        ax7.set_ylabel("Frequency")
        ax7.legend()
        
        plt.savefig(save_path, bbox_inches="tight")
        plt.close()
        
        print(f"Summary dashboard saved to: {save_path}")
    
    def create_all_charts(self, dispatch_data, summary_stats):
        """
        Create all visualization charts
        
        Args:
            dispatch_data (pd.DataFrame): Data with all calculations
            summary_stats (dict): Summary statistics
        """
        print("Creating all visualization charts...")
        
        self.create_dispatch_chart(dispatch_data)
        self.create_profitability_chart(dispatch_data)
        self.create_price_comparison_chart(dispatch_data)
        self.create_summary_dashboard(dispatch_data, summary_stats)
        
        print("All charts created successfully!")

