import pandas as pd
from datetime import datetime
import threading
import pytz


class AppState:
    def __init__(self):
        # State
        self.state = 'IDLE'  # IDLE, LOGGING_IN, WAITING_FOR_OTP, SCRAPING, ERROR, STOPPED
        
        # Multi-symbol data structure
        self.symbols = {}  # {'NIFTY': {df, df_roc, underlying_price, url, last_scrape_time}, ...}
        self.active_symbols = []  # ['NIFTY', 'RELIANCE']
        self.equity_symbol = None
        self.equity_expiry = None
        self.nifty_expiry = None
        
        # Legacy single-symbol support (for backward compatibility during transition)
        self.df = None
        self.df_roc = pd.DataFrame()
        self.nifty_futures = None
        
        # Metadata
        self.counter = 0
        self.last_update = None
        
        # Resources
        self.driver = None
        self.scraping_thread = None
        self.should_stop = False
        
        # Logs
        self.logs = []
        self.error_message = None
        
        # Thread lock for thread-safe operations (RLock allows reentrant locking)
        self.lock = threading.RLock()
    
    def add_log(self, message):
        with self.lock:
            IST = pytz.timezone('Asia/Kolkata')
            timestamp = datetime.now(IST).strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}"
            self.logs.append(log_entry)
            print(log_entry)
            
            # Keep only last 50 logs to avoid memory issues
            if len(self.logs) > 50:
                self.logs = self.logs[-50:]
    
    def set_state(self, new_state):
        with self.lock:
            self.state = new_state
            self.add_log(f"State changed to: {new_state}")
    
    def set_error(self, error_message):
        with self.lock:
            self.state = 'ERROR'
            self.error_message = error_message
            self.add_log(f"ERROR: {error_message}")
    
    def reset(self):
        with self.lock:
            self.state = 'IDLE'
            # Reset multi-symbol data
            self.symbols = {}
            self.active_symbols = []
            self.equity_symbol = None
            self.equity_expiry = None
            self.nifty_expiry = None
            # Reset legacy data
            self.df = None
            self.df_roc = pd.DataFrame()
            self.nifty_futures = None
            self.counter = 0
            self.last_update = None
            self.should_stop = False
            self.error_message = None
            self.add_log("State reset to IDLE")
            
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
    
    def add_symbol(self, symbol, url):
        """Initialize data structure for a symbol"""
        with self.lock:
            self.symbols[symbol] = {
                'df': None,  # Working dataframe (gets updated for ROC calculations)
                'df_reference': None,  # Static reference data from t0 (never changes)
                'df_roc': pd.DataFrame(),
                'underlying_price': None,
                'url': url,
                'last_scrape_time': None
            }
            if symbol not in self.active_symbols:
                self.active_symbols.append(symbol)
            self.add_log(f"Symbol {symbol} added for tracking")
    
    def remove_symbol(self, symbol):
        """Remove a symbol from tracking"""
        with self.lock:
            if symbol in self.symbols:
                del self.symbols[symbol]
            if symbol in self.active_symbols:
                self.active_symbols.remove(symbol)
            self.add_log(f"Symbol {symbol} removed from tracking")
    
    def get_status(self):
        with self.lock:
            return {
                'state': self.state,
                'counter': self.counter,
                'last_update': self.last_update.strftime("%d/%m/%Y %H:%M:%S") if self.last_update else None,
                'error_message': self.error_message,
                'logs': self.logs[-10:]  # Return last 10 logs
            }
    
    def get_roc_data(self):
        with self.lock:
            if self.df_roc.empty:
                return None
            # Convert to dict first, then clean NaN/Inf values
            records = self.df_roc.to_dict('records')
            # Clean each record to replace NaN and Infinity with None
            cleaned_records = []
            for record in records:
                cleaned = {}
                for key, value in record.items():
                    if pd.isna(value) or value == float('inf') or value == float('-inf'):
                        cleaned[key] = None
                    elif key == 'Time (ROC)' and pd.notna(value):
                        # Format time as HH:MM:SS only
                        cleaned[key] = pd.to_datetime(value).strftime("%H:%M:%S")
                    else:
                        cleaned[key] = value
                cleaned_records.append(cleaned)
            return cleaned_records
    
    def get_reference_data(self):
        with self.lock:
            if self.df is None:
                return None
            
            # Prepare reference data with renamed columns
            reference_data = self.df.copy()
            reference_data = reference_data.rename(columns={
                "volume_calls": "Volume (Calls)",
                "oi_lakhs_calls": "OI Lakhs (Calls)",
                "ltp_calls": "LTP (Calls)",
                "strike_price": "Strike Price",
                "iv": "IV",
                "ltp_puts": "LTP (Puts)",
                "oi_lakh_puts": "OI Lakhs (Puts)",
                "volume_puts": "Volume (Puts)",
                "time": "Time (t0)" 
            })
            
            reference_data['Remarks (Calls)'] = 'NA'
            reference_data['Remarks (Puts)'] = 'NA'
            reference_data['COI/VOL (Calls)'] = reference_data['OI Lakhs (Calls)'] / reference_data['Volume (Calls)']
            reference_data['COI/VOL (Puts)'] = reference_data['OI Lakhs (Puts)'] / reference_data['Volume (Puts)']
            
            reference_data = reference_data.reindex(columns=[
                'Remarks (Calls)', 'Volume (Calls)', 'OI Lakhs (Calls)', 'LTP (Calls)', 'IV', 'COI/VOL (Calls)',
                'Strike Price', 'COI/VOL (Puts)', 'LTP (Puts)', 'OI Lakhs (Puts)', 'Volume (Puts)', 'Remarks (Puts)', 'Time (t0)'
            ])
            
            # Convert to dict first, then clean NaN/Inf values
            records = reference_data.to_dict('records')
            # Clean each record to replace NaN and Infinity with None
            cleaned_records = []
            for record in records:
                cleaned = {}
                for key, value in record.items():
                    if pd.isna(value) or value == float('inf') or value == float('-inf'):
                        cleaned[key] = None
                    elif key == 'Time (t0)' and pd.notna(value):
                        # Format time as HH:MM:SS only
                        cleaned[key] = pd.to_datetime(value).strftime("%H:%M:%S")
                    else:
                        cleaned[key] = value
                cleaned_records.append(cleaned)
            
            return cleaned_records
    
    def get_symbol_roc_data(self, symbol):
        """Get ROC data for a specific symbol"""
        with self.lock:
            if symbol not in self.symbols or self.symbols[symbol]['df_roc'].empty:
                return None
            
            df_roc = self.symbols[symbol]['df_roc']
            records = df_roc.to_dict('records')
            
            # Clean each record to replace NaN and Infinity with None
            cleaned_records = []
            for record in records:
                cleaned = {}
                for key, value in record.items():
                    if pd.isna(value) or value == float('inf') or value == float('-inf'):
                        cleaned[key] = None
                    elif key == 'Time (ROC)' and pd.notna(value):
                        # Format time as HH:MM:SS only
                        cleaned[key] = pd.to_datetime(value).strftime("%H:%M:%S")
                    else:
                        cleaned[key] = value
                cleaned_records.append(cleaned)
            return cleaned_records
    
    def get_symbol_reference_data(self, symbol):
        """Get reference data for a specific symbol"""
        with self.lock:
            if symbol not in self.symbols or self.symbols[symbol]['df_reference'] is None:
                return None
            
            reference_data = self.symbols[symbol]['df_reference'].copy()
            reference_data = reference_data.rename(columns={
                "volume_calls": "Volume (Calls)",
                "oi_lakhs_calls": "OI Lakhs (Calls)",
                "ltp_calls": "LTP (Calls)",
                "strike_price": "Strike Price",
                "iv": "IV",
                "ltp_puts": "LTP (Puts)",
                "oi_lakh_puts": "OI Lakhs (Puts)",
                "volume_puts": "Volume (Puts)",
                "time": "Time (t0)" 
            })
            
            reference_data['Remarks (Calls)'] = 'NA'
            reference_data['Remarks (Puts)'] = 'NA'
            reference_data['COI/VOL (Calls)'] = reference_data['OI Lakhs (Calls)'] / reference_data['Volume (Calls)']
            reference_data['COI/VOL (Puts)'] = reference_data['OI Lakhs (Puts)'] / reference_data['Volume (Puts)']
            
            reference_data = reference_data.reindex(columns=[
                'Remarks (Calls)', 'Volume (Calls)', 'OI Lakhs (Calls)', 'LTP (Calls)', 'IV', 'COI/VOL (Calls)',
                'Strike Price', 'COI/VOL (Puts)', 'LTP (Puts)', 'OI Lakhs (Puts)', 'Volume (Puts)', 'Remarks (Puts)', 'Time (t0)'
            ])
            
            records = reference_data.to_dict('records')
            cleaned_records = []
            for record in records:
                cleaned = {}
                for key, value in record.items():
                    if pd.isna(value) or value == float('inf') or value == float('-inf'):
                        cleaned[key] = None
                    elif key == 'Time (t0)' and pd.notna(value):
                        # Format time as HH:MM:SS only
                        cleaned[key] = pd.to_datetime(value).strftime("%H:%M:%S")
                    else:
                        cleaned[key] = value
                cleaned_records.append(cleaned)
            
            return cleaned_records


# Global app state instance
app_state = AppState()

