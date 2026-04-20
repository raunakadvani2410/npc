import os

# Zerodha credentials
ZERODHA_USER_ID = os.getenv('ZERODHA_USER_ID')
ZERODHA_PASSWORD = os.getenv('ZERODHA_PASSWORD')

# Trading hours (IST)
TRADING_START_HOUR = 9
TRADING_START_MINUTE = 15
TRADING_END_HOUR = 15
TRADING_END_MINUTE = 30

# Scraping intervals
INITIAL_WAIT_SECONDS = 23
SCRAPING_INTERVAL_SECONDS = 23

# Nifty options
SENSIBULL_URL = 'https://web.sensibull.com/option-chain?tradingsymbol=NIFTY'

# Strike price configuration
STRIKE_RANGE = 4  # How many strikes above and below central strike
STRIKE_INTERVAL = 100  # Strike price intervals

# Chrome driver path
CHROMEDRIVER_PATH = './chromedriver'

