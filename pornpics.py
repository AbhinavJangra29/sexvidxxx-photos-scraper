from typing import *
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import json
import concurrent.futures
from pathlib import Path

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
    chrome_options.add_argument('--headless=new')
    service = Service('./chromedriver')
    return webdriver.Chrome(service=service, options=chrome_options)

def scroll_and_get_albums(driver, max_scroll_attempts=75) -> Set[str]:
    """Scrolls down the page and collects all unique album links."""
    all_albums = set()
    consecutive_same_count = 0
    scroll_height = 300
    
    for scroll_attempt in range(max_scroll_attempts):
        try:
            current_position = driver.execute_script("return window.pageYOffset;")
            total_height = driver.execute_script("return document.documentElement.scrollHeight;")
            
            new_position = min(current_position + scroll_height, total_height - 800)
            driver.execute_script(f"window.scrollTo(0, {new_position});")
            
            time.sleep(2)
            
            albums = driver.find_elements(By.CSS_SELECTOR, ".wookmark-initialised .thumbwook.in a")
            current_albums = {album.get_attribute("href") for album in albums if album.get_attribute("href")}
            
            previous_count = len(all_albums)
            all_albums.update(current_albums)
            
            if scroll_attempt % 5 == 0:
                print(f"[{driver.current_url}] Scroll attempt {scroll_attempt}/{max_scroll_attempts}")
                print(f"Found {len(all_albums)} unique albums so far")
            
            if len(all_albums) == previous_count:
                consecutive_same_count += 1
                if consecutive_same_count >= 3:
                    scroll_height = min(scroll_height + 100, 800)
                    driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
                    time.sleep(3)
                    consecutive_same_count = 0
            else:
                consecutive_same_count = 0
                scroll_height = 300
            
            if new_position >= total_height - 1000 and consecutive_same_count >= 5:
                print(f"[{driver.current_url}] Reached the bottom of the page")
                break
                
        except Exception as e:
            print(f"[{driver.current_url}] Error during scrolling: {str(e)}")
            time.sleep(2)
            continue
    
    return all_albums

def process_album(driver, album_url) -> Set[str]:
    """Process a single album and extract unique image links."""
    try:
        driver.get(album_url)
        time.sleep(3)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".wookmark-initialised"))
        )
        
        images = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".wookmark-initialised .thumbwook a"))
        )
        
        return {img.get_attribute("href") for img in images if img.get_attribute("href")}
        
    except (TimeoutException, StaleElementReferenceException) as e:
        print(f"Error processing album {album_url}: {str(e)}")
        return set()

def process_topic(topic: str) -> Dict[str, Any]:
    """Process a single topic and return statistics and image links."""
    driver = create_driver()
    all_image_links = set()  # Using set for automatic deduplication
    stats = {
        "topic": topic,
        "start_time": time.time(),
        "albums_processed": 0,
        "total_albums": 0,
        "unique_images": 0
    }
    
    try:
        base_url = f"https://www.pornpics.com/{topic}/"
        print(f"Starting processing for topic: {topic}")
        
        driver.get(base_url)
        driver.maximize_window()
        time.sleep(5)
        
        album_links = scroll_and_get_albums(driver)
        stats["total_albums"] = len(album_links)
        print(f"[{topic}] Found total of {len(album_links)} unique albums")
        
        for album_url in album_links:
            stats["albums_processed"] += 1
            print(f"[{topic}] Processing album {stats['albums_processed']}/{stats['total_albums']}")
            
            image_links = process_album(driver, album_url)
            all_image_links.update(image_links)
            stats["unique_images"] = len(all_image_links)
            
            print(f"[{topic}] Current unique images: {stats['unique_images']}")
    
    except Exception as e:
        print(f"Error in topic {topic}: {str(e)}")
        
    finally:
        driver.quit()
        stats["end_time"] = time.time()
        stats["duration"] = stats["end_time"] - stats["start_time"]
        
        # Save results for this topic
        result = {
            "stats": stats,
            "urls": list(all_image_links)
        }
        
        output_dir = Path("results")
        output_dir.mkdir(exist_ok=True)
        
        with open(output_dir / f"{topic}_results.json", "w") as f:
            json.dump(result, f, indent=4)
        
        print(f"\nTopic {topic} completed:")
        print(f"Total albums processed: {stats['albums_processed']}")
        print(f"Total unique images: {stats['unique_images']}")
        print(f"Duration: {stats['duration']:.2f} seconds")
    
    return result

def process_topic_batch(topics: List[str]):
    """Process a batch of topics concurrently."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(topics)) as executor:
        future_to_topic = {executor.submit(process_topic, topic): topic for topic in topics}
        for future in concurrent.futures.as_completed(future_to_topic):
            topic = future_to_topic[future]
            try:
                result = future.result()
                print(f"\nCompleted topic {topic}:")
                print(f"Processed {result['stats']['albums_processed']} albums")
                print(f"Found {result['stats']['unique_images']} unique images")
                print(f"Duration: {result['stats']['duration']:.2f} seconds")
            except Exception as e:
                print(f"Error processing topic {topic}: {str(e)}")

def main():
    start_time = time.time()
    
    # Read topics from file
    with open("pornpics.txt", "r") as f:
        topics = [line.strip() for line in f.readlines() if line.strip()]
    
    # Process topics in batches of 5
    batch_size = 5
    total_batches = (len(topics) + batch_size - 1) // batch_size
    
    for i in range(0, len(topics), batch_size):
        batch = topics[i:i + batch_size]
        current_batch = i//batch_size + 1
        print(f"\nProcessing batch {current_batch}/{total_batches}: {batch}")
        process_topic_batch(batch)
        print(f"Completed batch {current_batch}/{total_batches}")
    
    duration = time.time() - start_time
    print(f"\nAll processing completed in {duration:.2f} seconds")

if __name__ == "__main__":
    main()