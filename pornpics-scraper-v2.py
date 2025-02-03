from typing import *
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import json

def create_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-popup-blocking')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service('./chromedriver.exe')
    return webdriver.Chrome(service=service, options=chrome_options)

def scroll_and_get_albums(driver, max_scroll_attempts=150):
    """Scrolls down the page and collects all album links with improved loading handling."""
    all_albums = set()
    last_len = 0
    scroll_attempt = 0
    consecutive_same_count = 0
    scroll_height = 300  # Start with smaller scroll increments
    
    while scroll_attempt < max_scroll_attempts:
        try:
            # Get current scroll position and page height
            current_position = driver.execute_script("return window.pageYOffset;")
            total_height = driver.execute_script("return document.documentElement.scrollHeight;")
            
            # Scroll down gradually
            new_position = min(current_position + scroll_height, total_height - 800)
            driver.execute_script(f"window.scrollTo(0, {new_position});")
            
            # Wait for content to load - increased wait time
            time.sleep(2)
            
            # Get all current albums
            albums = driver.find_elements(By.CSS_SELECTOR, ".wookmark-initialised .thumbwook.in a")
            current_albums = set(album.get_attribute("href") for album in albums if album.get_attribute("href"))
            
            # Add new albums to our collection
            previous_count = len(all_albums)
            all_albums.update(current_albums)
            
            # Print progress
            if scroll_attempt % 5 == 0:
                print(f"Scroll attempt {scroll_attempt}/{max_scroll_attempts}")
                print(f"Current position: {new_position}/{total_height}")
                print(f"Found {len(all_albums)} albums so far")
                print("---")
            
            # Check if we're finding new content
            if len(all_albums) == previous_count:
                consecutive_same_count += 1
                # If we haven't found new content in a while, try scrolling more aggressively
                if consecutive_same_count >= 3:
                    scroll_height = min(scroll_height + 100, 800)  # Increase scroll amount up to a max
                    driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
                    time.sleep(3)  # Wait longer after aggressive scroll
                    consecutive_same_count = 0  # Reset counter
            else:
                consecutive_same_count = 0
                scroll_height = 300  # Reset to smaller increments when finding new content
            
            # Check if we've reached the bottom
            if new_position >= total_height - 1000 and consecutive_same_count >= 5:
                print("Reached the bottom of the page")
                break
                
            scroll_attempt += 1
            
        except Exception as e:
            print(f"Error during scrolling: {str(e)}")
            time.sleep(2)
            continue
    
    return list(all_albums)

def process_album(driver, album_url):
    """Process a single album and extract image links."""
    try:
        driver.get(album_url)
        time.sleep(3)  # Wait for initial load
        
        # First wait for the container to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".wookmark-initialised"))
        )
        
        # Then get all images
        images = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".wookmark-initialised .thumbwook a"))
        )
        
        image_links = [img.get_attribute("href") for img in images if img.get_attribute("href")]
        return image_links
        
    except (TimeoutException, StaleElementReferenceException) as e:
        print(f"Error processing album {album_url}: {str(e)}")
        return []

def main():
    driver = create_driver()
    all_image_links = []
    base_url = "https://www.pornpics.com/pussy-licking/"  # Replace with your target URL
    
    try:
        print("Starting browser...")
        driver.get(base_url)
        driver.maximize_window()
        time.sleep(5)  # Give initial page more time to load
        
        print("Starting to collect album links...")
        album_links = scroll_and_get_albums(driver)
        print(f"\nFound total of {len(album_links)} albums")
        
        # Process each album
        for i, album_url in enumerate(album_links, 1):
            print(f"Processing album {i}/{len(album_links)}")
            image_links = process_album(driver, album_url)
            all_image_links.extend(image_links)
            print(f"Found {len(image_links)} images in album")
            
            # Save progress every 10 albums
            if i % 10 == 0:
                with open(f"image_links_checkpoint_{i}.json", "w") as f:
                    json.dump(all_image_links, f, indent=4)
                    
    finally:
        driver.quit()
    
    # Save final results
    with open("pornpics_links.json", "w") as f:
        json.dump(all_image_links, f, indent=4)
    
    print(f"Total images collected: {len(all_image_links)}")

if __name__ == "__main__":
    start_time = time.time()
    main()
    print(f"Total execution time: {time.time() - start_time:.2f} seconds")