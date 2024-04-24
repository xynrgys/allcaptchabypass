# Import the required modules
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
import json
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from seleniumbase import Driver
import requests
import os
import whisper
import warnings
warnings.filterwarnings("ignore")

model = whisper.load_model("base")

def transcribe(url):
    with open('.temp', 'wb') as f:
        f.write(requests.get(url).content)
    result = model.transcribe('.temp')
    return result["text"].strip()

def click_checkbox(driver):
    driver.switch_to.default_content()
    driver.switch_to.frame(driver.find_element(By.XPATH, ".//iframe[@title='reCAPTCHA']"))
    driver.find_element(By.ID, "recaptcha-anchor-label").click()
    driver.switch_to.default_content()

def request_audio_version(driver):
    driver.switch_to.default_content()
    driver.switch_to.frame(driver.find_element(By.XPATH, ".//iframe[@title='recaptcha challenge expires in two minutes']"))
    driver.find_element(By.ID, "recaptcha-audio-button").click()

def solve_audio_captcha(driver):
    text = transcribe(driver.find_element(By.ID, "audio-source").get_attribute('src'))
    driver.find_element(By.ID, "audio-response").send_keys(text)
    driver.find_element(By.ID, "recaptcha-verify-button").click()

def captchasolve(driver, url):
    driver.get(url)
    click_checkbox(driver)
    time.sleep(1)
    request_audio_version(driver)
    time.sleep(1)
    solve_audio_captcha(driver)
    time.sleep(10)

def createDriver():
    driver = Driver(uc=True)
    return driver

def solveCaptcha(driver, url):
    driver.get(url)
    
    #captchasolve(url, driver)

driver = createDriver()
#driver.get("https://nowsecure.nl")
url = "https://www.google.com/recaptcha/api2/demo"
#url = "https://bot.sannysoft.com"
#solveCaptcha(driver, url)
captchasolve(driver, url)