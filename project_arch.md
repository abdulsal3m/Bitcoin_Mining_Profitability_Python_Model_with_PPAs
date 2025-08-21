# Bitcoin Mining Dispatch Model - Project Architecture

## Core Project Structure

```
mining_dispatch_model/
├── main.py # Entry point and user interface
├── config.py # Configuration and constants
├── data_handler.py # API data retrieval and processing, and local data loading
├── mining_calculator.py # Core mining economics calculations
├── dispatch_optimizer.py # Dispatch logic and optimization
├── visualizer.py # Charts and data visualization
├── utils.py # Helper functions
├── requirements.txt # Dependencies
└── README.md # Instructions and documentation
```

## File Responsibilities

### 1. `main.py` - Application Entry Point
- User input collection (facility size, efficiency, date range)
- Orchestrates the entire workflow
- Displays results and visualizations
- Simple CLI interface

### 2. `config.py` - Configuration Management
- API endpoints and keys
- Default parameters for the model
- Constants (electricity price thresholds, etc.)
- ERCOT-specific configurations
- Data paths and processing parameters
- Calculation and visualization parameters
- Risk management parameters

### 3. `data_handler.py` - Data Management
- Handles loading electricity price data from local CSV files.
- Manages API calls to `hashrateindex.com` for hashprice data.
- Performs data cleaning and preprocessing.
- Implements caching mechanisms for efficiency.
- Merges electricity and hashprice data into a single DataFrame.

### 4. `mining_calculator.py` - Core Economics Engine
- Calculates profitability per hour.
- Computes revenue (hashprice × hashrate).
- Determines cost (electricity price × power consumption).
- Calculates net profit.
- Generates summary statistics and performance metrics.

### 5. `dispatch_optimizer.py` - Dispatch Logic
- Makes on/off decisions for the mining operation based on profitability.
- Implements optimization algorithms (currently simple threshold-based).
- Executes backtests over historical data.
- Calculates performance metrics for the dispatch strategy.

### 6. `visualizer.py` - Data Visualization
- Generates line graphs for electricity prices and hashprices.
- Visualizes the dispatch schedule.
- Creates profitability charts.
- Provides summary dashboards.

### 7. `utils.py` - Helper Functions
- Contains general utility functions.
- Date/time handling.
- Data validation.
- Unit conversions.
- Common mathematical calculations.

## Development Approach (Priority Order)

### Phase 1: Core Functionality
1. **Data Pipeline**: Get API integration working, fetch and clean data.
2. **Basic Calculator**: Implement core profitability calculations.
3. **Simple Dispatch**: Basic on/off logic based on net profitability.
4. **Basic Visualization**: Simple line charts showing prices and dispatch decisions.

### Phase 2: Enhancement
1. **Advanced Dispatch Logic**: More sophisticated optimization.
2. **Backtesting Engine**: Historical performance analysis.
3. **Better Visualizations**: Multiple chart types, interactive elements.
4. **Input Validation**: Robust error handling.

### Phase 3: Extensions
1. **Forward Curve Integration**: Forecasting capabilities.
2. **Mixed Fleet Support**: Different miner efficiencies.
3. **PPA Integration**: Fixed price contracts.
4. **Advanced Analytics**: Risk metrics, sensitivity analysis.

## Key Technical Decisions

### Libraries to Use:
- `requests`: For API calls.
- `pandas`: For data manipulation and analysis.
- `matplotlib`/`plotly`: For visualization.
- `numpy`: For numerical calculations.
- `datetime`: For time handling.

### Data Flow:
User Input → Config → Data Fetcher → Calculator → Optimizer → Visualizer → Results

### Core Algorithm (Hourly):
```python
electricity_cost = power_consumption_mw * electricity_price_mwh
mining_revenue = hashrate_th * hashprice_th
net_profit = mining_revenue - electricity_cost

if net_profit > min_profit_threshold:
    operate_mine = True
else:
    operate_mine = False
```

## Minimum Viable Product (MVP) Features

1. **Input Collection**: Facility size (MW), efficiency (W/TH), date range.
2. **Data Retrieval**: Fetch electricity prices (from CSV) and hashprices (from API).
3. **Dispatch Calculation**: Hourly on/off decisions.
4. **Backtest Results**: Total profit, operating hours, efficiency metrics.
5. **Basic Visualization**: Price charts and dispatch schedule.
6. **Clear Output**: Summary statistics and insights.

## Scalability Considerations

- **Modular Design**: Each component is independent and testable.
- **Configuration-Driven**: Easy to modify parameters without code changes.
- **Extensible Architecture**: New features can be added without refactoring core logic.
- **Clean Interfaces**: Well-defined function signatures for easy enhancement.

## Success Metrics for Interview

1. **Functionality**: Model works correctly with transparent calculations.
2. **Usability**: User inputs are easily modifiable.
3. **Clarity**: Results are clearly displayed.
4. **Accessibility**: No paid software required.
5. **Documentation**: Clear usage instructions.

This structure provides a solid foundation to build incrementally, ensuring all core requirements are met first, with impressive extensions possible if time permits.


