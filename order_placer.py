"""
Order Placer Module
Places, modifies, and cancels orders on OANDA
"""

import json
import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class OrderPlacer:
    """Handles order placement and management"""
    
    def __init__(self, connector):
        """
        Initialize OrderPlacer
        
        Args:
            connector: OANDAConnector instance
        """
        self.connector = connector
        self.base_url = connector.base_url
        self.headers = connector.headers
        self.account_id = connector.account_id
    
    def place_limit_order(self, instrument: str, units: int, price: float, 
                         order_type: str = "BUY", stop_loss: float = None,
                         take_profit: float = None) -> Dict:
        """
        Place a limit order
        
        Args:
            instrument (str): Currency pair (e.g., 'EUR_USD')
            units (int): Number of units to trade
            price (float): Limit price
            order_type (str): 'BUY' or 'SELL'
            stop_loss (float): Optional stop loss price
            take_profit (float): Optional take profit price
            
        Returns:
            dict: Order response from API
        """
        try:
            url = f"{self.base_url}/v3/accounts/{self.account_id}/orders"
            
            order_data = {
                "order": {
                    "instrument": instrument,
                    "units": units if order_type == "BUY" else -units,
                    "price": str(price),
                    "type": "LIMIT",
                    "timeInForce": "GTC"  # Good till cancelled
                }
            }
            
            # Add stop loss if provided
            if stop_loss:
                order_data["order"]["stopLossOnFill"] = {
                    "price": str(stop_loss)
                }
            
            # Add take profit if provided
            if take_profit:
                order_data["order"]["takeProfitOnFill"] = {
                    "price": str(take_profit)
                }
            
            response = self.connector.make_request("POST", "v3/accounts/{}/orders".format(self.account_id), order_data)
            
            if "orderFillTransaction" in response or "orderCreateTransaction" in response:
                logger.info(f"✓ {order_type} Limit Order Placed")
                logger.info(f"  Instrument: {instrument}")
                logger.info(f"  Units: {units}")
                logger.info(f"  Price: {price}")
                return response
            else:
                logger.error(f"✗ Failed to place order: {response}")
                return response
        
        except Exception as e:
            logger.error(f"Error placing limit order: {str(e)}")
            return {"error": str(e)}
    
    def place_market_order(self, instrument: str, units: int, order_type: str = "BUY",
                         stop_loss: float = None, take_profit: float = None) -> Dict:
        """
        Place a market order (executes immediately)
        
        Args:
            instrument (str): Currency pair
            units (int): Number of units
            order_type (str): 'BUY' or 'SELL'
            stop_loss (float): Optional stop loss
            take_profit (float): Optional take profit
            
        Returns:
            dict: Order response
        """
        try:
            url = f"{self.base_url}/v3/accounts/{self.account_id}/orders"
            
            order_data = {
                "order": {
                    "instrument": instrument,
                    "units": units if order_type == "BUY" else -units,
                    "type": "MARKET"
                }
            }
            
            if stop_loss:
                order_data["order"]["stopLossOnFill"] = {
                    "price": str(stop_loss)
                }
            
            if take_profit:
                order_data["order"]["takeProfitOnFill"] = {
                    "price": str(take_profit)
                }
            
            response = self.connector.make_request("POST", "v3/accounts/{}/orders".format(self.account_id), order_data)
            
            if "orderFillTransaction" in response:
                logger.info(f"✓ {order_type} Market Order Executed")
                logger.info(f"  Instrument: {instrument}")
                logger.info(f"  Units: {units}")
                return response
            else:
                logger.error(f"✗ Failed to place market order: {response}")
                return response
        
        except Exception as e:
            logger.error(f"Error placing market order: {str(e)}")
            return {"error": str(e)}
    
    def get_pending_orders(self) -> List[Dict]:
        """
        Get all pending orders
        
        Returns:
            list: List of pending orders
        """
        try:
            response = self.connector.make_request("GET", f"v3/accounts/{self.account_id}/orders")
            
            if "orders" in response:
                pending = [o for o in response["orders"] if o["state"] == "PENDING"]
                logger.info(f"Found {len(pending)} pending orders")
                return pending
            else:
                logger.error(f"Failed to fetch orders: {response}")
                return []
        
        except Exception as e:
            logger.error(f"Error fetching pending orders: {str(e)}")
            return []
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a pending order
        
        Args:
            order_id (str): Order ID to cancel
            
        Returns:
            bool: True if successful
        """
        try:
            response = self.connector.make_request(
                "PUT",
                f"v3/accounts/{self.account_id}/orders/{order_id}/cancel",
                {}
            )
            
            if "orderCancelTransaction" in response:
                logger.info(f"✓ Order {order_id} cancelled")
                return True
            else:
                logger.error(f"✗ Failed to cancel order: {response}")
                return False
        
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return False
    
    def modify_order(self, order_id: str, new_price: float = None, 
                    new_units: int = None) -> bool:
        """
        Modify a pending order
        
        Args:
            order_id (str): Order ID to modify
            new_price (float): New price (for limit orders)
            new_units (int): New unit size
            
        Returns:
            bool: True if successful
        """
        try:
            update_data = {"order": {}}
            
            if new_price:
                update_data["order"]["price"] = str(new_price)
            if new_units:
                update_data["order"]["units"] = new_units
            
            response = self.connector.make_request(
                "PUT",
                f"v3/accounts/{self.account_id}/orders/{order_id}",
                update_data
            )
            
            if "orderUpdateTransaction" in response or "orderRejectTransaction" not in response:
                logger.info(f"✓ Order {order_id} modified")
                return True
            else:
                logger.error(f"✗ Failed to modify order: {response}")
                return False
        
        except Exception as e:
            logger.error(f"Error modifying order: {str(e)}")
            return False
    
    def get_order_details(self, order_id: str) -> Dict:
        """
        Get details of a specific order
        
        Args:
            order_id (str): Order ID
            
        Returns:
            dict: Order details
        """
        try:
            response = self.connector.make_request("GET", f"v3/accounts/{self.account_id}/orders/{order_id}")
            
            if "order" in response:
                return response["order"]
            else:
                logger.error(f"Failed to fetch order details: {response}")
                return {}
        
        except Exception as e:
            logger.error(f"Error fetching order details: {str(e)}")
            return {}
    
    def cancel_all_orders(self) -> int:
        """
        Cancel all pending orders
        
        Returns:
            int: Number of orders cancelled
        """
        pending = self.get_pending_orders()
        cancelled_count = 0
        
        for order in pending:
            if self.cancel_order(order["id"]):
                cancelled_count += 1
        
        logger.info(f"Cancelled {cancelled_count} orders")
        return cancelled_count
    
    def place_grid_buy_orders(self, instrument: str, buy_levels: List[float],
                             units: int) -> List[Dict]:
        """
        Place grid buy orders at specified levels
        
        Args:
            instrument (str): Currency pair
            buy_levels (list): List of price levels to buy at
            units (int): Units per order
            
        Returns:
            list: List of order responses
        """
        orders = []
        logger.info(f"Placing {len(buy_levels)} BUY grid orders...")
        
        for i, price in enumerate(buy_levels, 1):
            order = self.place_limit_order(instrument, units, price, "BUY")
            orders.append(order)
            logger.info(f"  [{i}/{len(buy_levels)}] BUY at {price}")
        
        return orders
    
    def place_grid_sell_orders(self, instrument: str, sell_levels: List[float],
                              units: int) -> List[Dict]:
        """
        Place grid sell orders at specified levels
        
        Args:
            instrument (str): Currency pair
            sell_levels (list): List of price levels to sell at
            units (int): Units per order
            
        Returns:
            list: List of order responses
        """
        orders = []
        logger.info(f"Placing {len(sell_levels)} SELL grid orders...")
        
        for i, price in enumerate(sell_levels, 1):
            order = self.place_limit_order(instrument, units, price, "SELL")
            orders.append(order)
            logger.info(f"  [{i}/{len(sell_levels)}] SELL at {price}")
        
        return orders
    
    def get_open_positions(self) -> List[Dict]:
        """
        Get all open positions
        
        Returns:
            list: List of open positions
        """
        try:
            response = self.connector.make_request("GET", f"v3/accounts/{self.account_id}/openPositions")
            
            if "positions" in response:
                open_positions = [p for p in response["positions"] if float(p["long"]["units"]) != 0 or float(p["short"]["units"]) != 0]
                logger.info(f"Found {len(open_positions)} open positions")
                return open_positions
            else:
                return []
        
        except Exception as e:
            logger.error(f"Error fetching open positions: {str(e)}")
            return []
    
    def get_position_by_instrument(self, instrument: str) -> Dict:
        """
        Get position for a specific instrument
        
        Args:
            instrument (str): Currency pair
            
        Returns:
            dict: Position details
        """
        positions = self.get_open_positions()
        
        for position in positions:
            if position["instrument"] == instrument:
                return position
        
        return {}
