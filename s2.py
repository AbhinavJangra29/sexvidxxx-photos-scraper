from typing import *
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
import json

chrome_driver_path = './chromedriver.exe'
service = Service(chrome_driver_path)

# Add Chrome options to block ads
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--disable-notifications')
chrome_options.add_argument('--disable-popup-blocking')
chrome_options.add_argument('--disable-infobars')
chrome_options.add_experimental_option("prefs", {
    "profile.default_content_setting_values.notifications": 2,
    "profile.default_content_settings.popups": 0
})

driver = webdriver.Chrome(service=service, options=chrome_options)
driver.maximize_window()

base_url = 'https://www.sexvid.xxx/photos/{}/'
start_page = 1
end_page = 3

image_data = []

def get_thumbnails():
    return WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.th_model.th_album'))
    )

def safe_click(element):
    try:
        # Scroll element into view
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", element)
        time.sleep(1)  # Small delay after scrolling
        
        try:
            # Try regular click first
            element.click()
        except ElementClickInterceptedException:
            # If regular click fails, try JavaScript click
            driver.execute_script("arguments[0].click();", element)
            
    except Exception as e:
        print(f"Click failed with error: {str(e)}")
        raise e

for page_num in range(start_page, end_page + 1):
    url = base_url.format(page_num)
    print("this is the url:", url)
    driver.get(url)
    
    # Wait for the page to stabilize
    time.sleep(3)
    
    thumbnails = get_thumbnails()
    print("Number of items on the page:", len(thumbnails))
    
    thumbnail_indices = list(range(len(thumbnails)))
    
    for index in thumbnail_indices:
        max_retries = 3
        current_retry = 0
        
        while current_retry < max_retries:
            try:
                # Check if URL is valid
                current_url = driver.current_url
                if current_url.startswith("data:"):
                    print("Invalid URL detected, refreshing page...")
                    driver.get(url)
                    time.sleep(3)
                
                # Get fresh thumbnails and try to click
                thumbnails = get_thumbnails()
                safe_click(thumbnails[index])
                
                # Wait for gallery to load
                gallery_holder = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.gallery-holder.js-album'))
                )
                
                # Find all 'item' elements within the gallery holder
                item_elements = gallery_holder.find_elements(By.CLASS_NAME, 'item')
                
                for item in item_elements:
                    img_src = item.find_element(By.TAG_NAME, 'img').get_attribute('src')
                    if img_src and not img_src.startswith("data:"):
                        image_data.append(img_src)
                        print("Found image source:", img_src)
                
                # Successfully processed this thumbnail, break the retry loop
                break
                
            except Exception as e:
                print(f"Error processing thumbnail {index} (attempt {current_retry + 1}/{max_retries}):", str(e))
                current_retry += 1
                
                if current_retry < max_retries:
                    print("Retrying...")
                    time.sleep(2)
                    driver.refresh()
                    time.sleep(3)
            
        # Navigate back to the thumbnails page
        driver.back()
        time.sleep(3)

# Write the image sources to a JSON file
with open("image_sources.json", "w") as json_file:
    json.dump(image_data, json_file, indent=4)

driver.quit()