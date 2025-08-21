"""
Validation tests for Bitcoin Mining Dispatch Model
Tests the core functionality and validates calculations
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Import our modules
from config import Config
from data_handler import DataHandler
from mining_calculator import MiningCalculator
from visualizer import Visualizer
from dispatch_optimizer import DispatchOptimizer
from utils import validate_positive_number, validate_date_range

def test_config():
    """Test configuration loading"""
    print("Testing configuration...")
    config = Config()
    
    # Test basic config values
    assert config.DEFAULT_FACILITY_SIZE_MW > 0, "Default facility size should be positive"
    assert config.DEFAULT_EFFICIENCY_W_PER_TH > 0, "Default efficiency should be positive"
    assert len(config.ENDPOINTS) > 0, "Should have API endpoints configured"
    
    # Test API headers
    headers = config.get_api_headers()
    assert 'Authorization' in headers, "Should have authorization header"
    
    print("✓ Configuration tests passed")

def test_data_handler():
    """Test data loading and processing"""
    print("Testing data handler...")
    handler = DataHandler()
    
    # Test electricity data loading
    try:
        elec_data = handler.load_electricity_data()
        assert len(elec_data) > 0, "Should load electricity data"
        assert 'electricity_price' in elec_data.columns, "Should have electricity_price column"
        print(f"✓ Loaded {len(elec_data)} electricity records")
    except Exception as e:
        print(f"✗ Electricity data loading failed: {e}")
        return False
    
    # Test hashprice data loading (will use dummy data)
    try:
        hash_data = handler.load_hashprice_data("2024-01-01", "2024-01-31")
        assert len(hash_data) > 0, "Should load hashprice data"
        assert 'hashprice' in hash_data.columns, "Should have hashprice column"
        print(f"✓ Loaded {len(hash_data)} hashprice records")
    except Exception as e:
        print(f"✗ Hashprice data loading failed: {e}")
        return False
    
    # Test data merging
    try:
        merged = handler.merge_data(elec_data, hash_data, "2024-01-01", "2024-01-31")
        assert len(merged) > 0, "Should merge data successfully"
        assert 'electricity_price' in merged.columns, "Merged data should have electricity_price"
        assert 'hashprice' in merged.columns, "Merged data should have hashprice"
        print(f"✓ Merged {len(merged)} records")
    except Exception as e:
        print(f"✗ Data merging failed: {e}")
        return False
    
    print("✓ Data handler tests passed")
    return True

def test_mining_calculator():
    """Test mining calculations"""
    print("Testing mining calculator...")
    calculator = MiningCalculator()
    
    # Test hashrate calculation
    facility_size = 50  # MW
    efficiency = 30  # W/TH
    hashrate = calculator.calculate_hashrate_from_facility(facility_size, efficiency)
    
    expected_hashrate = (facility_size * 1000 * 1000) / efficiency  # Should be ~1.67M TH/s
    assert abs(hashrate - expected_hashrate) < 1000, f"Hashrate calculation error: {hashrate} vs {expected_hashrate}"
    print(f"✓ Hashrate calculation: {hashrate:,.0f} TH/s")
    
    # Test revenue calculation
    hashprice = 0.065  # $/TH/day
    revenue = calculator.calculate_hourly_revenue(hashrate, hashprice)
    expected_revenue = hashrate * (hashprice / 24)  # Convert daily to hourly
    assert abs(revenue - expected_revenue) < 1, f"Revenue calculation error: {revenue} vs {expected_revenue}"
    print(f"✓ Revenue calculation: ${revenue:.2f}/hour")
    
    # Test electricity cost calculation
    electricity_price = 40  # $/MWh
    cost = calculator.calculate_hourly_electricity_cost(facility_size, electricity_price)
    expected_cost = facility_size * electricity_price
    assert abs(cost - expected_cost) < 1, f"Cost calculation error: {cost} vs {expected_cost}"
    print(f"✓ Electricity cost calculation: ${cost:.2f}/hour")
    
    # Test profit calculation
    profit = calculator.calculate_hourly_profit(revenue, cost)
    expected_profit = revenue - cost
    assert abs(profit - expected_profit) < 0.01, f"Profit calculation error: {profit} vs {expected_profit}"
    print(f"✓ Profit calculation: ${profit:.2f}/hour")
    
    print("✓ Mining calculator tests passed")
    return True

def test_dispatch_logic():
    """Test dispatch optimization logic"""
    print("Testing dispatch logic...")
    
    # Create sample data
    dates = pd.date_range('2024-01-01', '2024-01-02', freq='h')
    sample_data = pd.DataFrame({
        'electricity_price': np.random.uniform(20, 80, len(dates)),
        'hashprice': np.random.uniform(0.04, 0.08, len(dates)),
        'hourly_profit': np.random.uniform(-100, 500, len(dates))
    }, index=dates)
    
    optimizer = DispatchOptimizer()
    
    # Test simple threshold dispatch
    dispatch_decisions = optimizer.simple_threshold_dispatch(sample_data, 0)
    profitable_hours = (sample_data['hourly_profit'] > 0).sum()
    operating_hours = dispatch_decisions.sum()
    
    assert operating_hours == profitable_hours, "Simple threshold should operate only when profitable"
    print(f"✓ Simple threshold dispatch: {operating_hours}/{len(sample_data)} hours")
    
    # Test performance evaluation
    performance = optimizer.evaluate_dispatch_performance(sample_data, dispatch_decisions)
    assert 'total_profit' in performance, "Should calculate total profit"
    assert 'capacity_factor' in performance, "Should calculate capacity factor"
    print(f"✓ Performance evaluation: ${performance['total_profit']:.2f} profit")
    
    print("✓ Dispatch logic tests passed")
    return True

def test_full_workflow():
    """Test the complete workflow"""
    print("Testing full workflow...")
    
    try:
        # Import the main function
        from main_final import run_with_params
        
        # Run with test parameters
        result = run_with_params(
            facility_size_mw=25,  # Smaller facility for faster testing
            efficiency_w_per_th=35,
            start_date="2024-01-01",
            end_date="2024-01-07",  # Just one week
            min_profit_threshold=0
        )
        
        assert result['success'], f"Full workflow failed: {result.get('error', 'Unknown error')}"
        assert 'summary' in result, "Should return summary"
        assert 'export_file' in result, "Should export results"
        
        # Validate summary metrics
        summary = result['summary']
        assert summary['total_hours'] > 0, "Should have processed hours"
        assert summary['facility_size_mw'] == 25, "Should preserve facility size"
        assert summary['efficiency_w_per_th'] == 35, "Should preserve efficiency"
        
        print(f"✓ Full workflow test passed")
        print(f"  - Processed {summary['total_hours']} hours")
        print(f"  - Operating hours: {summary['operating_hours']}")
        print(f"  - Total profit: ${summary['total_profit']:,.2f}")
        print(f"  - Capacity factor: {summary['capacity_factor']:.2%}")
        
        return True
        
    except Exception as e:
        print(f"✗ Full workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_cases():
    """Test edge cases and error handling"""
    print("Testing edge cases...")
    
    # Test invalid inputs
    try:
        validate_positive_number(-5, "test")
        assert False, "Should raise error for negative number"
    except ValueError:
        print("✓ Negative number validation works")
    
    try:
        validate_date_range("2024-01-31", "2024-01-01")
        assert False, "Should raise error for invalid date range"
    except ValueError:
        print("✓ Date range validation works")
    
    # Test calculator with extreme values
    calculator = MiningCalculator()
    
    # Very small facility
    small_hashrate = calculator.calculate_hashrate_from_facility(0.1, 30)
    assert small_hashrate > 0, "Should handle small facilities"
    print(f"✓ Small facility handling: {small_hashrate:.0f} TH/s")
    
    # Very efficient miners
    efficient_hashrate = calculator.calculate_hashrate_from_facility(50, 15)  # Very efficient
    inefficient_hashrate = calculator.calculate_hashrate_from_facility(50, 60)  # Less efficient
    assert efficient_hashrate > inefficient_hashrate, "More efficient should give higher hashrate"
    print("✓ Efficiency comparison works")
    
    print("✓ Edge case tests passed")
    return True

def run_all_tests():
    """Run all validation tests"""
    print("=" * 50)
    print("BITCOIN MINING DISPATCH MODEL - VALIDATION TESTS")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_config),
        ("Data Handler", test_data_handler),
        ("Mining Calculator", test_mining_calculator),
        ("Dispatch Logic", test_dispatch_logic),
        ("Edge Cases", test_edge_cases),
        ("Full Workflow", test_full_workflow)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} PASSED")
            else:
                failed += 1
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} FAILED: {e}")
    
    print("\n" + "=" * 30)
    print("VALIDATION TEST SUMMARY")
    print("=" * 30)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! The model is working correctly.")
        return True
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

