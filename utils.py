from datetime import datetime, timedelta
import yfinance as yf

def get_stock_info(ticker_symbol):
    """
    Fetches stock information for a given ticker symbol.

    Args:
        ticker_symbol (str): The ticker symbol of the stock.

    Returns:
        dict: A dictionary containing the stock information.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        print(f"Fetched info for {ticker_symbol}: {info}")
        return info
    except Exception as e:
        print(f"Error fetching stock data for {ticker_symbol}: {e}")
        return None

def get_option_chain_dates_within_range(symbol, target_date, weeks_range=2):
    """
    Fetches option chain dates within a specified range of weeks around the target date.

    Args:
        symbol (str): The ticker symbol of the stock.
        target_date (str): The target date in 'YYYY-MM-DD' format.
        weeks_range (int): The number of weeks before and after the target date to consider.

    Returns:
        list: A list of available option chain dates within the specified range.
    """
    try:
        ticker = yf.Ticker(symbol)
        available_dates = ticker.options
        if not available_dates:
            print(f"No available expiration dates found for {symbol}.")
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
        print(f"Failed to fetch or filter option chain dates for {symbol}: {str(e)}")
        return []

def get_current_stock_price(symbol):
    """
    Fetches the current stock price for a given ticker symbol.

    Args:
        symbol (str): The ticker symbol of the stock.

    Returns:
        float: The current stock price.
    """
    try:
        ticker = yf.Ticker(symbol)
        ticker_info = ticker.info
        print(f"Ticker info for {symbol}: {ticker_info}")
        if 'regularMarketPrice' not in ticker_info or ticker_info['regularMarketPrice'] is None:
            print(f"Invalid stock symbol or missing price data for {symbol}.")
            return None
        price = ticker_info['regularMarketPrice']
        return price
    except Exception as e:
        print(f"Failed to fetch current stock price for {symbol}: {str(e)}")
        return None

def get_option_premium(symbol, expiration_date, strike_price):
    """
    Fetches the option premium for a given symbol, expiration date, and strike price.

    Args:
        symbol (str): The ticker symbol of the stock.
        expiration_date (str): The expiration date in 'YYYY-MM-DD' format.
        strike_price (float): The strike price of the option.

    Returns:
        tuple: A tuple containing the call premium and put premium.
    """
    try:
        options = yf.Ticker(symbol).option_chain(expiration_date)
        call_data = options.calls[options.calls['strike'] == float(strike_price)]
        put_data = options.puts[options.puts['strike'] == float(strike_price)]
        call_premium = call_data.iloc[0]['lastPrice'] if not call_data.empty else None
        put_premium = put_data.iloc[0]['lastPrice'] if not put_data.empty else None
        return call_premium, put_premium
    except Exception as e:
        print(f"Failed to fetch option premium for {symbol} on {expiration_date} at strike {strike_price}: {str(e)}")
        return None, None

# Test fetching stock information and prices
symbols = ["META", "AAPL", "GOOG"]
for symbol in symbols:
    print(f"Stock info for {symbol}: {get_stock_info(symbol)}")
    print(f"Current stock price for {symbol}: {get_current_stock_price(symbol)}")
