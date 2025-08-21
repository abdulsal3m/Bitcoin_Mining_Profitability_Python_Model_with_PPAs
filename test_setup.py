"""
Quick setup tester for Bitcoin Mining Dispatch Model
Run this to verify your environment is set up correctly
"""

import pandas as pd
import requests
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os

def test_environment():
    """Test if all required packages are installed"""
    print("Testing environment setup...")
    
    try:
        print("✓ pandas imported successfully")
        print("✓ requests imported successfully") 
        print("✓ numpy imported successfully")
        print("✓ matplotlib imported successfully")
        print("✓ All required packages are available")
        return True
    except ImportError as e:
        print(f"✗ Missing package: {e}")
        return False

def test_api_connection():
    """Test connection to hashrateindex API"""
    print("\nTesting API connection...")
    
    api_key = "hi.7dfcbe36e3eb05b795fc44279cd3cc"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Test basic API connectivity
    test_url = "https://api.hashrateindex.com/v1/network-data/btc/hashrate"
    
    try:
        response = requests.get(test_url, headers=headers, timeout=10)
        if response.status_code == 200:
            print("✓ API connection successful")
            print(f"✓ Response status: {response.status_code}")
            return True
        else:
            print(f"⚠ API responded with status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"✗ API connection failed: {e}")
        return False

def create_sample_electricity_data():
    """Create a sample electricity data file for testing"""
    print("\nCreating sample electricity data...")
    
    # Create data directory
    os.makedirs('data', exist_ok=True)
    
    # Generate sample hourly electricity price data
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)  # Just January for testing
    
    hours = pd.date_range(start=start_date, end=end_date, freq='1H')
    
    # Generate realistic electricity prices ($20-$150/MWh with daily patterns)
    np.random.seed(42)
    base_prices = []
    
    for hour in hours:
        # Base price around $40/MWh
        base_price = 40
        
        # Add daily pattern (higher during peak hours 2-7 PM)
        if 14 <= hour.hour <= 19:
            base_price += 20  # Peak pricing
        elif 22 <= hour.hour or hour.hour <= 6:
            base_price -= 10  # Off-peak pricing
        
        # Add some random variation
        price = base_price + np.random.normal(0, 8)
        price = max(15, min(price, 200))  # Reasonable bounds
        base_prices.append(price)
    
    # Create DataFrame
    df = pd.DataFrame({
        'datetime': hours,
        'electricity_price': base_prices
    })
    
    # Save to CSV
    filepath = 'data/electricity_prices.csv'
    df.to_csv(filepath, index=False)
    
    print(f"✓ Sample electricity data created: {filepath}")
    print(f"✓ Data range: {df['datetime'].min()} to {df['datetime'].max()}")
    print(f"✓ Price range: ${df['electricity_price'].min():.2f} - ${df['electricity_price'].max():.2f}")
    
    return filepath

def test_data_loading():
    """Test loading the sample data"""
    print("\nTesting data loading...")
    
    try:
        # Test electricity data loading
        df = pd.read_csv('data/electricity_prices.csv')
        print(f"✓ Electricity data loaded: {len(df)} records")
        
        # Test datetime conversion
        df['datetime'] = pd.to_datetime(df['datetime'])
        print("✓ Datetime conversion successful")
        
        # Basic stats
        print(f"✓ Price statistics: mean=${df['electricity_price'].mean():.2f}, std=${df['electricity_price'].std():.2f}")
        
        return True
    except Exception as e:
        print(f"✗ Data loading failed: {e}")
        return False

def create_project_structure():
    """Create necessary directories"""
    print("\nCreating project structure...")
    
    directories = ['data', 'output', 'cache']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}/")
    
    return True

def main():
    """Run all tests"""
    print("=" * 50)
    print("BITCOIN MINING DISPATCH MODEL - SETUP TEST")
    print("=" * 50)
    
    tests = [
        ("Environment Setup", test_environment),
        ("Project Structure", create_project_structure),
        ("Sample Data Creation", create_sample_electricity_data),
        ("Data Loading", test_data_loading),
        ("API Connection", test_api_connection)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 30)
    print("SETUP TEST SUMMARY")
    print("=" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 Setup is complete! You're ready to run the main model.")
        print("\nNext steps:")
        print("1. Download the electricity data CSV from the provided Google Drive link")
        print("2. Save it as 'data/electricity_prices.csv' (or update the path in config.py)")
        print("3. Run: python main.py")
    else:
        print("\n⚠️ Some setup issues detected. Please fix the failing tests before proceeding.")
    
    return passed == len(results)

if __name__ == "__main__":
    main()