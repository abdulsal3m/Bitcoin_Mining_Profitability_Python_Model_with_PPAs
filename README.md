# Bitcoin Mining Dispatch Model

This project implements a Bitcoin mining dispatch optimization model. It incorporates historical electricity price and hashprice data to assess the profitability of a mining operation, identify optimal operating hours, and compute overall profitability through backtesting.

## Features

- **Data Integration**: Fetches hashprice data from the Hashrate Index API and loads static electricity price data from CSV files.
- **Profitability Calculation**: Calculates hourly profitability based on facility efficiency, electricity costs, and hashprice.
- **Dispatch Optimization**: Determines optimal on/off hours for the mining operation to maximize profit.
- **Backtesting**: Computes overall profitability and key metrics over historical periods.
- **Visualization**: Generates charts to visualize prices, dispatch schedules, and profitability.

## Project Structure

```
mining_dispatch_model/
├── main.py                 # Main application entry point
├── config.py               # Configuration settings
├── data_handler.py         # Handles data loading and processing
├── mining_calculator.py    # Core profitability calculations
├── dispatch_optimizer.py   # Logic for dispatch decisions and backtesting
├── visualizer.py           # Data visualization utilities
├── utils.py                # Helper functions
├── requirements.txt        # Python dependencies
├── README.md               # Project overview and instructions
└── project_arch.md         # Detailed project architecture
```

## Setup and Installation

1.  **Clone the repository :**
    ```bash
    git clone <https://github.com/abdulsal3m/Bitcoin_Mining_Profitability_Python_Model_with_PPAs>
    cd bitcoin_mining_dispatch
    ```

2.  **Install Dependencies:**
    It is recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Prepare Electricity Price Data:**
    Place your historical electricity price data in a CSV file named `electricity_prices.csv` inside a `data/` directory at the root of the project. The `data_handler.py` expects columns like `datetime` and `electricity_price` (case-insensitive).
    
    Example structure:
    ```
    data/
    └── electricity_prices.csv
    ```

4.  **API Key:**
    Ensure your Hashrate Index API key is configured in `config.py`.

## Usage

To run the model, execute `main.py`:

```bash
python main.py
```

The application will prompt you for:
-   Facility size (in MW)
-   Machine efficiency (in W/TH)
-   Start and end dates for the analysis (YYYY-MM-DD)
-   If you have any fixed-price contracts
-   If you have any fixed-price contracts, you will be prompted for contract size and block
-   Minimum profit threshold per hour

After execution, results will be displayed in the console, and visualizations and .csv file will be saved to the `output/` directory.




