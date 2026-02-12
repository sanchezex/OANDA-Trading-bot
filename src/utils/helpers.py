"""
Helper utility functions for the grid trading bot.
Contains commonly used calculation and formatting functions.
"""
from typing import Union


def pips_to_price(pips: int, pair: str = 'EUR_USD') -> float:
    """
    Convert pips to price movement.
    
    Args:
        pips: Number of pips
        pair: Currency pair
        
    Returns:
        Price movement as float
    """
    # For most pairs, 1 pip = 0.0001
    # For JPY pairs, 1 pip = 0.01
    if 'JPY' in pair:
        return pips * 0.01
    return pips * 0.0001


def price_to_pips(price_diff: float, pair: str = 'EUR_USD') -> int:
    """
    Convert price movement to pips.
    
    Args:
        price_diff: Price difference
        pair: Currency pair
        
    Returns:
        Number of pips
    """
    if 'JPY' in pair:
        return int(price_diff / 0.01)
    return int(price_diff / 0.0001)


def format_currency(amount: float, decimals: int = 2) -> str:
    """
    Format amount as currency string.
    
    Args:
        amount: Amount to format
        decimals: Number of decimal places
        
    Returns:
        Formatted string
    """
    return f"${amount:,.{decimals}f}"


def calculate_position_value(units: int, price: float) -> float:
    """
    Calculate the value of a position.
    
    Args:
        units: Number of units
        price: Current price
        
    Returns:
        Position value
    """
    return abs(units) * price


def calculate_profit_loss(entry_price: float, current_price: float, 
                         units: int, pair: str = 'EUR_USD') -> dict:
    """
    Calculate profit/loss for a position.
    
    Args:
        entry_price: Entry price
        current_price: Current market price
        units: Position size (positive for long, negative for short)
        pair: Currency pair
        
    Returns:
        Dictionary with PnL details
    """
    price_diff = current_price - entry_price
    
    # For long positions, profit when price goes up
    # For short positions, profit when price goes down
    if units > 0:
        pnl = units * price_diff
    else:
        pnl = abs(units) * -price_diff
    
    pips = price_to_pips(abs(price_diff), pair)
    
    return {
        'pnl': pnl,
        'pips': pips if pnl > 0 else -pips,
        'percent': (pnl / (abs(units) * entry_price)) * 100
    }

