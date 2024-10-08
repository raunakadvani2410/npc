import pandas as pd
import os
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
#import chromedriver_binary  # Adds chromedriver binary to path
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime, time
import time as tm
import numpy as np
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def enter_webpage(link):
    # store exe directory
    cd_path = "/Users/raunakadvani/Desktop/2023-2024/Finances/nifty_puts_calls/npc/chromedriver"

    # set driver directory
    driver = webdriver.Chrome(executable_path=cd_path)
    # , options = chrome_options)

    # Open the website
    driver.get(link) 

    # For maximizing window
    driver.maximize_window()

    # sleep
    tm.sleep(3)

    # return the driver
    return driver

def get_nifty_futures(driver):
    # div holding nifty 50 futures value
    futures_element = '/html/body/div[1]/div/div[3]/div[2]/div[2]/div/header/div/div[1]/div/div/div/div[1]'

    # find div
    nifty = driver.find_element(By.XPATH, futures_element).text

    # split text to isolate nifty value
    nifty_text = nifty.split()[2]
    try:
        # convert to float
        nifty_float = float(nifty_text)
    except ValueError:
        print("Error! Nifty value can't be found or can't be converted to float")
    
    # driver.close()
    return driver, nifty_float



def find_and_return_table(driver):
    # add chrome options for headless config

    # TODO where does this go??
    # chrome_options = Options()
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--window-size=1920,1080")


    # set xpath for select all columns button
    button_x_path = '/html/body/div[1]/div/div[3]/div[2]/div[2]/div/footer/div[1]/button[2]'
    # //*[@id="app"]/div/div[3]/div[2]/div[2]/div/footer/div[1]/button[2]

    try:
        # find select all columns button
        l = driver.find_element(By.XPATH, button_x_path)

        # click button
        driver.execute_script("arguments[0].click();", l);
    
    except NoSuchElementException:
        print("Button not found, moving on.")

    # set xpath for div that contains data
    x_path = '/html/body/div[1]/div/div[3]/div[2]/div[2]/div/main/div/table/tbody'

    # sleep for 3 seconds
    tm.sleep(3)

    # find table element
    table_data = driver.find_elements(By.XPATH, x_path)

    # sleep for 3 seconds
    tm.sleep(3)

    for data in table_data:
        data_list = data.text.split()

    # close tab
    driver.close()
    
    # return the table element
    return data_list

# def build_dataframe(data_list):

#     # get the current datetime
#     now = datetime.now()
#     dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

#     # reshape the data into rows of 33 elements
#     rows = [data_list[i:i+33] for i in range(0, len(data_list), 33)]

#     # column names and corresponding indices
#     columns = {
#         'volume_calls': 6,
#         'oi_change_calls': 7,
#         'oi_change_pct_calls': 8,
#         'oi_lakhs_calls': 9,
#         'ltp_calls': 15,
#         'strike_price': 16,
#         'iv': 17,
#         'ltp_puts': 18,
#         'oi_lakh_puts': 24,
#         'oi_change_pct_puts': 25,
#         'oi_change_puts': 26,
#         'volume_puts': 27,
#     }

#     # initialize a list to store the rows of the DataFrame
#     df_data = []

#     # process each row
#     for row in rows:
#         # extract and convert the relevant columns
#         print("Next row:")
#         print(row)
#         df_row = {
#             # change not in row[index] to in row[index]?
#             # add condition for error handling of 'B'
#             column: float(row[index].replace('%', '')) if '%' not in row[index] else row[index] for column, index in columns.items()
#         }
#         #.replace('B', '')
#         print("Row passed")
        
#         # add the current datetime as a column
#         df_row['time'] = dt_string
#         df_data.append(df_row)

#     # create df
#     df = pd.DataFrame(df_data)

#     # return the df
#     return df

def build_dataframe(data_list):

    # get the current datetime
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

    # reshape the data into rows of 33 elements
    rows = [data_list[i:i+33] for i in range(0, len(data_list), 33)]

    # column names and corresponding indices
    # 17,18, 22, 23
    columns = {
        'volume_calls': 6,
        'oi_change_calls': 7,
        'oi_change_pct_calls': 8,
        'oi_lakhs_calls': 9,
        'ltp_calls': 15,
        'strike_price': 16,
        'iv': 17,
        'ltp_puts': 18,
        'oi_lakh_puts': 24,
        'oi_change_pct_puts': 25,
        'oi_change_puts': 26,
        'volume_puts': 27,
    }

    # initialize a list to store the rows of the DataFrame
    df_data = []

    # process each row
    for i, row in enumerate(rows):
        # print(f"Row {i+1} length: {len(row)}")
        # print(row)  # Print the row to see its content

        df_row = {}
        for column, index in columns.items():
            try:
                value = row[index].replace('%', '')
                df_row[column] = float(value)
            except (ValueError, IndexError):
                df_row[column] = np.nan  # Replace problematic values with NaN

        # add the current datetime as a column
        df_row['time'] = dt_string
        df_data.append(df_row)


    # create df
    df = pd.DataFrame(df_data)

    # return the df
    return df

def slice_df(df, nifty_futures):
    # round nifty_futures to nearest 100 to find the central strike price
    central_strike = round(nifty_futures / 100) * 100

    # calculate the strike prices to keep
    strike_prices_to_keep = [central_strike + i * 100 for i in range(-4, 4)]

    # filter the dataframe
    df = df[df['strike_price'].isin(strike_prices_to_keep)]

    # return the filtered dataframe
    return df


# Add remarks_calls column based on conditions
def get_remarks_calls(row):
    if row['change_oi_lakhs_calls'] < 0 and row['change_ltp_calls'] > 0:
        return "Short Covering"
    elif row['change_oi_lakhs_calls'] > 0 and row['change_ltp_calls'] < 0:
        return "Short Buildup"
    elif row['change_oi_lakhs_calls'] < 0 and row['change_ltp_calls'] < 0:
        return "Long Unwinding"
    else:
        return "NA"
    
# Add remarks_puts column based on conditions
def get_remarks_puts(row):
    if row['change_oi_lakhs_puts'] < 0 and row['change_ltp_puts'] > 0:
        return "Short Covering"
    elif row['change_oi_lakhs_puts'] > 0 and row['change_ltp_puts'] < 0:
        return "Short Buildup"
    elif row['change_oi_lakhs_puts'] < 0 and row['change_ltp_puts'] < 0:
        return "Long Unwinding"
    else:
        return "NA"

# calculate rate of change
def calculate_roc(df):
    # convert to datetime format
    df['time'] = pd.to_datetime(df['time'], format="%d/%m/%Y %H:%M:%S")
    df.drop(["oi_change_calls", "oi_change_pct_calls", "oi_change_pct_puts", "oi_change_puts"], axis = 1, inplace = True)

    # group by strike price
    grouped = df.groupby('strike_price')
    
    df_roc_list = []
    for strike_price, group in grouped:
        group = group.sort_values('time')
        group_roc = group.copy()
        
        for column in group.columns:
            if column not in ['strike_price', 'time', 'oi_change_pct_puts', 'oi_change_pct_calls']:
                # calculate the roc
                group_roc[column] = round(group[column].diff(),2)
        
        # drop nas
        group_roc = group_roc.dropna()

        # get the unique times and assign the later time to the new df
        unique_times = group['time'].unique()
        if len(unique_times) == 2:
            later_time = max(unique_times)
        else:
            later_time = group['time'].iloc[-1]
        
        group_roc['time'] = later_time
        
        df_roc_list.append(group_roc)

    df_roc = pd.concat(df_roc_list, ignore_index=True)
    df_roc.rename(columns = {
        "volume_calls":"change_volume_calls",
        "oi_lakhs_calls":"change_oi_lakhs_calls",
        "ltp_calls":"change_ltp_calls",
        "iv":"change_iv",
        "ltp_puts":"change_ltp_puts",
        "oi_lakh_puts":"change_oi_lakhs_puts",
        "volume_puts":"change_volume_puts",
        "time":"time_roc"
    }, inplace=True)

    # add remarks    
    df_roc['remarks_calls'] = df_roc.apply(get_remarks_calls, axis=1)
    df_roc['remarks_puts'] = df_roc.apply(get_remarks_puts, axis=1) 

    # rearrange columns
    df_roc = df_roc.reindex(columns = ['remarks_calls', 'change_volume_calls', 'change_oi_lakhs_calls', 'change_ltp_calls','change_iv',
                                       'strike_price', 'change_volume_puts', 'change_oi_lakhs_puts', 'change_ltp_puts', 'remarks_puts', 'time_roc'])

    return df_roc

def is_time_between(begin_time, end_time, check_time=None):
    # If check time is not given, default to current time
    if check_time is None:
        check_time = datetime.now().time()
    return begin_time <= check_time <= end_time


def main():
    # set path
    path = '/Users/raunakadvani/Desktop/2023-2024/Finances/nifty_puts_calls'
    os.chdir(path)

    # initialise df to hold all the data
    df_roc = pd.DataFrame()

    page_driver = enter_webpage('https://web.sensibull.com/option-chain?tradingsymbol=NIFTY')
    tm.sleep(10)
    page_driver, nifty_futures = get_nifty_futures(page_driver)

    # initialise data
    data_list = find_and_return_table()
    tm.sleep(5)
    df = build_dataframe(data_list)
    df.to_csv("raw_data_0.csv")
    # wait for 4 minutes
    tm.sleep(30)

    counter = 1
    
    while is_time_between(time(10,15), time(20,40)):

        # find and return the data
        data_list = find_and_return_table()
        df_1 = build_dataframe(data_list)
        filename = f"raw_data_{counter}.csv"
        df_1.to_csv(filename, index = False)

        # append to master df
        all_data = pd.concat([df, df_1], ignore_index = True)
        changes = calculate_roc(all_data)
        
        # set roc time
        unique_times = all_data['time'].unique()
        earlier_time = min(unique_times)
        all_data = all_data[all_data['time'] != earlier_time]
        
        # concat dfs
        df_roc = pd.concat([df_roc, changes], ignore_index = True)

        # save df
        df_roc.to_csv("rates_of_change.csv")

        # print time
        print(f"Update {counter}: Changes saved for {datetime.now().time()} ")

        # update counter
        counter+=1

        # create a copy of the second dataframe to assign it to the earlier one
        df = df_1.copy()
        del df_1

        # TODO
        # chnge to 3 mins?
        tm.sleep(30)
    return df_roc

if __name__ == '__main__':
    main()
        
           
        
    


