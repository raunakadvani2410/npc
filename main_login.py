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
from pyvirtualdisplay import Display

def enter_webpage(link):
    # store exe directory
    #cd_path2 = "/Users/raunakadvani/Desktop/2023-2024/Finances/nifty_puts_calls/npc/chromedriver"
    #cd_path = "./chromedriver"
    cd_path = Service('./chromedriver')
    # TODO where does this go??
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")

    # set driver directory
    # TODO below line for dsan5400, older version of selenium
    driver = webdriver.Chrome(service=cd_path, options= chrome_options)
    #driver = webdriver.Chrome("./chromedriver", options = chrome_options)
    #driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options = chrome_options)
    #driver = webdriver.Chrome(options = chrome_options)

   # driver = webdriver.Remote(
   #         command_executor = 'http://172.31.9.13:4444/wd/hub',
   #         options = chrome_options
   #         )
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

    # sleep
    tm.sleep(5)

    # id for otp
    login_otp = driver.find_element(By.ID, 'userid')

    # prompt the user for login otp
    while True:
        otp = input("Please enter a 6-digit mobile code: ")
        if otp.isdigit() and len(otp) == 6:
            break
        else:
            print("Invalid input. The mobile code must be numeric and 6 digits long.")

    # input the userid
    login_otp.send_keys(otp)

    # xpath for continue button
    continue_button_x_path = '//*[@id="container"]/div[2]/div/div[2]/form/div[2]/button'

    # find continue button
    cb = driver.find_element(By.XPATH, continue_button_x_path)

    # click button
    driver.execute_script("arguments[0].click();", cb);

    # sleep
    tm.sleep(2)

    # remove this?
    #driver.close()

    return driver

def find_table(driver):
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
    # TODO remove this?
    #driver.close()
    
    # return the driver and table element
    return driver, data_list


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

    # # sleep for 3 seconds
    # tm.sleep(3)

    for data in table_data:
        data_list = data.text.split()

    # close tab
    # TODO will have to keep open?
    #driver.close()
    
    # return the table element
    return driver, data_list

def find_and_return_table_no_button(driver):
    # set xpath for div that contains data
    x_path = '/html/body/div[1]/div/div[3]/div[2]/div[2]/div/main/div/table/tbody'

    # sleep for 3 seconds
    tm.sleep(3)

    # find table element
    table_data = driver.find_elements(By.XPATH, x_path)

    # # sleep for 3 seconds
    # tm.sleep(3)

    for data in table_data:
        data_list = data.text.split()

    # close tab
    # TODO will have to keep open?
    #driver.close()
    
    # return the table element
    return driver, data_list


def build_dataframe(data_list):
    # set IST
    IST = pytz.timezone('Asia/Kolkata') 

    # get the current datetime
    now = datetime.now(IST)

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

    print(f"Central Strike: {central_strike}")
    print(f"Strike Prices to Keep: {strike_prices_to_keep}")

    # Print the strike_price column before filtering
    print("Strike Prices in DataFrame before filtering:")
    print(df['strike_price'].unique())

    print("SAVE DF FOR SANITY")
    df.to_csv("test.csv")

    # filter the dataframe
    df = df[df['strike_price'].isin(strike_prices_to_keep)]

    # reset index and remove index column
    df = df.reset_index(drop = True)

    # Print the DataFrame after filtering
    print("DataFrame after slicing:")
    print(df.head())

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
        #IST = pytz.timezone('Asia/Kolkata') 
        # get the current datetime
        #check_time = datetime.now(IST).time()
        check_time = datetime.now().time()
    return begin_time <= check_time <= end_time


def main():
    disp = Display()
    disp.start()

    # set wide layout by default
    st.set_page_config(layout="wide")
    IST = pytz.timezone('Asia/Kolkata') 

    now = datetime.now(IST)
    print(now)

    # insert title
    st.title("Option Chain ROC")

    # set path
    #path = '/Users/raunakadvani/Desktop/2023-2024/Finances/nifty_puts_calls'
    # TODO add for local
    # os.chdir(path)

    # enter the webpage first
    page_driver = enter_webpage('https://web.sensibull.com/option-chain?tradingsymbol=NIFTY')
    #login()

    tm.sleep(10)
    page_driver, nifty_futures = get_nifty_futures(page_driver)

    print(f"Original NIFTY VALUE: {nifty_futures}")

    # initialise df to hold all the data
    df_roc = pd.DataFrame()

    # initialise data
    page_driver, data_list = find_and_return_table(page_driver)

    # build the dataframe from the list
    df = build_dataframe(data_list)
    print("****PRINTING ORIGINAL DF SHAPE:")
    print(df.shape)
    # slice the df based on the strike price
    df = slice_df(df, nifty_futures)
    print("****PRINTING SLICED DF SHAPE****")
    print(df.shape)

    print("SAVING RAW DATA AFTER SLICING")
    df.to_csv("raw_data_0.csv")

    st.dataframe(df)

    # wait for 4 minutes
    tm.sleep(20)

    counter = 1
    
    while is_time_between(time(0,2), time(19,34)):
        #TODO THIS IS NEW *****
        # enter the webpage first
        #page_driver = enter_webpage('https://web.sensibull.com/option-chain?tradingsymbol=NIFTY')
        #login()

        #tm.sleep(20)

        # get the current nifty futures value
        page_driver, nifty_futures = get_nifty_futures(page_driver)
        print(f"NIFTY VALUE: {nifty_futures}")

        # find and return the data
        print("SHOULD PRESS BUTTON NOW")
        page_driver, data_list = find_and_return_table_no_button(page_driver)
        df_1 = build_dataframe(data_list)

        # print original dataframe
        print("****PRINTING SHAPE DF TO BE SLICED******")
        print(df_1.shape)

        # slice the dataframe based on nifty
        df_1 = slice_df(df_1, nifty_futures)

        # print sliced df as a sanity check
        print("*****PRINTING SLICED DF SHAPE******")
        print(df_1.shape)

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

#TODO UNCOMMENT!!
        #if counter is 1: just output the original changes df
        if counter == 1:
            st.write(f"Printing change {counter}")
            changes = changes.sort_values(['strike_price', 'time_roc'], ascending=[True, True])
            dataa = st.dataframe(changes, height = 100)
            #dataa = st.dataframe(changes, height = len(changes))

        elif counter > 1:
            # append the changes to the master changes df
            st.write(f"Printing change {counter}")
            dataa.add_rows(changes)
        
        # concat dfs
        df_roc = pd.concat([df_roc, changes], ignore_index = True)

        # put in ascending order of strike price and time
        df_roc = df_roc.sort_values(['strike_price', 'time_roc'], ascending=[True, True])

        # save df
        df_roc.to_csv("rates_of_change.csv")
        print(df_roc)
        # print time
        now = datetime.now(IST)

        print(f"Update {counter}: Changes saved for {now} ")

        # update counter
        counter+=1

        # create a copy of the second dataframe to assign it to the earlier one
        df = df_1.copy()
        del df_1

        # TODO
        # chnge to 3 mins?
        tm.sleep(20)
    
    # shut the virtual display
    disp.stop()

    # 
    # quit the driver
    page_driver.quit()

    # return the df
    return

if __name__ == '__main__':
    main()
        
           
        
    


