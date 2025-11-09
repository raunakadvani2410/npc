from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time as tm
from config import CHROMEDRIVER_PATH, ZERODHA_USER_ID, ZERODHA_PASSWORD


def enter_webpage(link):
    cd_path = Service(CHROMEDRIVER_PATH)
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=3840,2160")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-mobile-emulation")
    chrome_options.add_argument("--force-device-scale-factor=1")
    chrome_options.add_argument("--high-dpi-support=1")

    desktop_emulation = {
        "deviceMetrics": {"width": 1920, "height": 1080, "pixelRatio": 1.0},
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "clientHints": {"platform": "Windows", "mobile": False}
    }
    chrome_options.add_experimental_option("mobileEmulation", desktop_emulation)

    driver = webdriver.Chrome(service=cd_path, options=chrome_options)
    driver.get(link) 
    print(f"Entering link: {link}")

    driver.maximize_window()
    driver.execute_script("window.resizeTo(3840, 2160);")
    driver.maximize_window()
    tm.sleep(3)

    return driver


def get_nifty_futures(driver):
    futures_element = '/html/body/div[1]/div/div[3]/div[2]/div/div/header/div/div[1]/div/div/div'
    
    nifty = driver.find_element(By.XPATH, futures_element).text
    nifty_float = None
    try:
        nifty_float = float(nifty)
    except ValueError:
        print("Error! Nifty value can't be found or can't be converted to float")
    
    return driver, nifty_float 


def login(driver):
    try:
        lb = driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
    except NoSuchElementException:
        try:
            lb = driver.find_element(By.XPATH, "//button[normalize-space()='Login']")
        except NoSuchElementException:
            print("Login button not found")
            return driver

    driver.execute_script("arguments[0].click();", lb)
    tm.sleep(2)

    try:
        zb = driver.find_element(By.XPATH, "//button[contains(text(), 'Login with Zerodha')]")
    except NoSuchElementException:
        try:
            zb = driver.find_element(By.XPATH, "//button[contains(normalize-space(), 'Zerodha')]")
        except NoSuchElementException:
            print("Zerodha button not found")
            return driver

    driver.execute_script("arguments[0].click();", zb)
    tm.sleep(2)

    login_input = driver.find_element(By.ID, 'userid')
    login_input.send_keys(ZERODHA_USER_ID)
    tm.sleep(2)

    password_input = driver.find_element(By.ID, 'password')
    password_input.send_keys(ZERODHA_PASSWORD)

    sb = driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
    driver.execute_script("arguments[0].click();", sb)
    tm.sleep(2)

    return driver


def submit_otp(driver, otp):
    try:
        print(f"Submitting OTP {otp} {type(otp)}")
        otp_input = driver.find_element(By.ID, 'userid')
        otp_input.send_keys(otp)

        continue_button_x_path = '//*[@id="container"]/div[2]/div/div[2]/form/div[2]/button'
        cb = driver.find_element(By.XPATH, continue_button_x_path)
        driver.execute_script("arguments[0].click();", cb)
        print("OTP entered successfully")
        tm.sleep(2)
    except Exception as e:
        print(f"An error occurred during OTP submission: {e}")
        raise
    return driver  


def find_and_return_table(driver):
    try:    
        print("Looking for 'All Column View' button")
        wait = WebDriverWait(driver, 10)
        l = wait.until(EC.element_to_be_clickable((By.XPATH, "//p[text()='All Column View']/parent::button")))
        driver.execute_script("arguments[0].click();", l)
        print("'All Column View' button found and clicked")
        
        print("Waiting for table to expand...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//tbody//td[contains(@class, 'col-ce')]")))
    
    except (NoSuchElementException, TimeoutException) as e:
        print(f"'All Column View' button not found or not clickable: {e}. Moving on.")

    print("Looking for options table")
    try:
        table_data = driver.find_elements(By.XPATH, "//tbody[.//tr[contains(@id, '2')]]")
    except Exception as e:
        print(f"Error finding table: {e}")
        table_data = []
        
    print(f"Length of table data: {len(table_data)}")
    print(f"Type of table data: {type(table_data)}")
   
    data_list = [data.text.split() for data in table_data]
    
    return driver, data_list[0]


def find_and_return_table_no_button(driver):
    tm.sleep(3)

    print("Looking for options table (no button)")
    try:
        table_data = driver.find_elements(By.XPATH, "//tbody[.//tr[contains(@id, '2')]]")
    except Exception as e:
        print(f"Error finding table: {e}")
        table_data = []

    data_list = [data.text.split() for data in table_data]
    return driver, data_list[0] if data_list else []

