import pandas as pd
from datetime import datetime
import threading


class AppState:
    def __init__(self):
        # State
        self.state = 'IDLE'  # IDLE, LOGGING_IN, WAITING_FOR_OTP, SCRAPING, ERROR, STOPPED
        
        # Data
        self.df = None
        self.df_roc = pd.DataFrame()
        self.nifty_futures = None
        
        # Configuration
        self.sensibull_url = None
        
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
            timestamp = datetime.now().strftime("%H:%M:%S")
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
                        # Format time consistently as DD/MM/YYYY HH:MM:SS
                        cleaned[key] = pd.to_datetime(value).strftime("%d/%m/%Y %H:%M:%S")
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
                    else:
                        cleaned[key] = value
                cleaned_records.append(cleaned)
            
            return cleaned_records
    
    def get_highest_oi_strike(self):
        """Find strike price with highest OI and whether it's call or put"""
        with self.lock:
            if self.df is None:
                return None
            
            max_oi = -1
            result = {'strike': None, 'type': None}
            
            for _, row in self.df.iterrows():
                strike = row['strike_price']
                call_oi = row['oi_lakhs_calls']
                put_oi = row['oi_lakh_puts']
                
                if call_oi > max_oi:
                    max_oi = call_oi
                    result = {'strike': int(strike), 'type': 'call'}
                
                if put_oi > max_oi:
                    max_oi = put_oi
                    result = {'strike': int(strike), 'type': 'put'}
            
            return result if result['strike'] is not None else None


# Global app state instance
app_state = AppState()

