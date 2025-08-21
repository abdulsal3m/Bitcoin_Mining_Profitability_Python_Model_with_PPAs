import os

class Config:
    """Configuration class for the Bitcoin Mining Dispatch Model."""

    # API Configuration
    API_CONFIG = {
        "BASE_URL": "https://api.hashrateindex.com/v1/hashrateindex",
        "API_KEY": "hi.7dfcbe36e3eb05b795fc44279cd3cc"
    }

    # Data Processing Parameters
    DATA_CONFIG = {
        "electricity_data_directory": "data/",  # Path to provided data
        "output_directory": "output/",
        "cache_directory": "cache/",
        "datetime_format": "%Y-%m-%d %H:%M:%S",
        "resample_frequency": "1H"  # Hourly data
    }

    # Mining Parameters
    MINING_CONFIG = {
        "default_facility_size_mw": 50,  # Default facility size in MW
        "default_efficiency_w_per_th": 30, # Default machine efficiency in W/TH
        "default_min_profit_threshold": 0, # Default minimum profit threshold in $
        "hashprice_unit": "TH/s", # Unit for hashprice
        "electricity_price_unit": "$/MWh" # Unit for electricity price
    }

    # Visualization Parameters
    VISUALIZATION_CONFIG = {
        "chart_style": "ggplot", # Matplotlib style
        "dpi": 300, # Dots per inch for saved images
        "figure_size": (12, 6), # Figure size for plots
        "colors": {
            "profit": "#2E8B57",      # Sea Green
            "loss": "#DC143C",        # Crimson
            "neutral": "#4682B4",     # Steel Blue
            "electricity": "#FF8C00", # Dark Orange
            "hashprice": "#9370DB"    # Medium Purple
        }
    }

    def get_api_headers(self):
        """Returns headers for API requests."""
        return {
            "X-Hi-Api-Key": self.API_CONFIG["API_KEY"],
            "Content-Type": "application/json"
        }




