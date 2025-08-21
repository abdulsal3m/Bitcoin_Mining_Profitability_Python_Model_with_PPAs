"""
Utility functions for Bitcoin Mining Dispatch Model
Contains helper functions for data validation, conversions, and common operations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re

def validate_date_string(date_string):
    """
    Validate and parse date string
    
    Args:
        date_string (str): Date in YYYY-MM-DD format
        
    Returns:
        datetime: Parsed datetime object
        
    Raises:
        ValueError: If date format is invalid
    """
    try:
        return datetime.strptime(date_string, '%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Invalid date format: {date_string}. Expected YYYY-MM-DD")

def validate_positive_number(value, name):
    """
    Validate that a number is positive
    
    Args:
        value (float): Value to validate
        name (str): Name of the parameter for error messages
        
    Returns:
        float: Validated value
        
    Raises:
        ValueError: If value is not positive
    """
    if not isinstance(value, (int, float)) or value <= 0:
        raise ValueError(f"{name} must be a positive number, got: {value}")
    return float(value)

def validate_date_range(start_date, end_date):
    """
    Validate that date range is logical
    
    Args:
        start_date (str or datetime): Start date
        end_date (str or datetime): End date
        
    Returns:
        tuple: (start_datetime, end_datetime)
        
    Raises:
        ValueError: If date range is invalid
    """
    if isinstance(start_date, str):
        start_dt = validate_date_string(start_date)
    else:
        start_dt = start_date
    
    if isinstance(end_date, str):
        end_dt = validate_date_string(end_date)
    else:
        end_dt = end_date
    
    if start_dt >= end_dt:
        raise ValueError(f"Start date ({start_dt}) must be before end date ({end_dt})")
    
    # Check if date range is reasonable (not too long)
    days_diff = (end_dt - start_dt).days
    if days_diff > 365 * 2:  # More than 2 years
        print(f"Warning: Date range is {days_diff} days ({days_diff/365:.1f} years). This may take a while to process.")
    
    return start_dt, end_dt

def convert_mw_to_kw(mw):
    """Convert MW to kW"""
    return mw * 1000

def convert_kw_to_mw(kw):
    """Convert kW to MW"""
    return kw / 1000

def convert_th_to_ph(th):
    """Convert TH/s to PH/s"""
    return th / 1000000

def convert_ph_to_th(ph):
    """Convert PH/s to TH/s"""
    return ph * 1000000

def convert_daily_to_hourly(daily_value):
    """Convert daily value to hourly"""
    return daily_value / 24

def convert_hourly_to_daily(hourly_value):
    """Convert hourly value to daily"""
    return hourly_value * 24

def format_currency(amount, decimals=2):
    """
    Format number as currency string
    
    Args:
        amount (float): Amount to format
        decimals (int): Number of decimal places
        
    Returns:
        str: Formatted currency string
    """
    return f"${amount:,.{decimals}f}"

def format_percentage(value, decimals=2):
    """
    Format number as percentage string
    
    Args:
        value (float): Value to format (0.1 = 10%)
        decimals (int): Number of decimal places
        
    Returns:
        str: Formatted percentage string
    """
    return f"{value * 100:.{decimals}f}%"

def format_large_number(number, decimals=1):
    """
    Format large numbers with appropriate suffixes (K, M, B)
    
    Args:
        number (float): Number to format
        decimals (int): Number of decimal places
        
    Returns:
        str: Formatted number string
    """
    if abs(number) >= 1e9:
        return f"{number / 1e9:.{decimals}f}B"
    elif abs(number) >= 1e6:
        return f"{number / 1e6:.{decimals}f}M"
    elif abs(number) >= 1e3:
        return f"{number / 1e3:.{decimals}f}K"
    else:
        return f"{number:.{decimals}f}"

def calculate_capacity_factor(operating_hours, total_hours):
    """
    Calculate capacity factor
    
    Args:
        operating_hours (int): Number of operating hours
        total_hours (int): Total available hours
        
    Returns:
        float: Capacity factor (0-1)
    """
    if total_hours <= 0:
        return 0
    return operating_hours / total_hours

def calculate_simple_roi(profit, investment):
    """
    Calculate simple return on investment
    
    Args:
        profit (float): Total profit
        investment (float): Initial investment
        
    Returns:
        float: ROI as decimal (0.1 = 10%)
    """
    if investment <= 0:
        return 0
    return profit / investment

def resample_data_to_hourly(data, datetime_col='datetime', method='mean'):
    """
    Resample data to hourly frequency
    
    Args:
        data (pd.DataFrame): Input data
        datetime_col (str): Name of datetime column
        method (str): Resampling method ('mean', 'sum', 'first', 'last')
        
    Returns:
        pd.DataFrame: Resampled data
    """
    if datetime_col not in data.columns:
        raise ValueError(f"Datetime column '{datetime_col}' not found in data")
    
    # Set datetime as index if it isn't already
    if data.index.name != datetime_col:
        data = data.set_index(datetime_col)
    
    # Ensure datetime index
    if not isinstance(data.index, pd.DatetimeIndex):
        data.index = pd.to_datetime(data.index)
    
    # Resample based on method
    if method == 'mean':
        return data.resample('1H').mean()
    elif method == 'sum':
        return data.resample('1H').sum()
    elif method == 'first':
        return data.resample('1H').first()
    elif method == 'last':
        return data.resample('1H').last()
    else:
        raise ValueError(f"Unknown resampling method: {method}")

def detect_data_frequency(data):
    """
    Detect the frequency of time series data
    
    Args:
        data (pd.DataFrame): Data with datetime index
        
    Returns:
        str: Detected frequency ('15min', '30min', '1H', 'D', etc.)
    """
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError("Data must have a datetime index")
    
    if len(data) < 2:
        return "Unknown"
    
    # Calculate time differences
    time_diffs = data.index[1:] - data.index[:-1]
    most_common_diff = time_diffs.mode()[0] if len(time_diffs.mode()) > 0 else time_diffs[0]
    
    # Convert to frequency string
    if most_common_diff == timedelta(minutes=15):
        return "15min"
    elif most_common_diff == timedelta(minutes=30):
        return "30min"
    elif most_common_diff == timedelta(hours=1):
        return "1H"
    elif most_common_diff == timedelta(days=1):
        return "D"
    else:
        return f"{most_common_diff}"

def clean_column_names(df):
    """
    Clean and standardize DataFrame column names
    
    Args:
        df (pd.DataFrame): DataFrame with potentially messy column names
        
    Returns:
        pd.DataFrame: DataFrame with cleaned column names
    """
    df = df.copy()
    
    # Convert to lowercase and strip whitespace
    df.columns = df.columns.str.lower().str.strip()
    
    # Replace spaces and special characters with underscores
    df.columns = df.columns.str.replace(r'[^\w]', '_', regex=True)
    
    # Remove multiple consecutive underscores
    df.columns = df.columns.str.replace(r'_+', '_', regex=True)
    
    # Remove leading/trailing underscores
    df.columns = df.columns.str.strip('_')
    
    return df

def find_column_by_keywords(df, keywords, case_sensitive=False):
    """
    Find column that contains any of the specified keywords
    
    Args:
        df (pd.DataFrame): DataFrame to search
        keywords (list): List of keywords to search for
        case_sensitive (bool): Whether search should be case sensitive
        
    Returns:
        str or None: Name of matching column, or None if not found
    """
    columns = df.columns if case_sensitive else df.columns.str.lower()
    keywords = keywords if case_sensitive else [kw.lower() for kw in keywords]
    
    for col in columns:
        if any(keyword in col for keyword in keywords):
            return df.columns[columns.get_loc(col)]
    
    return None

def calculate_rolling_statistics(series, window=24):
    """
    Calculate rolling statistics for a time series
    
    Args:
        series (pd.Series): Time series data
        window (int): Rolling window size
        
    Returns:
        dict: Dictionary with rolling statistics
    """
    return {
        'rolling_mean': series.rolling(window=window).mean(),
        'rolling_std': series.rolling(window=window).std(),
        'rolling_min': series.rolling(window=window).min(),
        'rolling_max': series.rolling(window=window).max(),
        'rolling_median': series.rolling(window=window).median()
    }

def identify_outliers(series, method='iqr', threshold=1.5):
    """
    Identify outliers in a time series
    
    Args:
        series (pd.Series): Time series data
        method (str): Method to use ('iqr' or 'zscore')
        threshold (float): Threshold for outlier detection
        
    Returns:
        pd.Series: Boolean series indicating outliers
    """
    if method == 'iqr':
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR
        return (series < lower_bound) | (series > upper_bound)
    
    elif method == 'zscore':
        z_scores = np.abs((series - series.mean()) / series.std())
        return z_scores > threshold
    
    else:
        raise ValueError(f"Unknown outlier detection method: {method}")

def safe_divide(numerator, denominator, default=0):
    """
    Safely divide two numbers, returning default if denominator is zero
    
    Args:
        numerator (float): Numerator
        denominator (float): Denominator
        default (float): Default value if division by zero
        
    Returns:
        float: Result of division or default value
    """
    if denominator == 0:
        return default
    return numerator / denominator

