import yfinance as yf
from datetime import datetime, timedelta
import logging

def get_option_chain_dates_within_range(symbol, target_date, weeks_range=2):
    try:
        ticker = yf.TTicker(symbol)
        available_dates = ticker.options
        if not available_dates:
            logging.error("No available expiration dates found for symbol: %s", symbol)
            return []

        target_date = datetime.strptime(target_date, "%Y-%m-%d")
        start_date = target_date - timedelta(weeks=weeks_range)
        end_date = target_date + timedelta(weeks=weeks_range)

        filtered_dates = [
            date for date in available_dates
            if start_date <= datetime.strptime(date, "%Y-%m-%d") <= end_date
        ]

        return filtered_dates
    except Exception as e:
        logging.error(f"Failed to fetch or filter option chain dates for {symbol}: {str(e)}")
        return []

def get_current_stock_price(symbol):
    try:
        logging.debug(f"Fetching current stock price for symbol: {symbol}")
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="1d")
        if history.empty:
            logging.error(f"No historical data found for symbol: {symbol}")
            return None
        price = history['Close'].iloc[-1]
        logging.debug(f"Current stock price for {symbol} is {price}")
        return price
    except Exception as e:
        logging.error(f"Failed to fetch current stock price for {symbol}: {str(e)}")
        return None

def get_option_premium(symbol, expiration_date, strike_price):
    try:
        options = yf.Ticker(symbol).option_chain(expiration_date)
        call_data = options.calls[options.calls['strike'] == float(strike_price)]
        put_data = options.puts[options.puts['strike'] == float(strike_price)]
        call_premium = call_data.iloc[0]['lastPrice'] if not call_data.empty else None
        put_premium = put_data.iloc[0]['lastPrice'] if not put_data.empty else None
        return call_premium, put_premium
    except Exception as e:
        logging.error(f"Failed to fetch option premium for {symbol} at {strike_price} expiring on {expiration_date}: {str(e)}")
        return None, None
