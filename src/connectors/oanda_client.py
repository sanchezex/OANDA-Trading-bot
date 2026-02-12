"""
OANDA API Client - handles all communication with OANDA.
Uses the official oandapyV20 library.
"""
import oandapyV20
from oandapyV20 import API
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.positions as positions
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.instruments as instruments
from typing import Dict, List, Optional
from config.settings import Config
from src.utils.logger import logger


class OandaClient:
    """
    Wrapper class for OANDA API operations.
    Handles authentication, requests, and response parsing.
    """
    
    def __init__(self):
        """Initialize OANDA API client with credentials from config."""
        self.account_id = Config.OANDA_ACCOUNT_ID
        self.api = API(
            access_token=Config.OANDA_ACCESS_TOKEN,
            environment=Config.OANDA_ENVIRONMENT
        )
        logger.info(f"OANDA client initialized for {Config.OANDA_ENVIRONMENT} environment")
    
    def get_account_summary(self) -> Dict:
        """
        Get account summary information.
        
        Returns:
            Account summary dictionary with balance, equity, etc.
        """
        try:
            r = accounts.AccountSummary(self.account_id)
            response = self.api.request(r)
            return response['account']
        except Exception as e:
            logger.error(f"Failed to get account summary: {e}")
            raise
    
    def get_account_balance(self) -> float:
        """
        Get current account balance.
        
        Returns:
            Account balance as float
        """
        summary = self.get_account_summary()
        balance = float(summary.get('balance', 0))
        return balance
    
    def get_current_price(self, instrument: str) -> Dict:
        """
        Get current bid/ask price for an instrument.
        
        Args:
            instrument: Currency pair (e.g., 'EUR_USD')
            
        Returns:
            Dictionary with bid, ask, mid, and spread
        """
        try:
            params = {"instruments": instrument}
            r = pricing.PricingInfo(self.account_id, params=params)
            response = self.api.request(r)
            
            price_data = response['prices'][0]
            
            result = {
                'instrument': instrument,
                'bid': float(price_data['bids'][0]['price']),
                'ask': float(price_data['asks'][0]['price']),
                'time': price_data['time']
            }
            result['mid'] = (result['bid'] + result['ask']) / 2
            result['spread'] = result['ask'] - result['bid']
            result['spread_pips'] = result['spread'] * 10000
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get price for {instrument}: {e}")
            raise
    
    def place_market_order(self, instrument: str, units: int) -> Dict:
        """
        Place a market order.
        
        Args:
            instrument: Currency pair
            units: Number of units (positive for buy, negative for sell)
            
        Returns:
            Order response dictionary
        """
        try:
            order_data = {
                "order": {
                    "type": "MARKET",
                    "instrument": instrument,
                    "units": str(units)
                }
            }
            
            r = orders.OrderCreate(self.account_id, data=order_data)
            response = self.api.request(r)
            
            logger.info(f"Market order placed: {units} units of {instrument}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to place market order: {e}")
            raise
    
    def place_limit_order(self, instrument: str, units: int, price: float,
                         take_profit: Optional[float] = None,
                         stop_loss: Optional[float] = None) -> Dict:
        """
        Place a limit order.
        
        Args:
            instrument: Currency pair
            units: Number of units (positive for buy, negative for sell)
            price: Limit price
            take_profit: Optional take profit price
            stop_loss: Optional stop loss price
            
        Returns:
            Order response dictionary
        """
        try:
            order_data = {
                "order": {
                    "type": "LIMIT",
                    "instrument": instrument,
                    "units": str(units),
                    "price": str(round(price, 5)),
                    "timeInForce": "GTC"  # Good Till Cancelled
                }
            }
            
            if take_profit:
                order_data["order"]["takeProfitOnFill"] = {
                    "price": str(round(take_profit, 5))
                }
            
            if stop_loss:
                order_data["order"]["stopLossOnFill"] = {
                    "price": str(round(stop_loss, 5))
                }
            
            r = orders.OrderCreate(self.account_id, data=order_data)
            response = self.api.request(r)
            
            action = "BUY" if units > 0 else "SELL"
            logger.info(f"Limit order placed: {action} {abs(units)} {instrument} @ {price}")
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to place limit order: {e}")
            raise
    
    def get_pending_orders(self) -> List[Dict]:
        """
        Get all pending orders.
        
        Returns:
            List of pending order dictionaries
        """
        try:
            r = orders.OrdersPending(self.account_id)
            response = self.api.request(r)
            return response.get('orders', [])
        except Exception as e:
            logger.error(f"Failed to get pending orders: {e}")
            raise
    
    def cancel_order(self, order_id: str) -> Dict:
        """
        Cancel a pending order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            Cancellation response
        """
        try:
            r = orders.OrderCancel(self.account_id, order_id)
            response = self.api.request(r)
            logger.info(f"Order {order_id} cancelled")
            return response
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise
    
    def get_open_positions(self) -> List[Dict]:
        """
        Get all open positions.
        
        Returns:
            List of open position dictionaries
        """
        try:
            r = positions.OpenPositions(self.account_id)
            response = self.api.request(r)
            return response.get('positions', [])
        except Exception as e:
            logger.error(f"Failed to get open positions: {e}")
            raise
    
    def close_position(self, instrument: str) -> Dict:
        """
        Close all positions for an instrument.
        
        Args:
            instrument: Currency pair
            
        Returns:
            Close response
        """
        try:
            data = {
                "longUnits": "ALL",
                "shortUnits": "ALL"
            }
            
            r = positions.PositionClose(self.account_id, instrument, data=data)
            response = self.api.request(r)
            logger.info(f"Closed all positions for {instrument}")
            return response
        except Exception as e:
            logger.error(f"Failed to close position for {instrument}: {e}")
            raise
    
    def get_candles(self, instrument: str, granularity: str = "M1", count: int = 20) -> List[Dict]:
        """
        Get historical candle data.
        
        Args:
            instrument: Currency pair
            granularity: Timeframe (M1, M5, M15, H1, D, etc.)
            count: Number of candles to fetch
            
        Returns:
            List of candle dictionaries
        """
        try:
            params = {
                "granularity": granularity,
                "count": count
            }
            r = instruments.InstrumentsCandles(instrument, params)
            response = self.api.request(r)
            return response.get('candles', [])
        except Exception as e:
            logger.error(f"Failed to get candles for {instrument}: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test connection to OANDA API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            r = accounts.AccountSummary(self.account_id)
            response = self.api.request(r)
            
            if response and 'account' in response:
                logger.info(f"OANDA connection successful")
                logger.info(f"Account: {response['account']['id']}")
                logger.info(f"Balance: ${response['account']['balance']}")
                return True
            else:
                logger.error("Connection failed: Invalid response")
                return False
                
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            return False

