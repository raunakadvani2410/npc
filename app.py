from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import threading
import time
import os
import sys
import yfinance as yf

# Load environment variables from .env file
load_dotenv()
import pandas as pd
from datetime import datetime, time as dt_time
import pytz
from pyvirtualdisplay import Display

from services.data_store import app_state
from services.scraper import enter_webpage, login, submit_otp, find_and_return_table, navigate_to_symbol
from services.data_processor import build_dataframe, slice_df, calculate_roc
from config import SENSIBULL_URL, NIFTY_TICKER, INITIAL_WAIT_SECONDS, SCRAPING_INTERVAL_SECONDS, build_sensibull_url, DEFAULT_NIFTY_EXPIRY

app = Flask(__name__)

# Virtual display for headless Selenium
display = None


def is_time_between(begin_time, end_time, check_time=None):
    if check_time is None:
        IST = pytz.timezone('Asia/Kolkata') 
        check_time = datetime.now(IST).time()
    
    is_between = begin_time <= check_time <= end_time
    
    if not is_between:
        app_state.add_log("Outside trading hours")
    
    return is_between


def scraping_loop():
    global display
    
    try:
        # Start virtual display
        app_state.add_log("Starting virtual display")
        display = Display(visible=0, size=(3840, 2160))
        display.start()
        
        # State: LOGGING_IN
        app_state.set_state('LOGGING_IN')
        app_state.add_log("Entering Sensibull webpage")
        
        # Use NIFTY URL for initial login (will navigate to other symbols later)
        initial_url = build_sensibull_url('NIFTY', app_state.nifty_expiry or DEFAULT_NIFTY_EXPIRY)
        app_state.driver = enter_webpage(initial_url)
        
        app_state.add_log("Entering login credentials")
        app_state.driver = login(app_state.driver)
        
        # State: WAITING_FOR_OTP
        app_state.set_state('WAITING_FOR_OTP')
        app_state.add_log("OTP sent, waiting for user to submit OTP")
        
        # Wait for OTP to be submitted (blocking)
        while app_state.state == 'WAITING_FOR_OTP' and not app_state.should_stop:
            time.sleep(1)
        
        # Check if stop was requested during OTP wait
        if app_state.should_stop:
            app_state.add_log("Scraping stopped by user during OTP wait")
            cleanup()
            return
        
        # OTP has been submitted, wait for login to complete
        app_state.add_log("OTP submitted, waiting for login to complete")
        time.sleep(15)
        
        # Initialize symbols
        app_state.add_log("Initializing symbol tracking")
        
        # Always add NIFTY
        nifty_url = build_sensibull_url('NIFTY', app_state.nifty_expiry or DEFAULT_NIFTY_EXPIRY)
        app_state.add_symbol('NIFTY', nifty_url)
        
        # Add equity symbol if provided
        if app_state.equity_symbol and app_state.equity_expiry:
            equity_url = build_sensibull_url(app_state.equity_symbol, app_state.equity_expiry)
            app_state.add_symbol(app_state.equity_symbol, equity_url)
        
        # Get initial data for all symbols
        app_state.add_log("Fetching initial data for all symbols")
        
        for symbol in app_state.active_symbols:
            try:
                symbol_data = app_state.symbols[symbol]
                
                # Navigate to symbol's page
                app_state.driver = navigate_to_symbol(app_state.driver, symbol_data['url'])
                
                # Get underlying price
                if symbol == 'NIFTY':
                    ticker = yf.Ticker(NIFTY_TICKER)
                    underlying_price = ticker.history(period="1d")['Close'].iloc[-1]
                else:
                    # For equity, construct ticker symbol (NSE: symbol.NS)
                    ticker = yf.Ticker(f"{symbol}.NS")
                    underlying_price = ticker.history(period="1d")['Close'].iloc[-1]
                
                app_state.symbols[symbol]['underlying_price'] = underlying_price
                app_state.add_log(f"{symbol} price: {underlying_price}")
                
                # Scrape table
                app_state.driver, data_list = find_and_return_table(app_state.driver)
                df = build_dataframe(data_list)
                df = slice_df(df, underlying_price)
                
                # Store as both reference (static) and working data
                app_state.symbols[symbol]['df_reference'] = df.copy()  # Static reference, never changes
                app_state.symbols[symbol]['df'] = df  # Working data for ROC calculations
                app_state.add_log(f"Initial data for {symbol} fetched successfully")
                
            except Exception as e:
                app_state.add_log(f"Error initializing {symbol}: {e}")
                # Continue with other symbols even if one fails
                continue
        
        app_state.add_log(f"Waiting {INITIAL_WAIT_SECONDS} seconds before first update")
        time.sleep(INITIAL_WAIT_SECONDS)
        
        # State: SCRAPING
        app_state.set_state('SCRAPING')
        
        # Main scraping loop - sequential scraping of all symbols
        while not app_state.should_stop and is_time_between(dt_time(2, 50), dt_time(15, 30)):
            for symbol in app_state.active_symbols:
                if app_state.should_stop:
                    break
                
                try:
                    app_state.add_log(f"Fetching update for {symbol}")
                    
                    # Navigate to symbol
                    app_state.driver = navigate_to_symbol(app_state.driver, app_state.symbols[symbol]['url'])
                    
                    # Scrape data
                    app_state.driver, data_list = find_and_return_table(app_state.driver)
                    df_new = build_dataframe(data_list)
                    df_new = slice_df(df_new, app_state.symbols[symbol]['underlying_price'])
                    
                    # Calculate ROC
                    df_old = app_state.symbols[symbol]['df']
                    all_data = pd.concat([df_old, df_new], ignore_index=True)
                    changes = calculate_roc(all_data)
                    
                    # Update state (prepend new data)
                    with app_state.lock:
                        app_state.symbols[symbol]['df_roc'] = pd.concat([changes, app_state.symbols[symbol]['df_roc']], ignore_index=True)
                        app_state.symbols[symbol]['df_roc'] = app_state.symbols[symbol]['df_roc'].sort_values(['Strike Price', 'Time (ROC)'], ascending=[True, False])
                        app_state.symbols[symbol]['last_scrape_time'] = datetime.now()
                        
                        # Remove old data from df (keep only last 2 time periods)
                        unique_times = all_data['time'].unique()
                        if len(unique_times) > 1:
                            earlier_time = min(unique_times)
                            all_data = all_data[all_data['time'] != earlier_time]
                        app_state.symbols[symbol]['df'] = all_data
                    
                    app_state.counter += 1
                    app_state.last_update = datetime.now()
                    app_state.add_log(f"Update for {symbol} completed (total updates: {app_state.counter})")
                    
                except Exception as e:
                    app_state.add_log(f"Error scraping {symbol}: {str(e)}")
                    # Continue with next symbol instead of stopping entirely
                    continue
            
            # Wait before next cycle
            if not app_state.should_stop:
                time.sleep(SCRAPING_INTERVAL_SECONDS)
        
        # Exited loop - either stopped or outside trading hours
        if app_state.should_stop:
            app_state.add_log("Scraping stopped by user")
        else:
            app_state.add_log("Outside trading hours, stopping scraping")
        
        cleanup()
        
    except Exception as e:
        error_msg = f"Fatal error in scraping loop: {str(e)}"
        app_state.set_error(error_msg)
        cleanup()


def cleanup():
    global display
    
    app_state.add_log("Cleaning up resources")
    
    if app_state.driver:
        try:
            app_state.driver.quit()
            app_state.add_log("Browser closed")
        except Exception as e:
            app_state.add_log(f"Error closing browser: {e}")
        app_state.driver = None
    
    if display:
        try:
            display.stop()
            app_state.add_log("Virtual display stopped")
        except Exception as e:
            app_state.add_log(f"Error stopping display: {e}")
        display = None
    
    # Reset should_stop flag for next run
    app_state.should_stop = False
    
    if app_state.state not in ['ERROR', 'STOPPED']:
        app_state.set_state('STOPPED')


@app.route('/')
def home():
    return render_template('dashboard.html')


@app.route('/api/start', methods=['POST'])
def start_scraping():
    if app_state.state not in ['IDLE', 'ERROR', 'STOPPED']:
        return jsonify({'error': f'Cannot start: current state is {app_state.state}'}), 400
    
    # Reset state if coming from ERROR or STOPPED
    if app_state.state in ['ERROR', 'STOPPED']:
        app_state.reset()
    
    # Get symbol configuration from request
    data = request.get_json() or {}
    equity_symbol = data.get('equity_symbol', '').strip().upper()
    equity_expiry = data.get('equity_expiry', '').strip()
    nifty_expiry = data.get('nifty_expiry', DEFAULT_NIFTY_EXPIRY)
    
    # Store in app_state
    app_state.equity_symbol = equity_symbol if equity_symbol else None
    app_state.equity_expiry = equity_expiry if equity_expiry else None
    app_state.nifty_expiry = nifty_expiry
    
    app_state.add_log("Start button clicked")
    if equity_symbol and equity_expiry:
        app_state.add_log(f"Tracking NIFTY (expiry: {nifty_expiry}) and {equity_symbol} (expiry: {equity_expiry})")
    else:
        app_state.add_log(f"Tracking NIFTY only (expiry: {nifty_expiry})")
    
    # Start scraping in background thread
    app_state.scraping_thread = threading.Thread(target=scraping_loop, daemon=True)
    app_state.scraping_thread.start()
    
    return jsonify({'status': 'started'})


@app.route('/api/stop', methods=['POST'])
def stop_scraping():
    if app_state.state not in ['LOGGING_IN', 'WAITING_FOR_OTP', 'OTP_SUBMITTED', 'SCRAPING']:
        return jsonify({'error': f'Cannot stop: current state is {app_state.state}'}), 400
    
    app_state.add_log("Stop button clicked")
    app_state.should_stop = True
    
    # Wait for thread to finish (with timeout)
    if app_state.scraping_thread:
        app_state.scraping_thread.join(timeout=5)
    
    app_state.reset()
    
    return jsonify({'status': 'stopped'})


@app.route('/api/reset', methods=['POST'])
def reset_state():
    """Force reset the app state - useful if app is stuck"""
    app_state.add_log("Force reset requested")
    
    # Try to stop any running thread
    if app_state.scraping_thread and app_state.scraping_thread.is_alive():
        app_state.should_stop = True
        app_state.scraping_thread.join(timeout=3)
    
    # Force cleanup
    try:
        cleanup()
    except:
        pass
    
    # Reset state
    app_state.reset()
    
    return jsonify({'status': 'reset_complete'})


@app.route('/api/submit_otp', methods=['POST'])
def submit_otp_api():
    if app_state.state != 'WAITING_FOR_OTP':
        return jsonify({'error': f'Not waiting for OTP. Current state: {app_state.state}'}), 400
    
    data = request.get_json()
    otp = data.get('otp')
    
    if not otp:
        return jsonify({'error': 'OTP is required'}), 400
    
    app_state.add_log(f"OTP received: {otp}")
    
    try:
        app_state.driver = submit_otp(app_state.driver, otp)
        app_state.add_log("OTP submitted successfully to Zerodha")
        
        # Change state to signal the scraping loop to continue
        app_state.set_state('OTP_SUBMITTED')
        
        return jsonify({'status': 'otp_submitted'})
    except Exception as e:
        error_msg = f"Failed to submit OTP: {str(e)}"
        app_state.set_error(error_msg)
        return jsonify({'error': error_msg}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(app_state.get_status())


@app.route('/api/symbols', methods=['GET'])
def get_active_symbols():
    """Return list of active symbols being tracked"""
    return jsonify({'symbols': app_state.active_symbols})


@app.route('/api/roc/<symbol>', methods=['GET'])
def get_roc(symbol):
    """Get ROC data for a specific symbol"""
    symbol = symbol.upper()
    data = app_state.get_symbol_roc_data(symbol)
    if data is None:
        return jsonify([])
    return jsonify(data)


@app.route('/api/reference/<symbol>', methods=['GET'])
def get_reference(symbol):
    """Get reference data for a specific symbol"""
    symbol = symbol.upper()
    data = app_state.get_symbol_reference_data(symbol)
    if data is None:
        return jsonify([])
    return jsonify(data)


# Legacy endpoints for backward compatibility (default to NIFTY)
@app.route('/api/roc', methods=['GET'])
def get_roc_legacy():
    data = app_state.get_symbol_roc_data('NIFTY') if 'NIFTY' in app_state.active_symbols else app_state.get_roc_data()
    if data is None:
        return jsonify([])
    return jsonify(data)


@app.route('/api/reference', methods=['GET'])
def get_reference_legacy():
    data = app_state.get_symbol_reference_data('NIFTY') if 'NIFTY' in app_state.active_symbols else app_state.get_reference_data()
    if data is None:
        return jsonify([])
    return jsonify(data)


if __name__ == '__main__':
    try:
        print("Flask app starting...", flush=True)
        sys.stdout.flush()
        
        # Reset app state on startup
        app_state.reset()
        app_state.add_log("Flask app started")
        
        # Disable debug mode in production (set via environment variable)
        debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        print(f"Starting Flask on port 8501 (debug={debug_mode})", flush=True)
        sys.stdout.flush()
        
        app.run(debug=debug_mode, host='0.0.0.0', port=8501, threaded=True, use_reloader=False)
    except KeyboardInterrupt:
        print("Flask app stopped by user", flush=True)
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.stderr.flush()
        sys.exit(1)

