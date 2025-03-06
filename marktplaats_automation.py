from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time
import json
import os
import requests
import traceback
import datetime
from dotenv import load_dotenv
from webdriver_manager.chrome import ChromeDriverManager
from plyer import notification
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# load sensitive data
load_dotenv()

# pushover credentials
USER_KEY = os.getenv("USER_KEY")
API_TOKEN = os.getenv("API_TOKEN")

# Google login credentials
GOOGLE_EMAIL = os.getenv("GOOGLE_EMAIL")
GOOGLE_PASSWORD = os.getenv("GOOGLE_PASSWORD")

# Set up Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--disable-notifications")
options.add_argument(r"user-data-dir=C:\Users\markh\AppData\Local\Google\Chrome\User Data")
options.add_argument("profile-directory=Default")
options.add_argument("--disable-gpu")

chromedriver_path = r"C:\Niet synchroniseren\chromedriver-win64\chromedriver-win64\chromedriver.exe"
driver = webdriver.Chrome(service = Service(chromedriver_path), options=options)

# Open Marktplaats and log in manually
driver.get("https://www.marktplaats.nl/identity/v2/login")
input("Log in manually, then press Enter here...")  # Wait for manual login

# Save cookies to a file
cookies = driver.get_cookies()
with open("fb_cookies.json", "w") as file:
    json.dump(cookies, file)

print("✅ Cookies saved! You can now use them to log in automatically.")
driver.quit()

# Marktplaats URL with filters
#MARKETPLACE_URL = "https://www.marktplaats.nl/l/sport-en-fitness/#offeredSince:Vandaag|sortBy:SORT_INDEX|sortOrder:DECREASING|postcode:8071NS"
MARKETPLACE_URL = "https://www.marktplaats.nl/l/spelcomputers-en-games/spelcomputers-nintendo-ds/#q:nintendo+ds|offeredSince:Vandaag|sortBy:SORT_INDEX|sortOrder:DECREASING|postcode:8071NS"

# Set up Selenium WebDriver
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def load_cookies():
    """Loads Marktplaats cookies to avoid login."""
    driver.get("https://www.marktplaats.nl/")  # Open Marktplaats to set cookies
    time.sleep(2)

    # Load saved cookies
    with open("fb_cookies.json", "r") as file:
        cookies = json.load(file)

    for cookie in cookies:
        driver.add_cookie(cookie)

    # Reload the page after adding cookies to ensure session is set correctly
    driver.refresh()
    time.sleep(3)  # Wait for the page to reload

    # Navigate to the filtered marketplace page
    driver.get(MARKETPLACE_URL)
    time.sleep(3)  # Wait for the filtered page to load

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//ul[@class='hz-Listings hz-Listings--list-view']")))

    driver.get(MARKETPLACE_URL)  # Now open Marketplace with cookies
    time.sleep(3)

def get_listings():
    """Fetches the current listings from Marketplace."""
    driver.get(MARKETPLACE_URL)

    # Wait until the listings section is visible before proceeding
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//ul[@class='hz-Listings hz-Listings--list-view']")))

    # Get the list of items
    items = driver.find_elements(By.XPATH, "//div[@class='hz-Listing-listview-content']")
    listings = []

    # Get info of every listing
    for item in items:
        # skip if it is an ad
        seller_link = item.find_element(By.XPATH, ".//span[@class='hz-Listing-seller-link']").text
        if seller_link:
            continue
        try:
            item.find_element(By.XPATH, ".//a[@class='hz-Link hz-Link--isolated hz-Listing-sellerCoverLink hz-TextLink']")
            continue

        # find info if it is not an ad
        except Exception as e:
            try:
                # Extract title
                title = item.find_element(By.XPATH, ".//h3[@class='hz-Listing-title']").text

                # extract link
                temp = item.find_element(By.XPATH, ".//a[@class='hz-Link hz-Link--block hz-Listing-coverLink']")
                ActionChains(driver).move_to_element(temp).perform()  # Hover over the element
                time.sleep(0.5)  # Allow time for the href to load
                link = temp.get_attribute("href")

                # Extracting the price
                try:
                    price = item.find_element(By.XPATH, ".//p[contains(@class, 'hz-Listing-price')]").text
                    if not price:
                        price = item.find_element(By.XPATH, ".//span[contains(@class, 'hz-Listing-price')]").text

                except Exception as e:
                    print(f"Error fetching price for {title}: {e}")
                    price = "N/A"  # Default value if price is not found

                listings.append({"title": title, "price": price, "link": link})

            except Exception as e:
                print(f"Error fetching listing data for {title}: {e}")
                continue  # Skip items that don't match

    return listings

def load_previous_listings():
    """Loads previous listings from file."""
    filename = "listings.json"

    # If the file doesn't exist, return an empty list
    if not os.path.exists(filename):
        print("⚠️ listings.json not found. Creating a new one...")
        return []

    try:
        with open(filename, "r") as f:
            data = f.read().strip()  # Remove extra spaces/newlines

            if not data:  # If the file is empty, return an empty list
                print("⚠️ listings.json is empty. Returning an empty list...")
                return []

            return json.loads(data)  # Parse JSON normally

    except json.JSONDecodeError:
        print("❌ Error: listings.json is corrupted. Resetting file...")
        return []  # Return an empty list instead of crashing

def save_listings(listings):
    """Saves listings to file."""
    with open("listings.json", "w") as f:
        json.dump(listings, f, indent=4)

def log_error(error_message):
    """Logs the error to a file with a timestamp."""
    with open("error_log.txt", "a") as f:
        f.write(f"{datetime.datetime.now()} - {error_message}\n")
    print("Error logged!")

def check_internet():
    """Checks if there is an internet connection."""
    try:
        requests.get("https://www.google.com", timeout=5)
        return True
    except requests.ConnectionError:
        return False

def send_pushover_notification(title, message, url):
    """Sends a Pushover notification to phone"""
    try:
        api_url = 'https://api.pushover.net:443/1/messages.json'
        data = {
            'token': API_TOKEN,
            'user': USER_KEY,
            'message': message,
            'title': title,
            'url': url,
        }
        response = requests.post(api_url, data=data)

        print("Notification sent successfully!")

    except requests.exceptions.RequestException:
        send_desktop_notification("❌ Pushover Error", "Failed to send notification!")

def send_desktop_notification(title, message):
    """Shows a desktop notification."""
    notification.notify(
        title=title,
        message=message,
        app_name="Marktplaats",
        timeout=10
    )

def send_delayed_notification(error_message):
    """Waits for internet reconnection and then sends a notification."""
    print("🔴 No internet connection. Waiting to send notification...")
    while not check_internet():
        time.sleep(30)  # Check every 30 seconds
    print("✅ Internet reconnected! Sending crash notification...")
    send_pushover_notification("⚠️ Bot Crashed!", error_message, MARKETPLACE_URL)

def remove_files():
    files_to_remove = ["listings.json"]
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
            print(f"Removed {file}")
        else:
            print(f"{file} does not exist, skipping.")

def main():
    global driver
    remove_files()
    load_cookies()

    # Check if this is the first run (file doesn't exist)
    first_run = not os.path.exists("listings.json")

    try:

        while True:
            print("Checking for new listings...")
            driver.refresh()
            time.sleep(3)

            # After scrolling and waiting for content to load, fetch the listings
            new_listings = get_listings()
            old_listings = load_previous_listings()

            # Compare old and new listings
            old_titles = {item['title'] for item in old_listings}
            new_items = [item for item in new_listings if item['title'] not in old_titles]

            if new_items:
                print(f"🔔 Found {len(new_items)} new listings!")

                if not first_run:
                    for item in new_items:
                        title = item['title']
                        message = f"New Listing: {item['title']}\nPrice: {item['price']}"
                        url = item['link']
                        send_pushover_notification(title, message, url)

                save_listings(new_listings)
            else:
                print("No new listings.")

            # After the first run, set `first_run` to False
            first_run = False

            #time.sleep(25)
    except Exception as e:
        error_message = f"Bot crashed: {str(e)}\n{traceback.format_exc()}"
        log_error(error_message)
        send_desktop_notification("⚠️ Bot Crashed!", "Check logs for details.")

        # if internet is up, notify me of the error than crash the program
        if check_internet():
            send_pushover_notification("⚠️ Bot Crashed!", error_message, MARKETPLACE_URL)
            raise e
        else:
            print("🔴 No internet. Checking every 30 seconds...")
            down_time = datetime.datetime.now()

            while not check_internet():
                time.sleep(30)

            up_time = datetime.datetime.now()
            downtime_duration = up_time - down_time

            recovery_message = f"🌍 Internet Restored!\n⏳ Downtime: {downtime_duration}\n⏱️ Down: {down_time}\n⏱️ Back: {up_time}"
            send_pushover_notification("✅ Internet Back Online", recovery_message, MARKETPLACE_URL)
            send_desktop_notification("✅ Internet Back!", f"Down for {downtime_duration}")

        print("🔄 Restarting bot...")
        time.sleep(5)
        main()  # Restart the bot

if __name__ == "__main__":
    main()
