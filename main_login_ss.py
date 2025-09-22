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
import sys
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
    print(f"Entering link: {link}")
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
    # login_button_x_path = '//*[@id="app"]/div/div[3]/div[2]/div[1]/div/div[2]/button'
    # login_button_x_path = '//*[@id="app"]/div/div[2]/nav/div/div[3]/div/button[1]'

    # # find login button
    # lb = driver.find_element(By.XPATH, login_button_x_path)

    # find login button by text content - more reliable than xpath
    try:
        lb = driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
    except NoSuchElementException:
        # fallback: try finding by partial text match
        try:
            lb = driver.find_element(By.XPATH, "//button[normalize-space()='Login']")
        except NoSuchElementException:
            print("Login button not found")
            return driver

    # click button
    driver.execute_script("arguments[0].click();", lb)

    # sleep
    tm.sleep(2)
    # set xpath for zerodha button
    # zerodha_button_x_path = '//*[@id="notloggedInSegment"]/div/div[1]/div[2]/button[1]'
    # zerodha_button_x_path = '//*[@id="radix-4"]/div/div[1]/button[1]'
    

    # find zerodha button
    # find zerodha button by text content - bulletproof approach
    try:
    #     zb = driver.find_element(By.XPATH, zerodha_button_x_path)
    # except NoSuchElementException:
    #     print("Zerodha button not found")
    #     return driver
        zb = driver.find_element(By.XPATH, "//button[contains(text(), 'Login with Zerodha')]")
    except NoSuchElementException:
        # fallback: try partial match or case variations
        try:
            zb = driver.find_element(By.XPATH, "//button[contains(normalize-space(), 'Zerodha')]")
        except NoSuchElementException:
            print("Zerodha button not found")
            return driver

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
    # submit_button_x_path = '//*[@id="container"]/div/div/div[2]/form/div[4]/button'
    # submit_button_x_path = '//*[@id="container"]/div/div/div[2]/form/div[4]/button'



    # find submit button
    # sb = driver.find_element(By.XPATH, submit_button_x_path)
    sb = driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")

    # click button
    driver.execute_script("arguments[0].click();", sb);

    tm.sleep(2)

    return driver


def submit_otp(driver, otp):
    try:
        #tm.sleep(20)
        # ID for OTP
        print(f"Submitting OTP {otp} {type(otp)}")
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
            print(type(response))
            if response.status_code == 200:
                data = response.json()
                otp = data.get('otp')
                print(f"Retrieved OTP: {otp}")
        except requests.exceptions.RequestException as e:
            st.write("Error contacting flask app", e)
            tm.sleep(10)
    return otp


def find_and_return_table(driver):

    # set xpath for select all columns button
    # button_x_path = '/html/body/div[1]/div/div[3]/div[2]/div[2]/div/footer/div[1]/button[2]'
    # button_x_path = '/html/body/div[1]/div/div[3]/div[2]/div/div/footer/div[1]/button[2]'
    # button_x_path = '/html/body/div[1]/div/div[2]/div[2]/div[2]/div/footer/div[1]/button[2]'
    #button_x_path = '/html/body/div[1]/div/div[2]/div/div[2]/footer/div[1]/button[2]'
    button_x_path = '/html/body/div[1]/div/div[2]/div/div/footer/div[1]/button[2]'
    
    # //*[@id="app"]/div/div[3]/div[2]/div[2]/div/footer/div[1]/button[2]
    try:
        print("Looking for button")
        # find select all columns button
        l = driver.find_element(By.XPATH, button_x_path)

        driver.execute_script("arguments[0].click();", l);
        print("Button found ")
    except NoSuchElementException:
        print("Button not found, moving on.")

    # set xpath for div that contains data
    # x_path = '/html/body/div[1]/div/div[3]/div[2]/div/div/main/div/table/tbody'
    # x_path = '/html/body/div[1]/div/div[2]/div[2]/div[2]/div/main/div/table/tbody'
    # x_path = '/html/body/div[1]/div/div[2]/div/div[2]/main/div/table/tbody'
    # x_path = '/html/body/div[1]/div/div[3]/div[2]/div[2]/div/main/div/table/tbody'
    x_path = '/html/body/div[1]/div/div[2]/div/div/main/div/table/tbody'
    # sleep for 3 seconds
    tm.sleep(3)
    
    print("Looking for table")
    # find table element
    table_data = driver.find_elements(By.XPATH, x_path)
    # for data in table_data:
    #     data_list1 = data.text.split()

    print(f"Length of table data: {len(table_data)}")
    print(f"Type of table data: {type(table_data)}")
    data_list = [data.text.split() for data in table_data]

    print(f"Length of data list: {len(data_list)}")
    print(f"Type of data list: {type(data_list)}")
    # print(f"Data list: {data_list}")

    # close tab
    # TODO will have to keep open?
    #driver.close()
    
    # return the table element
    return driver, data_list[0]

def find_and_return_table_no_button(driver):
    # set xpath for div that contains data
    # x_path = '/html/body/div[1]/div/div[3]/div[2]/div[2]/div/main/div/table/tbody'
    # x_path = '/html/body/div[1]/div/div[3]/div[2]/div/div/main/div/table/tbody'
    # x_path = '/html/body/div[1]/div/div[2]/div[2]/div[2]/div/main/div/table/tbody'
    # x_path = '/html/body/div[1]/div/div[2]/div/div[2]/footer/div[1]/button[2]'
    # x_path = '/html/body/div[1]/div/div[2]/div/div[2]/main/div/table/tbody'
    x_path = '/html/body/div[1]/div/div[2]/div/div/main/div/table/tbody'

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
    dt_string = datetime.now(IST).strftime("%d/%m/%Y %H:%M:%S")

    # reshape the data into rows of 41 elements (0 to 40 inclusive) ***TODO this is for without login
    # with login, it is 27
    rows = [data_list[i:i+27] for i in range(0, len(data_list), 27)]

    # column names and corresponding indices, below is indices without login
    # columns = {
    #     'volume_calls': 6,
    #     'oi_change_calls': 7,
    #     'oi_change_pct_calls': 8,
    #     'oi_lakhs_calls': 9,
    #     'ltp_calls': 18,
    #     'strike_price': 20,
    #     'iv': 21,
    #     'ltp_puts': 22,
    #     'oi_lakh_puts': 32,
    #     'oi_change_pct_puts': 33,
    #     'oi_change_puts': 34,
    #     'volume_puts': 35,
    # }

    # column names and corresponding indices
    columns = {       
        'volume_calls': 2,
        'oi_change_calls': 3 ,
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

    # filter the dataframe
    df = df[df['strike_price'].isin(strike_prices_to_keep)]

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
    df['time'] = pd.to_datetime(df['time'], format="%d/%m/%Y %H:%M:%S")
    df.drop(["oi_change_calls", "oi_change_pct_calls", "oi_change_pct_puts", "oi_change_puts"], axis = 1, inplace = True)

    # group by strike price
    grouped = df.groupby('strike_price')
    
    df_roc_list = []
    for strike_price, group in grouped:
        group = group.sort_values('time')
        group_roc = group.copy()
        
        for column in group.columns:
            # Skip strike_price and time columns when calculating ROC
            if column not in ['strike_price', 'time', 'oi_change_pct_puts', 'oi_change_pct_calls']:
                # calculate the roc
                group_roc[column] = round(group[column].diff(),2)
        
        # Keep the original strike price value (don't calculate diff)
        group_roc['strike_price'] = group['strike_price']
        
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

    # Convert strike_price to integer before renaming
    df_roc['strike_price'] = df_roc['strike_price'].astype(int)
    # rename columns
    df_roc.rename(columns = {
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

    # add remarks    
    df_roc['Remarks (Calls)'] = df_roc.apply(get_remarks_calls, axis=1)
    df_roc['Remarks (Puts)'] = df_roc.apply(get_remarks_puts, axis=1)
    df_roc['COI/VOL (Calls)'] = df_roc['OI Lakhs (Calls)']/df_roc['Volume (Calls)']
    df_roc['COI/VOL (Puts)'] = df_roc['OI Lakhs (Puts)']/df_roc['Volume (Puts)']

    # rearrange columns
    df_roc = df_roc.reindex(columns = ['Remarks (Calls)', 'Volume (Calls)', 'OI Lakhs (Calls)', 'LTP (Calls)','IV', 'COI/VOL (Calls)',
                                       'Strike Price', 'COI/VOL (Puts)', 'Volume (Puts)', 'OI Lakhs (Puts)', 'LTP (Puts)', 'Remarks (Puts)', 'Time (ROC)'])

    return df_roc

def is_time_between(begin_time, end_time, check_time=None):
    # If check time is not given, default to current time
    if check_time is None:
        IST = pytz.timezone('Asia/Kolkata') 
        check_time = datetime.now(IST).time()
    
    is_between = begin_time <= check_time <= end_time
    
    # If we're outside the time window, print a message
    if not is_between:
        st.write("Outside trading hours. Shutting down...")
        print("Outside trading hours. Shutting down...")
    
    return is_between

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

    time_start = datetime.now()
    print("Getting table")
    page_driver, data_list = find_and_return_table(page_driver)

    #COMMENTING 4 LINES BELOW
    # fetching Nifty 50 data
    nifty = yf.Ticker("^NSEI")

    # get the latest market price
    nifty_futures = nifty.history(period="1d")['Close'].iloc[-1]

    #ADDED IN
    # nifty_futures = 25019


    # initialise df to hold all the data
    df_roc = pd.DataFrame()

    # build the dataframe from the list
    df = build_dataframe(data_list)

    df.to_csv("raw_data_0.csv")
    # slice the df based on the strike price
    df = slice_df(df, nifty_futures)

    # print("SAVING RAW DATA AFTER SLICING")
    df.to_csv("raw_data_0_idk.csv")

    st.write("Raw Data Fetched")
    
    # check end time
    time_end = datetime.now()

    print(f"Time taken to fetch raw data: {time_end - time_start}")
    print(f"Waiting 30 seconds")
    tm.sleep(30)

    counter = 1

    with st.empty():
        try:
            while is_time_between(time(0,2), time(9,40)):
                time_start = datetime.now()
                # get the current nifty futures value

                # COMMENTING 4 LINES BELOW ***UNCOMMENT FOR REAL TIME DATA ***
                # # fetching Nifty 50 data
                nifty = yf.Ticker("^NSEI")

                # # get the latest market price
                # nifty_futures = nifty.history(period="1d")['Close'].iloc[-1]

                # nifty_futures = 25019
                # find and return the data
                # print("SHOULD PRESS BUTTON NOW")
                page_driver, data_list = find_and_return_table_no_button(page_driver)
                # print(f"Length of data list: {len(data_list)}")

                df_1 = build_dataframe(data_list)
                # print("Building dataframe, now saving to csv") 
                df_1.to_csv("raw_data_1unsliced.csv")

                # slice the dataframe based on nifty
                df_1 = slice_df(df_1, nifty_futures)
                # print("Slicing dataframe")
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

                # Get unique strike prices and sort them
                unique_strikes = sorted(df_roc['Strike Price'].unique())
                
                # Create tabs for each strike price
                tabs = st.tabs([f"{int(strike)}" for strike in unique_strikes])
                
                # List of columns to apply the style (keeping your original styling)
                columns_to_style = [
                    'Volume (Calls)',
                    'OI Lakhs (Calls)',
                    'LTP (Calls)',
                    'Volume (Puts)',
                    'OI Lakhs (Puts)',
                    'LTP (Puts)'
                ]
                
                # For each tab/strike price
                for tab, strike in zip(tabs, unique_strikes):
                    with tab:
                        # Filter data for this strike price
                        strike_data = df_roc[df_roc['Strike Price'] == strike]
                        
                        # Sort by time within each strike price
                        strike_data = strike_data.sort_values('Time (ROC)', ascending=True)
                        
                        # Apply your original styling to the filtered data
                        s2 = strike_data.style.applymap(
                            lambda x: style_pos_neg(x, 
                                pos='color:white;background-color:darkgreen', 
                                neg='color:white;background-color:red'),
                            subset=columns_to_style
                        )
                        
                        # Display the styled dataframe for this strike price
                        st.dataframe(s2, height=500)

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
            
            # Once we exit the while loop:
            print("Closing driver")
            st.write("Ending Program")
            
            # Clean up resources
            try:
                disp.stop()
                page_driver.quit()
            except:
                pass
                
            # Force stop the Streamlit app
            st.stop()
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
            try:
                disp.stop()
                page_driver.quit()
            except:
                pass
            st.stop()

    # return the df
    return


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Main program error: {e}")
        st.stop()
    