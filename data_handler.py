"""
Data Handler for Bitcoin Mining Dispatch Model
Handles loading electricity prices and hashprice data from various sources
"""

import pandas as pd
import requests
import numpy as np
from datetime import datetime, timedelta
import os
from config import Config

class DataHandler:
    """Handles all data loading, processing, and API interactions"""
    
    def __init__(self):
        self.config = Config()
        self.electricity_data = None
        self.hashprice_data = None
        
    def load_electricity_data(self, selected_load_zones):
        """
        Load electricity price data for selected load zones from CSV files.
        
        Args:
            selected_load_zones (list): List of load zone names (e.g., ["houston", "west"])
            
        Returns:
            pd.DataFrame: Processed electricity price data for all selected zones.
        """
        all_electricity_data = []
        data_dir = self.config.DATA_CONFIG["electricity_data_directory"]
        
        for zone in selected_load_zones:
            file_name = f"{zone}.csv"
            file_path = os.path.join(data_dir, file_name)
            
            try:
                print(f"Loading electricity data from: {file_path}")
                
                # Try different common CSV formats
                try:
                    # Try with standard format first
                    df = pd.read_csv(file_path)
                except Exception as e:
                    # Try with different separators and encodings
                    print(f"Attempting alternative CSV read for {file_name}: {e}")
                    df = pd.read_csv(file_path, sep=";", encoding="utf-8")
                
                print(f"Raw data shape for {zone}: {df.shape}")
                
                # Standardize column names (common variations)
                df.columns = df.columns.str.lower().str.strip()
                
                # Look for datetime and price columns
                datetime_col = self._find_datetime_column(df)
                price_col = self._find_price_column(df)
                
                if datetime_col is None or price_col is None:
                    raise ValueError("Could not identify datetime or price columns")
                
                # Rename to standard names
                df = df.rename(columns={
                    datetime_col: "datetime",
                    price_col: "electricity_price"
                })
                
                # Convert datetime and localize to UTC
                df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce", utc=True)
                df = df.dropna(subset=["datetime"])  # ensure we only keep valid datetimes
                
                # Convert price to numeric
                df["electricity_price"] = pd.to_numeric(df["electricity_price"], errors="coerce")
                
                # Remove any rows with missing data
                df = df.dropna(subset=["datetime", "electricity_price"])
                
                # Set datetime as index
                df = df.set_index("datetime").sort_index()
                
                # Ensure the index is a DatetimeIndex and in UTC
                if not isinstance(df.index, pd.DatetimeIndex):
                    df.index = pd.to_datetime(df.index)
                if df.index.tz is None:
                    df.index = df.index.tz_localize("UTC")
                else:
                    df.index = df.index.tz_convert("UTC")
                
                # Resample to hourly if needed (in case data is 15-minute)
                if len(df) > 0:
                    if len(df) > 1:
                        time_diff = df.index[1] - df.index[0]
                        if time_diff < timedelta(hours=1):
                            print(f"Resampling from {time_diff} to hourly frequency for {zone}")
                            # Only resample numeric columns
                            numeric_cols = df.select_dtypes(include=[np.number]).columns
                            df = df[numeric_cols].resample("h").mean()  # Fixed deprecation warning
                    else:
                        # Handle case with single data point, ensure it's hourly
                        df = df.resample("h").mean()  # Fixed deprecation warning

                df["load_zone"] = zone # Add load zone column
                all_electricity_data.append(df)
                
                print(f"Processed electricity data for {zone}: {len(df)} hourly records")
                print(f"Date range for {zone}: {df.index.min()} to {df.index.max()}")
                print(f"Price range for {zone}: ${df["electricity_price"].min():.2f} - ${df["electricity_price"].max():.2f}")
                
            except Exception as e:
                print(f"Error loading electricity data for {zone}: {e}")
                print("Please check the file path and format")
                raise
        
        if not all_electricity_data:
            raise ValueError("No electricity data could be loaded for the selected zones.")
            
        self.electricity_data = pd.concat(all_electricity_data)
        return self.electricity_data
            
    def _find_datetime_column(self, df):
        """Find the datetime column in the dataframe"""
        datetime_keywords = ["date", "time", "datetime", "timestamp", "hour_ending", "interval_start_local"]
        for col in df.columns:
            col_lower = col.lower().strip()
            if any(keyword in col_lower for keyword in datetime_keywords):
                return col
        return None
    
    def _find_price_column(self, df):
        """Find the price column in the dataframe"""
        price_keywords = ["price", "lmp", "cost", "rate", "mwh", "kwh", "settlement", "lmp_with_adders"]
        for col in df.columns:
            col_lower = col.lower().strip()
            if any(keyword in col_lower for keyword in price_keywords):
                # Skip if it's a datetime-related column
                if not any(dt_keyword in col_lower for dt_keyword in ["date", "time"]):
                    return col
        return None
    
    def load_hashprice_data(self, start_date, end_date):
        """
        Load hashprice data from HashrateIndex API with proper parameters.
        Daily data is forward-filled to hourly frequency.
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            
        Returns:
            pd.DataFrame: DataFrame indexed hourly with a 'hashprice' column
        """
        print(f"Fetching hashprice data from {start_date} to {end_date} using /hashprice ...")
        
        # Prepare request with required parameters
        url = f"{self.config.API_CONFIG['BASE_URL']}/hashprice"
        headers = self.config.get_api_headers()
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "currency": "USD",  # Required parameter
            "hashunit": "THS",   # Required parameter - TeraHash
            "sma": "7D"         # 7-day SMA
        }
        
        print(f"API request parameters: {params}")
        
        # Call API with error handling
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            print(f"API response status: {resp.status_code}")
            
            if resp.status_code != 200:
                print(f"API request failed: {resp.status_code}")
                print(f"Response: {resp.text}")
                
                # Try alternative parameters if the first attempt fails
                if resp.status_code == 422:
                    print("Trying with PH hashunit instead...")
                    params["hashunit"] = "PH"  # Try PetaHash instead
                    resp = requests.get(url, headers=headers, params=params, timeout=30)
                    
                    if resp.status_code != 200:
                        print(f"Second attempt failed: {resp.status_code}")
                        print(f"Response: {resp.text}")
                        raise RuntimeError("Failed to fetch hashprice data from HashrateIndex API")
            
        except requests.exceptions.RequestException as e:
            print(f"Network error occurred: {e}")
            raise RuntimeError(f"Network error while fetching hashprice data: {e}")
        
        # Parse JSON response
        try:
            data = resp.json()
        except ValueError as e:
            print(f"Failed to parse JSON response: {e}")
            print(f"Raw response: {resp.text[:500]}")
            raise RuntimeError("Invalid JSON response from API")
        
        if not isinstance(data, dict) or "data" not in data:
            print(f"Unexpected API response structure: {data}")
            raise ValueError("Unexpected API response structure for hashprice")
        
        df = pd.DataFrame(data["data"])
        print(f"API returned {len(df)} records")
        print(f"Available columns: {df.columns.tolist()}")
        
        # Check for required columns - handle different possible column names
        if "hashprice" not in df.columns:
            # Look for alternative column names
            possible_columns = [col for col in df.columns if 'price' in col.lower() or 'hash' in col.lower()]
            if possible_columns:
                print(f"Using column '{possible_columns[0]}' as hashprice")
                df = df.rename(columns={possible_columns[0]: "hashprice"})
            else:
                raise ValueError(f"No hashprice column found. Available columns: {df.columns.tolist()}")
        
        if "timestamp" not in df.columns:
            # Look for alternative timestamp column names
            possible_time_columns = [col for col in df.columns if any(word in col.lower() for word in ['time', 'date'])]
            if possible_time_columns:
                print(f"Using column '{possible_time_columns[0]}' as timestamp")
                df = df.rename(columns={possible_time_columns[0]: "timestamp"})
            else:
                raise ValueError(f"No timestamp column found. Available columns: {df.columns.tolist()}")
        
        # Parse timestamp and set index
        df["datetime"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.set_index("datetime").sort_index()
        
        # Keep only the hashprice column
        df = df[["hashprice"]]
        
        # Convert to numeric if it's not already
        df["hashprice"] = pd.to_numeric(df["hashprice"], errors="coerce")
        
        # Remove any NaN values
        df = df.dropna()
        
        if len(df) == 0:
            raise ValueError("No valid hashprice data after processing")
        
        # Forward-fill to hourly frequency across requested range
        start_dt = pd.to_datetime(start_date).tz_localize("UTC")
        end_dt = pd.to_datetime(end_date).tz_localize("UTC")
        hourly_index = pd.date_range(start=start_dt, end=end_dt, freq="h", tz="UTC")  # Fixed deprecation warning
        df = df.reindex(hourly_index, method="ffill")
        
        print(f"Loaded hashprice data: {len(df)} hourly records")
        print(f"Hashprice range ($/TH/day): {df['hashprice'].min():.6f} - {df['hashprice'].max():.6f}")
        
        self.hashprice_data = df
        return df
    
    def merge_data(self, electricity_data, hashprice_data, start_date, end_date):
        """
        Merge electricity and hashprice data into a single dataframe
        
        Args:
            electricity_data (pd.DataFrame): Electricity price data
            hashprice_data (pd.DataFrame): Hashprice data
            start_date (str): Filter start date
            end_date (str): Filter end date
            
        Returns:
            pd.DataFrame: Merged and filtered data
        """
        try:
            print("Merging electricity and hashprice data...")
            
            # Convert string dates to timezone-aware datetime objects for filtering
            start_dt_filter = pd.to_datetime(start_date).tz_localize("UTC")
            end_dt_filter = pd.to_datetime(end_date).tz_localize("UTC")
            
            # Filter electricity data (already UTC)
            elec_filtered = electricity_data[
                (electricity_data.index >= start_dt_filter) & 
                (electricity_data.index <= end_dt_filter)
            ].copy()
            
            # Filter hashprice data (already UTC)
            hash_filtered = hashprice_data[
                (hashprice_data.index >= start_dt_filter) & 
                (hashprice_data.index <= end_dt_filter)
            ].copy()
            
            print(f"Electricity data after filtering: {len(elec_filtered)} records")
            print(f"Hashprice data after filtering: {len(hash_filtered)} records")
            
            # Merge on datetime index
            merged = pd.merge(
                elec_filtered, 
                hash_filtered, 
                left_index=True, 
                right_index=True, 
                how="inner"
            )
            
            if len(merged) == 0:
                raise ValueError("No overlapping data found between electricity and hashprice datasets. Check date ranges and timezones.")
            
            # Add additional useful columns
            merged["hour"] = merged.index.hour
            merged["day_of_week"] = merged.index.dayofweek
            merged["month"] = merged.index.month
            
            print(f"Final merged dataset: {len(merged)} records")
            print(f"Date range: {merged.index.min()} to {merged.index.max()}")
            
            return merged
            
        except Exception as e:
            print(f"Error merging data: {e}")
            raise
    
    def save_processed_data(self, data, filename=None):
        """Save processed data to CSV for backup/debugging"""
        if filename is None:
            filename = f"processed_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        os.makedirs(self.config.DATA_CONFIG["cache_directory"], exist_ok=True)
        filepath = os.path.join(self.config.DATA_CONFIG["cache_directory"], filename)
        
        data.to_csv(filepath)
        print(f"Data saved to: {filepath}")
        return filepath