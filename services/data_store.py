import pandas as pd
import numpy as np
import json
import os
import math
from datetime import datetime
import threading


class AppState:
    def __init__(self):
        # State
        self.state = 'IDLE'  # IDLE, LOGGING_IN, WAITING_FOR_OTP, SCRAPING, ERROR, STOPPED
        
        # Data
        self.df = None
        self.df_latest = None
        self.df_previous = None       # t-1 snapshot for LTP change calculations
        self.df_prev_close = None     # Previous trading day's 3:40 PM data (loaded from file)
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
            self.df_latest = None
            self.df_previous = None
            self.df_roc = pd.DataFrame()
            self.nifty_futures = None
            self.counter = 0
            self.last_update = None
            self.should_stop = False
            self.error_message = None
            # df_prev_close intentionally NOT reset — it persists from the file
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
    
    def get_raw_data(self):
        """Return the latest scraped data in the same format as reference data"""
        with self.lock:
            source_df = self.df_latest if self.df_latest is not None else self.df
            if source_df is None:
                return None
            
            raw_data = source_df.copy()
            raw_data = raw_data.rename(columns={
                "volume_calls": "Volume (Calls)",
                "oi_lakhs_calls": "OI Lakhs (Calls)",
                "ltp_calls": "LTP (Calls)",
                "strike_price": "Strike Price",
                "iv": "IV",
                "ltp_puts": "LTP (Puts)",
                "oi_lakh_puts": "OI Lakhs (Puts)",
                "volume_puts": "Volume (Puts)",
                "time": "Time"
            })
            
            raw_data['Remarks (Calls)'] = 'NA'
            raw_data['Remarks (Puts)'] = 'NA'
            raw_data['COI/VOL (Calls)'] = raw_data['OI Lakhs (Calls)'] / raw_data['Volume (Calls)']
            raw_data['COI/VOL (Puts)'] = raw_data['OI Lakhs (Puts)'] / raw_data['Volume (Puts)']
            
            raw_data = raw_data.reindex(columns=[
                'Remarks (Calls)', 'Volume (Calls)', 'OI Lakhs (Calls)', 'LTP (Calls)', 'IV', 'COI/VOL (Calls)',
                'Strike Price', 'COI/VOL (Puts)', 'LTP (Puts)', 'OI Lakhs (Puts)', 'Volume (Puts)', 'Remarks (Puts)', 'Time'
            ])
            
            records = raw_data.to_dict('records')
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
        """Find the three strikes with highest OI and whether each is a call or put"""
        with self.lock:
            source_df = self.df_latest if self.df_latest is not None else self.df
            if source_df is None:
                return None
            
            candidates = []
            for _, row in source_df.iterrows():
                strike = int(row['strike_price'])
                candidates.append({'strike': strike, 'type': 'call', 'oi_value': float(row['oi_lakhs_calls'])})
                candidates.append({'strike': strike, 'type': 'put', 'oi_value': float(row['oi_lakh_puts'])})
            
            candidates.sort(key=lambda c: c['oi_value'], reverse=True)
            
            if not candidates:
                return None
            
            first = candidates[0]
            result = {'strike': first['strike'], 'type': first['type'], 'oi_value': first['oi_value']}
            
            if len(candidates) >= 2:
                second = candidates[1]
                result['second_strike'] = second['strike']
                result['second_type'] = second['type']
                result['second_oi_value'] = second['oi_value']
            
            if len(candidates) >= 3:
                third = candidates[2]
                result['third_strike'] = third['strike']
                result['third_type'] = third['type']
                result['third_oi_value'] = third['oi_value']
            
            return result

    def load_prev_close(self):
        from config import PREV_CLOSE_FILE
        with self.lock:
            try:
                with open(PREV_CLOSE_FILE, 'r') as f:
                    records = json.load(f)
                self.df_prev_close = pd.DataFrame(records)
                self.add_log(f"Loaded previous day's close data ({len(records)} rows)")
            except FileNotFoundError:
                self.df_prev_close = None
                self.add_log("No previous day's close data file found")
            except Exception as e:
                self.df_prev_close = None
                self.add_log(f"Error loading previous day's close: {e}")

    def save_prev_close(self):
        from config import PREV_CLOSE_FILE
        with self.lock:
            source_df = self.df_latest if self.df_latest is not None else self.df
            if source_df is None:
                return
            records = source_df.to_dict('records')
            cleaned = []
            for r in records:
                cleaned.append({
                    k: (float(v) if isinstance(v, (np.floating, np.integer)) else v)
                    for k, v in r.items()
                })
            try:
                with open(PREV_CLOSE_FILE, 'w') as f:
                    json.dump(cleaned, f, indent=2)
                self.add_log("Saved previous day's close data to file")
            except Exception as e:
                self.add_log(f"Error saving previous day's close: {e}")

    def get_prev_close_data(self):
        with self.lock:
            if self.df_prev_close is None:
                return None

            prev_close = self.df_prev_close.copy()
            prev_close = prev_close.rename(columns={
                "volume_calls": "Volume (Calls)",
                "oi_lakhs_calls": "OI Lakhs (Calls)",
                "ltp_calls": "LTP (Calls)",
                "strike_price": "Strike Price",
                "iv": "IV",
                "ltp_puts": "LTP (Puts)",
                "oi_lakh_puts": "OI Lakhs (Puts)",
                "volume_puts": "Volume (Puts)",
                "time": "Time (Prev Close)"
            })

            prev_close['Remarks (Calls)'] = 'NA'
            prev_close['Remarks (Puts)'] = 'NA'
            prev_close['COI/VOL (Calls)'] = prev_close['OI Lakhs (Calls)'] / prev_close['Volume (Calls)']
            prev_close['COI/VOL (Puts)'] = prev_close['OI Lakhs (Puts)'] / prev_close['Volume (Puts)']

            prev_close = prev_close.reindex(columns=[
                'Remarks (Calls)', 'Volume (Calls)', 'OI Lakhs (Calls)', 'LTP (Calls)', 'IV', 'COI/VOL (Calls)',
                'Strike Price', 'COI/VOL (Puts)', 'LTP (Puts)', 'OI Lakhs (Puts)', 'Volume (Puts)', 'Remarks (Puts)',
                'Time (Prev Close)'
            ])

            records = prev_close.to_dict('records')
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

    def get_top3_oi_summary(self):
        """Aggregate OI and LTP change across both sides of the top-3 strike prices by OI."""
        with self.lock:
            source_df = self.df_latest if self.df_latest is not None else self.df
            prev_df = self.df_previous
            if source_df is None:
                return None

            # Rank at the strike level: highest single-side OI determines the strike's rank
            strike_data = []
            for _, row in source_df.iterrows():
                strike = int(row['strike_price'])
                call_oi = float(row['oi_lakhs_calls'])
                put_oi = float(row['oi_lakh_puts'])
                call_oi = call_oi if not math.isnan(call_oi) else 0
                put_oi = put_oi if not math.isnan(put_oi) else 0
                strike_data.append({
                    'strike': strike,
                    'rank_oi': max(call_oi, put_oi),
                    'call_oi': call_oi,
                    'put_oi': put_oi,
                    'call_ltp': float(row['ltp_calls']),
                    'put_ltp': float(row['ltp_puts'])
                })

            strike_data.sort(key=lambda s: s['rank_oi'], reverse=True)
            top3 = strike_data[:3]

            if not top3:
                return None

            total_call_oi = sum(s['call_oi'] for s in top3)
            total_put_oi = sum(s['put_oi'] for s in top3)

            avg_call_ltp_change = None
            avg_put_ltp_change = None

            if prev_df is not None:
                call_changes = []
                put_changes = []
                for s in top3:
                    prev_row = prev_df[prev_df['strike_price'] == s['strike']]
                    if not prev_row.empty:
                        prev_call_ltp = float(prev_row['ltp_calls'].iloc[0])
                        if prev_call_ltp != 0 and not math.isnan(prev_call_ltp):
                            call_changes.append(
                                ((s['call_ltp'] - prev_call_ltp) / prev_call_ltp) * 100
                            )
                        prev_put_ltp = float(prev_row['ltp_puts'].iloc[0])
                        if prev_put_ltp != 0 and not math.isnan(prev_put_ltp):
                            put_changes.append(
                                ((s['put_ltp'] - prev_put_ltp) / prev_put_ltp) * 100
                            )
                if call_changes:
                    avg_call_ltp_change = round(sum(call_changes) / len(call_changes), 2)
                if put_changes:
                    avg_put_ltp_change = round(sum(put_changes) / len(put_changes), 2)

            return {
                'top3': [
                    {
                        'strike': s['strike'],
                        'call_oi': round(s['call_oi'], 2),
                        'put_oi': round(s['put_oi'], 2)
                    }
                    for s in top3
                ],
                'total_call_oi': round(total_call_oi, 2),
                'total_put_oi': round(total_put_oi, 2),
                'avg_call_ltp_change': avg_call_ltp_change,
                'avg_put_ltp_change': avg_put_ltp_change
            }


# Global app state instance
app_state = AppState()

