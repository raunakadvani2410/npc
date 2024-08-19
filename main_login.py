import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
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
import streamlit as st
import pytz
import yfinance as yf
import requests
from pyvirtualdisplay import Display

def enter_webpage(link):
    # store exe directory
    cd_path = Service('./chromedriver')
    
    # set chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")

    # set driver directory
    # TODO below line for dsan5400, older version of selenium
    driver = webdriver.Chrome(service=cd_path, options= chrome_options)

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
    # futures_element = '/html/body/div[1]/div/div[3]/div[2]/div[2]/div/header/div/div[1]/div/div/div/div[1]'
    futures_element = '/html/body/div[1]/div/div[3]/div[2]/div/div/header/div/div[1]/div/div/div'
    # futures_element = '/html/body/div[1]/div/div[3]/div[2]/div[2]/div/header/div/div[1]/div/div/div/div[1]/span[2]'

    # find div
    nifty = driver.find_element(By.XPATH, futures_element).text
    nifty_float = None
    try:
        # convert to float
        nifty_float = float(nifty)
    except ValueError:
        print("Error! Nifty value can't be found or can't be converted to float")
    
    # driver.close()
    return driver, nifty_float 

def login(driver):
    # set xpath for login button
    login_button_x_path = '//*[@id="app"]/div/div[3]/div[2]/div[1]/div/div[2]/button'

    # find login button
    lb = driver.find_element(By.XPATH, login_button_x_path)

    # click button
    driver.execute_script("arguments[0].click();", lb);

    # sleep
    tm.sleep(2)

    # set xpath for zerodha button
    zerodha_button_x_path = '//*[@id="notloggedInSegment"]/div/div[1]/div[2]/button[1]'

    # find zerodha button
    zb = driver.find_element(By.XPATH, zerodha_button_x_path)

    # click button
    driver.execute_script("arguments[0].click();", zb);

    # sleep
    tm.sleep(2)

    # id for userid
    login_input = driver.find_element(By.ID, 'userid')

    # input the userid
    login_input.send_keys("ETS537")

    # sleep
    tm.sleep(2)

    # id for password
    password_input = driver.find_element(By.ID, 'password')

    # input the password
    password_input.send_keys("Kaustubh@1")

    # xpath for submit button
    submit_button_x_path = '//*[@id="container"]/div/div/div[2]/form/div[4]/button'

    # find submit button
    sb = driver.find_element(By.XPATH, submit_button_x_path)

    # click button
    driver.execute_script("arguments[0].click();", sb);

    tm.sleep(2)

    return driver


def submit_otp(driver, otp):
    try:
        #tm.sleep(20)
        # ID for OTP
        otp_input = driver.find_element(By.ID, 'userid')
        otp_input.send_keys(otp)

        # XPath for continue button
        continue_button_x_path = '//*[@id="container"]/div[2]/div/div[2]/form/div[2]/button'
        cb = driver.find_element(By.XPATH, continue_button_x_path)
        driver.execute_script("arguments[0].click();", cb)
        st.success("OTP entered successfully")
        tm.sleep(2)
    except Exception as e:
        st.error(f"An error occurred: {e}")
    return driver  

def get_otp_from_flask():
    # wait for user to input otp
    otp = None
    while otp is None:
        try:
            tm.sleep(15)

            # URL to get the OTP
            url = 'https://raunakadvani.pythonanywhere.com/get_otp'

            # Send a GET request to retrieve the OTP
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                otp = data.get('otp')
        except requests.exceptions.RequestException as e:
            st.write("Error contacting flask app", e)
            tm.sleep(10)
    return otp


def find_and_return_table(driver):

    # set xpath for select all columns button
    # button_x_path = '/html/body/div[1]/div/div[3]/div[2]/div[2]/div/footer/div[1]/button[2]'
    button_x_path = '/html/body/div[1]/div/div[3]/div[2]/div/div/footer/div[1]/button[2]'
    # //*[@id="app"]/div/div[3]/div[2]/div[2]/div/footer/div[1]/button[2]
    try:
        # find select all columns button
        l = driver.find_element(By.XPATH, button_x_path)

        # click button
        driver.execute_script("arguments[0].click();", l);
    
    except NoSuchElementException:
        print("Button not found, moving on.")

    # set xpath for div that contains data
    x_path = '/html/body/div[1]/div/div[3]/div[2]/div/div/main/div/table/tbody'
    # x_path = '/html/body/div[1]/div/div[3]/div[2]/div[2]/div/main/div/table/tbody'

    # sleep for 3 seconds
    tm.sleep(3)

    # find table element
    table_data = driver.find_elements(By.XPATH, x_path)

    # # sleep for 3 seconds
    # tm.sleep(3)

    # for data in table_data:
    #     data_list1 = data.text.split()

    # print(f"Type using for loop: {type(data_list1)}")
    # print(f"Length using for loop: {len(data_list1)}")

    data_list = [data.text.split() for data in table_data]

    # close tab
    # TODO will have to keep open?
    #driver.close()
    
    # return the table element
    return driver, data_list[0]

def find_and_return_table_no_button(driver):
    # set xpath for div that contains data
    # x_path = '/html/body/div[1]/div/div[3]/div[2]/div[2]/div/main/div/table/tbody'
    x_path = '/html/body/div[1]/div/div[3]/div[2]/div/div/main/div/table/tbody'

    # sleep for 3 seconds
    tm.sleep(3)

    # find table element
    table_data = driver.find_elements(By.XPATH, x_path)

    # for data in table_data:
    #     data_list = data.text.split()

    data_list = [data.text.split() for data in table_data]

    # return the table element
    return driver, data_list[0]


def build_dataframe(data_list):
    # set IST
    IST = pytz.timezone('Asia/Kolkata') 

    # get the current datetime
    # dt_string = datetime.now(IST).strftime("%d/%m/%Y %H:%M:%S")
    dt_string = datetime.now(IST).strftime("%H:%M")

    # reshape the data into rows of 33 elements
    rows = [data_list[i:i+28] for i in range(0, len(data_list), 28)]

    # column names and corresponding indices
    columns = {
        'volume_calls': 5,
        'oi_change_calls': 6,
        'oi_change_pct_calls': 7,
        'oi_lakhs_calls': 8,
        'ltp_calls': 11,
        'Strike Price': 13,
        'iv': 14,
        'ltp_puts': 16,
        'oi_lakh_puts': 20,
        'oi_change_pct_puts': 21,
        'oi_change_puts': 22,
        'volume_puts': 23,
    }

    # initialize a list to store the rows of the DataFrame
    df_data = []

    # process each row
    for i, row in enumerate(rows):
        df_row = {}
        for column, index in columns.items():
            try:
                value = row[index].replace('%', '')
                if column == 'Strike Price':
                    df_row[column] = int(float(value))  
                else:
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
    print(strike_prices_to_keep)
    # filter the dataframe
    df = df[df['Strike Price'].isin(strike_prices_to_keep)]

    # reset index and remove index column
    df = df.reset_index(drop = True)

    # return the filtered dataframe
    return df


# Add remarks_calls column based on conditions
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
    
# Add remarks_puts column based on conditions
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

# calculate rate of change
def calculate_roc(df):
    # convert to datetime format
    # df['time'] = pd.to_datetime(df['time'], format="%d/%m/%Y %H:%M:%S")
    df['time'] = pd.to_datetime(df['time'], format="%H:%M").dt.time
    # df['time'] = pd.to_datetime(df['time'])
    df.drop(["oi_change_calls", "oi_change_pct_calls", "oi_change_pct_puts", "oi_change_puts"], axis = 1, inplace = True)

    # group by strike price
    grouped = df.groupby('Strike Price')
    
    df_roc_list = []
    for strike_price, group in grouped:
        group = group.sort_values('time')
        group_roc = group.copy()
        
        for column in group.columns:
            if column not in ['Strike Price', 'time', 'oi_change_pct_puts', 'oi_change_pct_calls']:
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
        "volume_calls":"Volume (calls)",
        "oi_lakhs_calls":"OI Lakhs (Calls)",
        "ltp_calls":"LTP (Calls)",
        "iv":"IV",
        "ltp_puts":"LTP (Puts)",
        "oi_lakh_puts":"OI Lakhs (Puts)",
        "volume_puts":"Volume (puts)",
        "time":"Time (ROC)"
    }, inplace=True)

    # add remarks    
    df_roc['Remarks (Calls)'] = df_roc.apply(get_remarks_calls, axis=1)
    df_roc['Remarks (Puts)'] = df_roc.apply(get_remarks_puts, axis=1) 

    # rearrange columns
    df_roc = df_roc.reindex(columns = ['Remarks (Calls)', 'Volume (calls)', 'OI Lakhs (Calls)', 'LTP (Calls)','IV',
                                       'Strike Price', 'Volume (puts)', 'OI Lakhs (Puts)', 'LTP (Puts)', 'Remarks (Puts)', 'Time (ROC)'])

    return df_roc

def is_time_between(begin_time, end_time, check_time=None):
    # If check time is not given, default to current time
    if check_time is None:
        IST = pytz.timezone('Asia/Kolkata') 
        
        # get the current datetime
        check_time = datetime.now(IST).time()
        #check_time = datetime.now().time()
    return begin_time <= check_time <= end_time

def style_pos_neg(v, pos='', neg = ''):
    return pos if v > 0 else neg if v < 0 else None


def main():
    # turn on virtual display
    disp = Display()
    disp.start()

    # set wide layout by default
    st.set_page_config(layout="wide")
    IST = pytz.timezone('Asia/Kolkata') 

    now = datetime.now(IST)

    # insert title
    st.title("Option Chain ROC")

    # enter the webpage first
    st.write("Entering Sensibull webpage...")
    page_driver = enter_webpage('https://web.sensibull.com/option-chain?tradingsymbol=NIFTY')
    
    # login
    st.write("Entering login credentials...")
    page_driver = login(page_driver)
    st.write("OTP sent, enter in website now")

    otp = get_otp_from_flask()
    # tm.sleep(20)

    page_driver = submit_otp(page_driver, otp)

    tm.sleep(10)
    page_driver, data_list = find_and_return_table(page_driver)

    #return
    # fetching Nifty 50 data
    nifty = yf.Ticker("^NSEI")

    # get the latest market price
    nifty_futures = nifty.history(period="1d")['Close'].iloc[-1]

    # initialise df to hold all the data
    df_roc = pd.DataFrame()

    time_start = datetime.now()

    # build the dataframe from the list
    df = build_dataframe(data_list)

    # slice the df based on the strike price
    df = slice_df(df, nifty_futures)

    # print("SAVING RAW DATA AFTER SLICING")
    df.to_csv("raw_data_0.csv")

    st.write("Raw Data Fetched")
    
    # check end time
    time_end = datetime.now()

    print(f"Time taken to fetch raw data: {time_end - time_start}")
    tm.sleep(10)

    counter = 1

    with st.empty():
        while is_time_between(time(0,2), time(9,46)):
            time_start = datetime.now()
            # get the current nifty futures value
            # fetching Nifty 50 data
            nifty = yf.Ticker("^NSEI")

            # get the latest market price
            nifty_futures = nifty.history(period="1d")['Close'].iloc[-1]

            # find and return the data
            # print("SHOULD PRESS BUTTON NOW")
            page_driver, data_list = find_and_return_table_no_button(page_driver)
            df_1 = build_dataframe(data_list)

            # slice the dataframe based on nifty
            df_1 = slice_df(df_1, nifty_futures)

            # save to csv
            filename = f"raw_data_{counter}.csv"
            df_1.to_csv(filename)

            # append to master df
            all_data = pd.concat([df, df_1], ignore_index = True)
            changes = calculate_roc(all_data)

            # set roc time
            unique_times = all_data['time'].unique()
            earlier_time = min(unique_times)
            all_data = all_data[all_data['time'] != earlier_time]

            # concat dfs
            df_roc = pd.concat([df_roc, changes], ignore_index = True)
            st.write(f"ROC update: {counter}")
            # put in ascending order of strike price and time
            df_roc = df_roc.sort_values(['Strike Price', 'Time (ROC)'], ascending=[True, True])

            # save df
            df_roc.to_csv("rates_of_change.csv")
            print(df_roc)

            #if counter is 1: just output the original changes df
            if counter == 1:
                st.write(f"Printing change {counter}")
            
                # List of columns to apply the style
                columns_to_style = [
                    'Volume (calls)',
                    'OI Lakhs (Calls)',
                    'LTP (Calls)',
                    'Volume (puts)',
                    'OI Lakhs (Puts)',
                    'LTP (Puts)'
                ]
                st.write(f"ROC shape: {df_roc.shape}")

                # Apply the style only to the specified columns
                s2 = df_roc.style.applymap(lambda x: style_pos_neg(x, pos='color:white;background-color:darkgreen', neg='color:white;background-color:red'),
                                            subset=columns_to_style)
    
                # Display the styled dataframe
                dataa = st.dataframe(s2, height=900)

            elif counter > 1:
                # List of columns to apply the style
                columns_to_style = [
                    'Volume (calls)',
                    'OI Lakhs (Calls)',
                    'LTP (Calls)',
                    'Volume (puts)',
                    'OI Lakhs (Puts)',
                    'LTP (Puts)'
                ]

                # Apply the style only to the specified columns
                s2 = df_roc.style.applymap(lambda x: style_pos_neg(x, pos='color:white;background-color:darkgreen', neg='color:white;background-color:red'),
                                            subset=columns_to_style)

                # Display the styled dataframe
                dataa = st.dataframe(s2, height=900)

            
            # print time
            now = datetime.now(IST)

            print(f"Update {counter}: Changes saved for {now} ")

            # update counter
            counter+=1

            # create a copy of the second dataframe to assign it to the earlier one
            df = df_1.copy()
            del df_1

            time_end = datetime.now()
            print(f"Time taken: {time_end - time_start}")

            # TODO
            # chnge to 3 mins?
            tm.sleep(30)
    
    st.write("Ending Program Now")
    # shut the virtual display
    disp.stop()

    print("Quiting driver now")
    # quit the driver
    page_driver.quit()

    # return the df
    return


if __name__ == '__main__':
    main()
    