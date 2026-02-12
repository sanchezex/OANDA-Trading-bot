"""
Market Data Module
Fetches real-time prices, spreads, and market data from OANDA
"""

import requests
import json
from datetime import datetime
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class MarketData:
    """Handles market data fetching from OANDA"""
    
    def __init__(self, connector):
        """
        Initialize MarketData
        
        Args:
            connector: OANDAConnector instance
        """
        self.connector = connector
        self.base_url = connector.base_url
        self.headers = connector.headers
        self.account_id = connector.account_id
    
    def get_current_price(self, instrument: str) -> Dict[str, float]:
        """
        Get current bid/ask prices for an instrument
        
        Args:
            instrument (str): Currency pair (e.g., 'EUR_USD')
            
        Returns:
            dict: {'bid': float, 'ask': float, 'mid': float}
        """
        try:
            url = f"{self.base_url}/v3/accounts/{self.account_id}/pricing"
            params = {"instruments": instrument}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                prices = data['prices'][0]
                
                bid = float(prices['bids'][0]['price'])
                ask = float(prices['asks'][0]['price'])
                mid = (bid + ask) / 2
                
                result = {
                    'bid': bid,
                    'ask': ask,
                    'mid': mid,
                    'spread_pips': (ask - bid) * 10000,
                    'timestamp': prices['time']
                }
                
                logger.debug(f"{instrument} - Bid: {bid}, Ask: {ask}, Spread: {result['spread_pips']:.1f} pips")
                return result
            else:
                logger.error(f"Failed to fetch price: {response.text}")
                return {}
        
        except Exception as e:
            logger.error(f"Error fetching price for {instrument}: {str(e)}")
            return {}
    
    def get_candle_data(self, instrument: str, granularity: str = "M1", count: int = 20) -> list:
        """
        Get historical candle data
        
        Args:
            instrument (str): Currency pair (e.g., 'EUR_USD')
            granularity (str): Timeframe (M1, M5, M15, H1, D)
            count (int): Number of candles to fetch
            
        Returns:
            list: List of candle dictionaries
        """
        try:
            url = f"{self.base_url}/v3/instruments/{instrument}/candles"
            params = {
                "granularity": granularity,
                "count": count
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                candles = data['candles']
                
                logger.info(f"Fetched {len(candles)} {granularity} candles for {instrument}")
                return candles
            else:
                logger.error(f"Failed to fetch candles: {response.text}")
                return []
        
        except Exception as e:
            logger.error(f"Error fetching candle data: {str(e)}")
            return []
    
    def get_instrument_details(self, instrument: str) -> dict:
        """
        Get detailed information about an instrument
        
        Args:
            instrument (str): Currency pair
            
        Returns:
            dict: Instrument details
        """
        try:
            url = f"{self.base_url}/v3/accounts/{self.account_id}/instruments"
            params = {"instruments": instrument}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['instruments']:
                    return {
                        'name': data['instruments'][0]['name'],
                        'type': data['instruments'][0]['type'],
                        'pip_location': data['instruments'][0]['pipLocation'],
                        'display_precision': data['instruments'][0]['displayPrecision'],
                        'trade_units_precision': data['instruments'][0]['tradeUnitsPrecision'],
                        'minimum_trade_size': data['instruments'][0]['minimumTradeSize'],
                        'maximum_trade_size': data['instruments'][0]['maximumTradeSize'],
                        'maximum_position_size': data['instruments'][0]['maximumPositionSize']
                    }
            
            logger.error(f"Failed to fetch instrument details: {response.text}")
            return {}
        
        except Exception as e:
            logger.error(f"Error fetching instrument details: {str(e)}")
            return {}
    
    def get_multiple_prices(self, instruments: list) -> Dict[str, dict]:
        """
        Get prices for multiple instruments
        
        Args:
            instruments (list): List of instrument pairs
            
        Returns:
            dict: Price data for each instrument
        """
        try:
            url = f"{self.base_url}/v3/accounts/{self.account_id}/pricing"
            params = {"instruments": ",".join(instruments)}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result = {}
                
                for price in data['prices']:
                    instrument = price['instrument']
                    bid = float(price['bids'][0]['price'])
                    ask = float(price['asks'][0]['price'])
                    mid = (bid + ask) / 2
                    
                    result[instrument] = {
                        'bid': bid,
                        'ask': ask,
                        'mid': mid,
                        'spread_pips': (ask - bid) * 10000
                    }
                
                return result
            else:
                logger.error(f"Failed to fetch multiple prices: {response.text}")
                return {}
        
        except Exception as e:
            logger.error(f"Error fetching multiple prices: {str(e)}")
            return {}
    
    def calculate_pips_difference(self, price1: float, price2: float) -> float:
        """
        Calculate difference between two prices in pips
        
        Args:
            price1 (float): First price
            price2 (float): Second price
            
        Returns:
            float: Difference in pips
        """
        return (price2 - price1) * 10000
    
    def is_market_trending(self, instrument: str, threshold: float = 0.005) -> bool:
        """
        Simple check if market is trending
        
        Args:
            instrument (str): Currency pair
            threshold (float): Price change threshold as decimal
            
        Returns:
            bool: True if trending, False if ranging
        """
        candles = self.get_candle_data(instrument, "H1", count=10)
        
        if len(candles) < 2:
            return False
        
        # Calculate price change over last 10 hours
        first_close = float(candles[0]['close'])
        last_close = float(candles[-1]['close'])
        price_change = abs(last_close - first_close) / first_close
        
        return price_change > threshold
