import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from config import STRIKE_RANGE, STRIKE_INTERVAL


def build_dataframe(data_list):
    IST = pytz.timezone('Asia/Kolkata') 
    dt_string = datetime.now(IST).strftime("%d/%m/%Y %H:%M:%S")

    # Reshape the data into rows of 27 elements
    rows = [data_list[i:i+27] for i in range(0, len(data_list), 27)]

    columns = {       
        'volume_calls': 2,
        'oi_change_calls': 3,
        'oi_change_pct_calls': 4,
        'oi_lakhs_calls': 5,
        'ltp_calls': 10,
        'strike_price': 12,
        'iv': 13,
        'ltp_puts': 15,
        'oi_lakh_puts': 21,
        'oi_change_pct_puts': 22,
        'oi_change_puts': 23,
        'volume_puts': 24,
    }

    df_data = []

    for i, row in enumerate(rows):
        df_row = {}
        for column, index in columns.items():
            try:
                if index < len(row):
                    value = row[index].replace('%', '')

                    if column == 'strike_price':
                        df_row[column] = int(float(value))  
                    else:
                        df_row[column] = float(value)
                else:
                    print(f"  {column} (index {index}): INDEX OUT OF RANGE (row length: {len(row)})")
                    df_row[column] = np.nan
            except (ValueError, IndexError) as e:
                print(f"  {column} (index {index}): ERROR - {e}")
                df_row[column] = np.nan

        df_row['time'] = dt_string
        df_data.append(df_row)

    df = pd.DataFrame(df_data)
    return df


def slice_df(df, nifty_futures):
    central_strike = round(nifty_futures / 100) * 100
    strike_prices_to_keep = [central_strike + i * STRIKE_INTERVAL for i in range(-STRIKE_RANGE, STRIKE_RANGE)]
    df = df[df['strike_price'].isin(strike_prices_to_keep)]
    df = df.reset_index(drop=True)
    return df


def get_remarks_calls(row):
    if row['OI Lakhs (Calls)'] < 0 and row['LTP (Calls)'] > 0:
        return "Short Covering"
    elif row['OI Lakhs (Calls)'] > 0 and row['LTP (Calls)'] < 0:
        return "Short Buildup"
    elif row['OI Lakhs (Calls)'] < 0 and row['LTP (Calls)'] < 0:
        return "Long Unwinding"
    elif row['OI Lakhs (Calls)'] > 0 and row['LTP (Calls)'] > 0:
        return "Long Buildup"
    else:
        return "NA"
    

def get_remarks_puts(row):
    if row['OI Lakhs (Puts)'] < 0 and row['LTP (Puts)'] > 0:
        return "Short Covering"
    elif row['OI Lakhs (Puts)'] > 0 and row['LTP (Puts)'] < 0:
        return "Short Buildup"
    elif row['OI Lakhs (Puts)'] < 0 and row['LTP (Puts)'] < 0:
        return "Long Unwinding"
    elif row['OI Lakhs (Puts)'] > 0 and row['LTP (Puts)'] > 0:
        return "Long Buildup"
    else:
        return "NA"


def calculate_roc(df):
    df['time'] = pd.to_datetime(df['time'], format="%d/%m/%Y %H:%M:%S")
    df.drop(["oi_change_calls", "oi_change_pct_calls", "oi_change_pct_puts", "oi_change_puts"], axis=1, inplace=True)

    grouped = df.groupby('strike_price')
    
    df_roc_list = []
    for strike_price, group in grouped:
        group = group.sort_values('time')
        group_roc = group.copy()
        
        for column in group.columns:
            if column not in ['strike_price', 'time', 'oi_change_pct_puts', 'oi_change_pct_calls']:
                group_roc[column] = round(group[column].diff(), 2)
        
        group_roc['strike_price'] = group['strike_price']
        group_roc = group_roc.dropna()

        unique_times = group['time'].unique()
        if len(unique_times) == 2:
            later_time = max(unique_times)
        else:
            later_time = group['time'].iloc[-1]
        
        group_roc['time'] = later_time
        df_roc_list.append(group_roc)

    df_roc = pd.concat(df_roc_list, ignore_index=True)

    df_roc['strike_price'] = df_roc['strike_price'].astype(int)
    
    df_roc.rename(columns={
        "volume_calls": "Volume (Calls)",
        "oi_lakhs_calls": "OI Lakhs (Calls)",
        "ltp_calls": "LTP (Calls)",
        "strike_price": "Strike Price",
        "iv": "IV",
        "ltp_puts": "LTP (Puts)",
        "oi_lakh_puts": "OI Lakhs (Puts)",
        "volume_puts": "Volume (Puts)",
        "time": "Time (ROC)"
    }, inplace=True)

    df_roc['Remarks (Calls)'] = df_roc.apply(get_remarks_calls, axis=1)
    df_roc['Remarks (Puts)'] = df_roc.apply(get_remarks_puts, axis=1)
    df_roc['COI/VOL (Calls)'] = df_roc['OI Lakhs (Calls)'] / df_roc['Volume (Calls)']
    df_roc['COI/VOL (Puts)'] = df_roc['OI Lakhs (Puts)'] / df_roc['Volume (Puts)']

    df_roc = df_roc.reindex(columns=[
        'Remarks (Calls)', 'Volume (Calls)', 'OI Lakhs (Calls)', 'LTP (Calls)', 'IV', 'COI/VOL (Calls)',
        'Strike Price', 'COI/VOL (Puts)', 'Volume (Puts)', 'OI Lakhs (Puts)', 'LTP (Puts)', 'Remarks (Puts)', 'Time (ROC)'
    ])

    return df_roc

