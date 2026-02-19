"""
Configuration settings for the grid trading bot.
Loads environment variables from .env file or Vercel environment.
"""
import os
from dotenv import load_dotenv
from pathlib import Path


# Load environment variables from .env file (for local development)
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Main configuration class for the grid trading bot."""
    
    # OANDA Credentials - Check Vercel env vars first, then .env
    OANDA_ACCOUNT_ID = os.getenv('OANDA_ACCOUNT_ID') or os.getenv('ACCOUNT_ID')
    OANDA_ACCESS_TOKEN = os.getenv('OANDA_ACCESS_TOKEN') or os.getenv('ACCESS_TOKEN')
    OANDA_ENVIRONMENT = os.getenv('OANDA_ENVIRONMENT', 'practice')
    
    # API Endpoints
    OANDA_API_URL = {
        'practice': 'https://api-fxpractice.oanda.com',
        'live': 'https://api-fxtrade.oanda.com'
    }
    
    # Trading Parameters
    TRADING_PAIR = os.getenv('TRADING_PAIR', 'EUR_USD')
    GRID_LOWER_BOUND = float(os.getenv('GRID_LOWER_BOUND', 1.0700))
    GRID_UPPER_BOUND = float(os.getenv('GRID_UPPER_BOUND', 1.0900))
    NUMBER_OF_GRIDS = int(os.getenv('NUMBER_OF_GRIDS', 20))
    POSITION_SIZE = int(os.getenv('POSITION_SIZE', 1000))
    
    # Risk Management
    MAX_LOSS_PERCENT = float(os.getenv('MAX_LOSS_PERCENT', 10))
    STOP_LOSS_PIPS = int(os.getenv('STOP_LOSS_PIPS', 50))
    TAKE_PROFIT_PIPS = int(os.getenv('TAKE_PROFIT_PIPS', 10))
    
    # Bot Settings
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 60))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Paths
    BASE_DIR = Path(__file__).resolve().parent.parent
    LOG_DIR = BASE_DIR / 'logs'
    DATA_DIR = BASE_DIR / 'data'
    
    @classmethod
    def validate(cls):
        """Check that required settings are present."""
        if not cls.OANDA_ACCOUNT_ID:
            raise ValueError("OANDA_ACCOUNT_ID is required")
        if not cls.OANDA_ACCESS_TOKEN:
            raise ValueError("OANDA_ACCESS_TOKEN is required")
        
        # Create directories if they don't exist
        cls.LOG_DIR.mkdir(exist_ok=True)
        cls.DATA_DIR.mkdir(exist_ok=True)
        
        return True
    
    @classmethod
    def get_api_url(cls):
        """Get the appropriate OANDA API URL."""
        return cls.OANDA_API_URL.get(cls.OANDA_ENVIRONMENT)

