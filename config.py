import os

# Zerodha credentials
ZERODHA_USER_ID = os.getenv('ZERODHA_USER_ID')
ZERODHA_PASSWORD = os.getenv('ZERODHA_PASSWORD')

# Trading hours (IST)
TRADING_START_HOUR = 2
TRADING_START_MINUTE = 50
TRADING_END_HOUR = 15
TRADING_END_MINUTE = 30

# Scraping intervals
INITIAL_WAIT_SECONDS = 22
SCRAPING_INTERVAL_SECONDS = 22

# Nifty options
SENSIBULL_BASE_URL = 'https://web.sensibull.com/option-chain'
SENSIBULL_URL = 'https://web.sensibull.com/option-chain?tradingsymbol=NIFTY'  # Legacy, for backward compatibility
NIFTY_TICKER = "^NSEI"

# Default expiry dates
DEFAULT_NIFTY_EXPIRY = "2026-06-30"  # Update as needed

# Strike price configuration
STRIKE_RANGE = 4  # How many strikes above and below central strike
STRIKE_INTERVAL = 100  # Strike price intervals

# Chrome driver path
CHROMEDRIVER_PATH = './chromedriver'


def build_sensibull_url(symbol, expiry):
    """Build Sensibull URL for a given symbol and expiry date"""
    return f"{SENSIBULL_BASE_URL}?tradingsymbol={symbol}&view=all&expiry={expiry}"

