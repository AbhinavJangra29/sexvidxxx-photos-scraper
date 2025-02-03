from typing import *
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

def create_driver():
    chrome_options = webdriver.ChromeOptions()
    # Performance optimizations
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-popup-blocking')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--blink-settings=imagesEnabled=true')
    chrome_options.add_argument('--disable-javascript')
    # Add these new options to suppress media-related errors
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-accelerated-video-decode')
    chrome_options.add_argument('--disable-accelerated-video-encode')
    chrome_options.add_argument('--autoplay-policy=no-user-gesture-required')
    chrome_options.add_argument('--disable-features=MediaEngagement')
    
    # Suppress logging
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.page_load_strategy = 'eager'
    
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
        "profile.managed_default_content_settings.images": 1,
        "profile.default_content_setting_values.cookies": 1,
        # Add these preferences to further reduce media-related issues
        "media.autoplay.enabled": False,
        "media.audio_video_capture.enabled": False
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    service = Service('./chromedriver.exe')
    return webdriver.Chrome(service=service, options=chrome_options)

def process_page(page_num, base_url):
    driver = create_driver()
    driver.maximize_window()
    image_data = []
    
    try:
        url = base_url.format(page_num)
        print(f"Processing page {page_num}: {url}")
        driver.get(url)
        
        def get_thumbnails():
            return WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.th_model.th_album'))
            )

        def safe_click(element):
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                try:
                    element.click()
                except ElementClickInterceptedException:
                    driver.execute_script("arguments[0].click();", element)
            except Exception as e:
                print(f"Click failed: {str(e)}")
                raise e

        thumbnails = get_thumbnails()
        print(f"Found {len(thumbnails)} thumbnails on page {page_num}")
        
        for index in range(len(thumbnails)):
            max_retries = 5
            current_retry = 0
            
            while current_retry < max_retries:
                try:
                    if driver.current_url.startswith("data:"):
                        driver.get(url)
                    
                    thumbnails = get_thumbnails()
                    safe_click(thumbnails[index])
                    
                    gallery_holder = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.gallery-holder.js-album'))
                    )
                    
                    # Process all images in parallel
                    img_elements = gallery_holder.find_elements(By.CSS_SELECTOR, '.item img')
                    img_sources = [elem.get_attribute('src') for elem in img_elements]
                    valid_sources = [src for src in img_sources if src and not src.startswith("data:")]
                    image_data.extend(valid_sources)
                    
                    print(f"Page {page_num}, Thumbnail {index + 1}: Found {len(valid_sources)} images")
                    break
                    
                except Exception as e:
                    print(f"Error on page {page_num}, thumbnail {index} (attempt {current_retry + 1}/{max_retries}): {str(e)}")
                    current_retry += 1
                    if current_retry < max_retries:
                        driver.refresh()
                
                finally:
                    driver.back()
                    
    finally:
        driver.quit()
        
    return image_data

def main():
    base_url = 'https://www.sexvid.xxx/photos/{}/'
    start_page = 1
    end_page = 1677
    all_image_data = []
    
    # Process pages in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_page = {
            executor.submit(process_page, page_num, base_url): page_num 
            for page_num in range(start_page, end_page + 1)
        }
        
        for future in as_completed(future_to_page):
            page_num = future_to_page[future]
            try:
                page_data = future.result()
                all_image_data.extend(page_data)
                print(f"Completed page {page_num} with {len(page_data)} images")
            except Exception as e:
                print(f"Page {page_num} generated an exception: {str(e)}")

    # Write results
    with open("image_sources.json", "w") as json_file:
        json.dump(all_image_data, json_file, indent=4)
        
    print(f"Total images collected: {len(all_image_data)}")

if __name__ == "__main__":
    start_time = time.time()
    main()
    print(f"Total execution time: {time.time() - start_time:.2f} seconds")
