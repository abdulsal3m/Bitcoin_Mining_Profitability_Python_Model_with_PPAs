"""
Bitcoin Mining Dispatch Model - Final Version
Main application file that orchestrates the entire workflow
"""

import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Import our custom modules
try:
    from config import Config
    from data_handler import DataHandler
    from mining_calculator import MiningCalculator
    from visualizer import Visualizer

    from utils import validate_date_string, validate_positive_number, validate_date_range
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required files are in the same directory")
    sys.exit(1)

class BitcoinMiningDispatch:
    """Main application class for Bitcoin mining dispatch optimization"""
    
    def __init__(self):
        self.config = Config()
        self.data_handler = DataHandler()
        self.calculator = MiningCalculator()
        self.visualizer = Visualizer()

        
        # Results storage
        self.results = {}
        self.dispatch_data = None
        
    def get_user_inputs(self):
        """Collect user inputs for the model"""
        print("=" * 50)
        print("BITCOIN MINING DISPATCH MODEL")
        print("=" * 50)
        
        try:
            # Load Zone Selection
            available_load_zones = ["houston", "west", "north", "south"]
            print("\nAvailable Load Zones: " + ", ".join(available_load_zones).upper())
            load_zones_input = input("Enter load zone(s) separated by commas (e.g., houston,west): ").lower()
            selected_load_zones = [zone.strip() for zone in load_zones_input.split(",") if zone.strip() in available_load_zones]
            
            if not selected_load_zones:
                raise ValueError("No valid load zones selected. Please choose from the available options.")
            
            facility_sizes = {}
            for zone in selected_load_zones:
                size_input = input(f"Enter facility size in MW for {zone.upper()} (default: 50): ") or "50"
                facility_sizes[zone] = validate_positive_number(float(size_input), f"Facility size for {zone.upper()}")
            
            # Machine efficiency in W/TH
            efficiency_input = input("Enter machine efficiency in W/TH (default: 30): ") or "30"
            efficiency = validate_positive_number(float(efficiency_input), "Machine efficiency")
            
            # Date range
            print("\nDate Range (YYYY-MM-DD format):")
            start_date = input("Start date (default: 2024-01-01): ") or "2024-01-01"
            end_date = input("End date (default: 2024-01-31): ") or "2024-01-31"
            
            # Validate dates
            validate_date_range(start_date, end_date)
            
            # Fixed Price Contract
            fixed_price_contract_choice = input("Do you have a fixed-price contract? (yes/no, default: no): ").lower() or "no"
            contract_details = {"has_contract": False}
            
            if fixed_price_contract_choice == "yes":
                contract_zone = None
                if len(selected_load_zones) > 1:
                    while contract_zone not in selected_load_zones:
                        contract_zone = input(f"Which load zone is the contract for? ({', '.join(selected_load_zones)}): ").lower()
                        if contract_zone not in selected_load_zones:
                            print("Invalid load zone. Please choose from the selected load zones.")
                else:
                    contract_zone = selected_load_zones[0]
                
                contract_size_input = input(f"Enter contract size in MWh for {contract_zone.upper()}: ")
                contract_size = validate_positive_number(float(contract_size_input), "Contract size")
                
                # Contract size cannot be greater than facility size for that zone
                if contract_size > facility_sizes[contract_zone]:
                    print(f"Warning: Contract size ({contract_size} MWh) is greater than facility size ({facility_sizes[contract_zone]} MW) for {contract_zone.upper()}. Contract size will be capped at facility size.")
                    contract_size = facility_sizes[contract_zone]

                print("\nAvailable Contract Blocks: 7x24, 5x16, 2x16, 7x8")
                contract_block = None
                while contract_block not in ["7x24", "5x16", "2x16", "7x8"]:
                    contract_block = input("Enter contract block: ").lower()
                    if contract_block not in ["7x24", "5x16", "2x16", "7x8"]:
                        print("Invalid contract block. Please choose from 7x24, 5x16, 2x16, 7x8.")
                
                contract_rate_input = input(f"Enter fixed price rate in $/MWh for {contract_zone.upper()}: ")
                contract_rate = validate_positive_number(float(contract_rate_input), "Contract rate")
                
                contract_details = {
                    "has_contract": True,
                    "zone": contract_zone,
                    "size_mwh": contract_size,
                    "block": contract_block,
                    "rate_per_mwh": contract_rate
                }
            
            # Additional parameters
            print("\nOptional Parameters:")
            min_profit_input = input("Minimum profit threshold per hour in $ (default: 0): ") or "0"
            min_profit_threshold = float(min_profit_input)
            
            return {
                "selected_load_zones": selected_load_zones,
                "facility_sizes_mw": facility_sizes,
                "efficiency_w_per_th": efficiency,
                "start_date": start_date,
                "end_date": end_date,
                "min_profit_threshold": min_profit_threshold,
                "fixed_price_contract": contract_details
            }
            
        except ValueError as e:
            print(f"Invalid input: {e}")
            print("Please enter valid values and try again.")
            return self.get_user_inputs()  # Retry
    
    def load_data(self, params):
        """Load electricity and hashprice data"""
        print("\n" + "=" * 30)
        print("LOADING DATA")
        print("=" * 30)
        
        # Load electricity price data (from provided CSVs)
        print("Loading electricity price data...")
        electricity_data = self.data_handler.load_electricity_data(params["selected_load_zones"])
        
        # Load hashprice data (from API)
        print("Loading hashprice data from API...")
        hashprice_data = self.data_handler.load_hashprice_data(params["start_date"], params["end_date"])
        
        # Merge and clean data
        print("Processing and merging data...")
        merged_data = self.data_handler.merge_data(electricity_data, hashprice_data, params["start_date"], params["end_date"])
        
        print(f"Data loaded successfully: {len(merged_data)} records")
        return merged_data
    
    def run_dispatch_model(self, params, data):
        """Run the core dispatch optimization model"""
        print("\n" + "=" * 30)
        print("RUNNING DISPATCH MODEL")
        print("=" * 30)
        
        # Calculate profitability for each hour
        print("Calculating hourly profitability...")
        dispatch_results = self.calculator.calculate_dispatch(
            data, 
            params["facility_sizes_mw"],
            params["efficiency_w_per_th"],
            params["min_profit_threshold"],
            params["fixed_price_contract"]
        )
        
        # Generate summary statistics
        print("Generating performance metrics...")
        summary = self.calculator.generate_summary(dispatch_results)
        
        return dispatch_results, summary
    

    
    def display_results(self, summary, dispatch_data):
        """Display results in a clear format"""
        print("\n" + "=" * 40)
        print("DISPATCH MODEL RESULTS")
        print("=" * 40)
        
        print(f"Total Operating Hours: {summary['operating_hours']:,}")
        print(f"Total Hours Available: {summary['total_hours']:,}")
        print(f"Capacity Factor: {summary['capacity_factor']:.2%}")
        print(f"Total Revenue: ${summary['total_revenue']:,.2f}")
        print(f"Total Electricity Costs: ${summary['total_electricity_cost']:,.2f}")
        print(f"Total Net Profit: ${summary['total_profit']:,.2f}")
        print(f"Average Profit per Operating Hour: ${summary['avg_profit_per_hour']:.2f}")
        
        # Additional insights
        print(f"\nOperational Insights:")
        if summary.get("best_month"):
            print(f"Best Month: {summary['best_month']}")
        if summary.get("worst_month"):
            print(f"Worst Month: {summary['worst_month']}")
        print(f"Average Electricity Price: ${summary['avg_electricity_price']:.2f}/MWh")
        print(f"Average Hashprice: ${summary['avg_hashprice']:.6f}/TH/day")
        
        # Profitability breakdown
        print(f"\nProfitability Breakdown:")
        print(f"Profitable Hours: {summary['profitable_hours']:,}")
        print(f"Unprofitable Hours: {summary['unprofitable_hours']:,}")
        print(f"Facility Hashrate: {summary['hashrate_th']:,.0f} TH/s")
    

    
    def generate_visualizations(self, dispatch_data, params, summary_stats):
        """Generate charts and visualizations"""
        print("\n" + "=" * 30)
        print("GENERATING VISUALIZATIONS")
        print("=" * 30)
        
        # Create all visualizations
        self.visualizer.create_all_charts(dispatch_data, summary_stats)
        
        print("All charts saved to \'output/\' directory")
    
    def export_results(self, filename=None):
        """Export results to CSV for further analysis"""
        if self.dispatch_data is None:
            print("No results to export. Run the model first.")
            return None
        
        if filename is None:
            filename = f"mining_dispatch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Ensure output directory exists
        os.makedirs("output", exist_ok=True)
        filepath = os.path.join("output", filename)
        
        self.dispatch_data.to_csv(filepath)
        print(f"Results exported to: {filepath}")
        return filepath

def run_with_params(selected_load_zones=["houston"], facility_sizes_mw={"houston": 50}, efficiency_w_per_th=30, 
                   start_date="2024-01-01", end_date="2024-01-31", 
                   min_profit_threshold=0, fixed_price_contract={"has_contract": False}):
    """Run the model with specified parameters (for testing/automation)"""
    print("Running Bitcoin Mining Dispatch Model with specified parameters...")
    
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    # Initialize the model
    mining_model = BitcoinMiningDispatch()
    
    # Set parameters
    params = {
        "selected_load_zones": selected_load_zones,
        "facility_sizes_mw": facility_sizes_mw,
        "efficiency_w_per_th": efficiency_w_per_th,
        "start_date": start_date,
        "end_date": end_date,
        "min_profit_threshold": min_profit_threshold,
        "fixed_price_contract": fixed_price_contract
    }
    
    try:
        # Load data
        data = mining_model.load_data(params)
        
        # Run dispatch model
        dispatch_data, summary = mining_model.run_dispatch_model(params, data)
        


        # Generate visualizations
        mining_model.generate_visualizations(dispatch_data, params, summary)
        
        # Store results for export
        mining_model.dispatch_data = dispatch_data
        mining_model.results = {
            "parameters": params,
            "summary": summary,
            "dispatch_data": dispatch_data
        }
        
        # Export results
        filepath = mining_model.export_results()
        
        print("\n" + "=" * 40)
        print("MODEL EXECUTION COMPLETED SUCCESSFULLY")
        print("=" * 40)
        
        return {
            "success": True,
            "summary": summary,

            "export_file": filepath
        }
        
    except Exception as e:
        print(f"\nError during execution: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def run_interactive():
    """Run the model interactively"""
    print("Initializing Bitcoin Mining Dispatch Model...")
    
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    # Initialize the model
    mining_model = BitcoinMiningDispatch()
    
    try:
        # Get user inputs
        params = mining_model.get_user_inputs()
        
        # Load data
        data = mining_model.load_data(params)
        
        # Run dispatch model
        dispatch_data, summary = mining_model.run_dispatch_model(params, data)
        


        # Generate visualizations
        mining_model.generate_visualizations(dispatch_data, params, summary)
        
        # Store results for export
        mining_model.dispatch_data = dispatch_data
        mining_model.results = {
            "parameters": params,
            "summary": summary,
            "dispatch_data": dispatch_data
        }
        
        # Export results automatically
        mining_model.export_results()
        
        print("\nModel completed successfully!")
        print("Check the \'output/\' directory for:")
        print("- CSV file with detailed results")
        print("- PNG charts showing dispatch schedule and profitability")
        
        return True
        
    except Exception as e:
        print(f"Model execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "auto":
        # Example of running with predefined parameters
        # This can be used for automated testing or specific scenarios
        # run_with_params(selected_load_zones=["houston", "west"], facility_sizes_mw={"houston": 100, "west": 50})
        print("Running in automated mode (not yet fully implemented for all features).")
        print("Please run without 'auto' argument for interactive mode.")
    else:
        run_interactive()

if __name__ == "__main__":
    main()
