import yfinance as yf
from datetime import datetime, timedelta

def get_option_chain_dates_within_range(symbol, target_date, weeks_range=2):
    try:
        ticker = yf.Ticker(symbol)
        available_dates = ticker.options
        if not available_dates:
            print("No available expiration dates found.")
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
        print(f"Failed to fetch or filter option chain dates: {str(e)}")
        return []

def get_current_stock_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        price = ticker.history(period="1d")['Close'].iloc[-1]
        return price
    except Exception as e:
        print(f"Failed to fetch current stock price: {str(e)}")
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
        print(f"Failed to fetch option premium: {str(e)}")
        return None, None

def validate_stock_symbol(symbol):
    """
    Validates a given stock symbol by checking if it has a regular market price.

    Args:
        symbol (str): The ticker symbol of the stock.

    Returns:
        bool: True if the stock symbol is valid, False otherwise.
    """
    try:
        ticker = yf.Ticker(symbol)
        ticker_info = ticker.info
        print(f"Ticker info for {symbol}: {ticker_info}")

        if 'regularMarketPrice' in ticker_info and ticker_info['regularMarketPrice'] is not None:
            price = ticker_info['regularMarketPrice']
            print(f"Valid stock symbol: {symbol}, Current Price: {price}")
            return True
        else:
            print(f"Stock symbol {symbol} has no current price data or 'regularMarketPrice' key is missing.")
            return False
    except Exception as e:
        print(f"Error validating stock symbol {symbol}: {str(e)}")
        return False
