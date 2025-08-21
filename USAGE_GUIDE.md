# Bitcoin Mining Dispatch Model - Usage Guide

## Quick Start

### 1. Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Test your setup
python test_setup.py
```

### 2. Prepare Your Data
Place your electricity price data in a CSV file at `data/electricity_prices.csv`. The file should have columns for datetime and electricity price (case-insensitive column names are supported).

Example format:
```csv
datetime,electricity_price
2024-01-01 00:00:00,35.50
2024-01-01 01:00:00,32.25
...
```

### 3. Run the Model

**Interactive Mode:**
```bash
python main.py
```

**Automated Mode (for testing):**
```bash
python main.py auto
```

## Model Requirements Compliance

This model meets all the specified requirements:

✅ **Incorporates historical electricity price and hashprice data**
- Loads electricity prices from CSV files
- Fetches hashprice data from Hashrate Index API (with fallback to realistic dummy data)

✅ **Assesses profitability based on facility efficiency**
- Calculates hourly revenue: `hashrate_th * hashprice_per_th_day / 24`
- Calculates hourly costs: `facility_size_mw * electricity_price_per_mwh`
- Determines net profit: `revenue - costs`

✅ **Identifies hours to operate or remain offline**
- Simple threshold strategy: operate when `hourly_profit > min_threshold`
- Advanced strategies: percentile-based, rolling average, peak-hour avoidance
- Outputs clear on/off decisions for each hour

✅ **Computes overall profitability through backtesting**
- Calculates total profit, revenue, and costs over the entire period
- Provides capacity factor, operating hours, and efficiency metrics
- Compares multiple dispatch strategies to find the optimal approach

## Key Features

### Data Integration
- **Electricity Data**: Loads from CSV with flexible column detection
- **Hashprice Data**: API integration with Hashrate Index
- **Data Validation**: Automatic cleaning and error handling

### Profitability Calculations
- **Facility Sizing**: Converts MW capacity to TH/s hashrate based on efficiency
- **Revenue Modeling**: Hourly revenue based on hashprice and facility hashrate
- **Cost Modeling**: Electricity costs based on facility power consumption
- **Profit Optimization**: Multiple dispatch strategies to maximize profitability

### Dispatch Strategies
1. **Simple Threshold**: Operate when profit > threshold
2. **Percentile-Based**: Operate during top X% of profitable hours
3. **Rolling Average**: Operate when profit exceeds rolling average
4. **Peak Hour Avoidance**: Avoid high electricity price periods
5. **Custom Strategies**: Extensible framework for additional strategies

### Visualization & Reporting
- **Dispatch Schedule**: Visual timeline of on/off decisions
- **Profitability Analysis**: Charts showing cumulative profit, daily distributions
- **Price Comparisons**: Electricity vs hashprice correlation analysis
- **Summary Dashboard**: Comprehensive overview with key metrics
- **CSV Export**: Detailed hourly results for further analysis

## Input Parameters

### Required Parameters
- **Facility Size (MW)**: Total power capacity of the mining facility
- **Efficiency (W/TH)**: Power consumption per terahash (typical: 20-50 W/TH)
- **Start Date**: Beginning of analysis period (YYYY-MM-DD)
- **End Date**: End of analysis period (YYYY-MM-DD)

### Optional Parameters
- **Min Profit Threshold**: Minimum hourly profit required to operate (default: $0)

## Output Files

The model generates several output files in the `output/` directory:

1. **mining_dispatch_results_[timestamp].csv**: Detailed hourly data with all calculations
2. **dispatch_schedule.png**: Visual timeline of operating decisions
3. **profitability_analysis.png**: Multi-panel profitability analysis
4. **price_comparison.png**: Electricity price vs hashprice trends
5. **summary_dashboard.png**: Comprehensive results dashboard

## Sample Results

For a 50 MW facility with 30 W/TH efficiency over January 2024:

```
Total Operating Hours: 720
Total Hours Available: 721
Capacity Factor: 99.86%
Total Revenue: $3,245,571.30
Total Electricity Costs: $1,483,255.09
Total Net Profit: $1,762,316.21
Average Profit per Operating Hour: $2,447.66
```

## Advanced Usage

### Custom Dispatch Strategies
You can extend the `DispatchOptimizer` class to implement custom strategies:

```python
def custom_strategy(self, data):
    # Your custom logic here
    return dispatch_decisions  # Boolean series
```

### API Configuration
Update the API key in `config.py` if you have your own Hashrate Index API access:

```python
API_KEY = "your_api_key_here"
```

### Batch Processing
For multiple scenarios, use the programmatic interface:

```python
from main import run_with_params

result = run_with_params(
    facility_size_mw=100,
    efficiency_w_per_th=25,
    start_date="2024-01-01",
    end_date="2024-12-31"
)
```

## Validation & Testing

Run the validation suite to ensure everything is working correctly:

```bash
python test_validation.py
```

This tests:
- Configuration loading
- Data processing
- Calculation accuracy
- Dispatch logic
- Full workflow integration

## Troubleshooting

### Common Issues

1. **API Connection Failed**: The model will automatically use realistic dummy hashprice data if the API is unavailable.

2. **CSV Format Issues**: The data handler automatically detects common column name variations and formats.

3. **Date Range Errors**: Ensure dates are in YYYY-MM-DD format and start_date < end_date.

4. **Memory Issues**: For very large datasets (>1 year), consider breaking into smaller chunks.

### Performance Tips

- Use shorter date ranges for faster processing during development
- The model processes ~1000 hours in a few seconds on typical hardware
- Visualization generation takes the most time for large datasets

## Technical Architecture

The model follows a modular design:

- **main.py**: Application entry point and workflow orchestration
- **config.py**: Configuration management and constants
- **data_handler.py**: Data loading, cleaning, and API integration
- **mining_calculator.py**: Core profitability calculations
- **dispatch_optimizer.py**: Dispatch strategies and optimization
- **visualizer.py**: Chart generation and data visualization
- **utils.py**: Helper functions and utilities

This architecture makes the model easily extensible and maintainable for production use.

