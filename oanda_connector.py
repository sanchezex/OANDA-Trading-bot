"""
OANDA API Connector Module
Handles authentication and connection to OANDA v20 API
"""

import requests
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OANDAConnector:
    """Establishes and maintains connection to OANDA API"""
    
    def __init__(self, access_token: str, account_id: str, environment: str = "practice"):
        """
        Initialize OANDA connector
        
        Args:
            access_token (str): OANDA API token
            account_id (str): OANDA account ID
            environment (str): 'practice' or 'live'
        """
        self.access_token = access_token
        self.account_id = account_id
        self.environment = environment
        
        # Set the correct URL based on environment
        if environment == "practice":
            self.base_url = "https://api-fxpractice.oanda.com"
        else:
            self.base_url = "https://api-fxtrade.oanda.com"
        
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "AcceptDatetimeFormat": "UNIX",
            "Content-Type": "application/json"
        }
        
        logger.info(f"OANDA Connector initialized for {environment} environment")
    
    def test_connection(self) -> bool:
        """
        Test connection to OANDA API
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            url = f"{self.base_url}/v3/accounts/{self.account_id}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                logger.info("✓ OANDA Connection successful")
                account_data = response.json()
                logger.info(f"Account: {account_data['account']['id']}")
                logger.info(f"Balance: ${account_data['account']['balance']}")
                return True
            else:
                logger.error(f"✗ Connection failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
        except Exception as e:
            logger.error(f"✗ Connection error: {str(e)}")
            return False
    
    def get_account_summary(self) -> dict:
        """
        Fetch account summary including balance, equity, open positions
        
        Returns:
            dict: Account data
        """
        try:
            url = f"{self.base_url}/v3/accounts/{self.account_id}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()['account']
            else:
                logger.error(f"Failed to fetch account summary: {response.text}")
                return {}
        except Exception as e:
            logger.error(f"Error fetching account summary: {str(e)}")
            return {}
    
    def get_account_balance(self) -> float:
        """Get current account balance"""
        account = self.get_account_summary()
        return float(account.get('balance', 0))
    
    def get_account_equity(self) -> float:
        """Get current account equity (balance + unrealized P&L)"""
        account = self.get_account_summary()
        return float(account.get('equity', 0))
    
    def get_open_positions_count(self) -> int:
        """Get count of open positions"""
        account = self.get_account_summary()
        positions = account.get('openPositionCount', 0)
        return int(positions)
    
    def make_request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """
        Make a generic API request
        
        Args:
            method (str): HTTP method (GET, POST, PUT, DELETE)
            endpoint (str): API endpoint path (without base URL)
            data (dict): Request body data
            
        Returns:
            dict: Response data
        """
        try:
            url = f"{self.base_url}/{endpoint}"
            
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return {}
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"API Error ({response.status_code}): {response.text}")
                return {"error": response.text}
        
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return {"error": str(e)}


def create_connector_from_config(config_path: str) -> OANDAConnector:
    """
    Create OANDAConnector from config file
    
    Args:
        config_path (str): Path to config.json
        
    Returns:
        OANDAConnector: Initialized connector
    """
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    return OANDAConnector(
        access_token=config['account']['access_token'],
        account_id=config['account']['account_id'],
        environment=config['account']['environment']
    )
