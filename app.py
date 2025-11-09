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
from services.scraper import enter_webpage, login, submit_otp, find_and_return_table, find_and_return_table_no_button
from services.data_processor import build_dataframe, slice_df, calculate_roc
from config import SENSIBULL_URL, NIFTY_TICKER, INITIAL_WAIT_SECONDS, SCRAPING_INTERVAL_SECONDS

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
        app_state.driver = enter_webpage(SENSIBULL_URL)
        
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
        
        # Get initial data
        app_state.add_log("Fetching initial data")
        
        # Get Nifty futures value
        nifty = yf.Ticker(NIFTY_TICKER)
        app_state.nifty_futures = nifty.history(period="1d")['Close'].iloc[-1]
        app_state.add_log(f"Nifty futures: {app_state.nifty_futures}")
        
        app_state.driver, data_list = find_and_return_table(app_state.driver)
        app_state.df = build_dataframe(data_list)
        app_state.df = slice_df(app_state.df, app_state.nifty_futures)
        
        app_state.add_log("Initial data fetched successfully")
        app_state.add_log(f"Waiting {INITIAL_WAIT_SECONDS} seconds before first update")
        time.sleep(INITIAL_WAIT_SECONDS)
        
        # State: SCRAPING
        app_state.set_state('SCRAPING')
        
        # Main scraping loop
        while not app_state.should_stop and is_time_between(dt_time(2, 50), dt_time(15, 30)):
            try:
                app_state.add_log(f"Fetching update #{app_state.counter + 1}")
                
                # Get new data
                app_state.driver, data_list = find_and_return_table_no_button(app_state.driver)
                df_1 = build_dataframe(data_list)
                df_1 = slice_df(df_1, app_state.nifty_futures)
                
                # Calculate ROC
                all_data = pd.concat([app_state.df, df_1], ignore_index=True)
                changes = calculate_roc(all_data)
                
                # Update df_roc (prepend new data so most recent is at top)
                with app_state.lock:
                    app_state.df_roc = pd.concat([changes, app_state.df_roc], ignore_index=True)
                    app_state.df_roc = app_state.df_roc.sort_values(['Strike Price', 'Time (ROC)'], ascending=[True, False])
                    app_state.counter += 1
                    app_state.last_update = datetime.now()
                
                app_state.add_log(f"Update #{app_state.counter} completed successfully")
                
                # Remove earlier time data
                unique_times = all_data['time'].unique()
                earlier_time = min(unique_times)
                all_data = all_data[all_data['time'] != earlier_time]
                
                # Save to CSV (optional)
                try:
                    app_state.df_roc.to_csv("rates_of_change.csv", index=False)
                except Exception as e:
                    app_state.add_log(f"Warning: Failed to save CSV: {e}")
                
                # Wait before next update
                time.sleep(SCRAPING_INTERVAL_SECONDS)
                
            except Exception as e:
                error_msg = f"Error during scraping iteration: {str(e)}"
                app_state.set_error(error_msg)
                cleanup()
                return
        
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
    
    app_state.add_log("Start button clicked")
    
    # Start scraping in background thread
    app_state.scraping_thread = threading.Thread(target=scraping_loop, daemon=True)
    app_state.scraping_thread.start()
    
    return jsonify({'status': 'started'})


@app.route('/api/stop', methods=['POST'])
def stop_scraping():
    if app_state.state not in ['LOGGING_IN', 'WAITING_FOR_OTP', 'SCRAPING']:
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
        return jsonify({'status': 'otp_submitted'})
    except Exception as e:
        error_msg = f"Failed to submit OTP: {str(e)}"
        app_state.set_error(error_msg)
        return jsonify({'error': error_msg}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(app_state.get_status())


@app.route('/api/roc', methods=['GET'])
def get_roc():
    data = app_state.get_roc_data()
    if data is None:
        return jsonify([])
    return jsonify(data)


@app.route('/api/reference', methods=['GET'])
def get_reference():
    data = app_state.get_reference_data()
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

