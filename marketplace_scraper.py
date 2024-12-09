from splinter import Browser, Config
from bs4 import BeautifulSoup as soup
import pandas as pd
import time
import requests
from datetime import datetime
from tabulate import tabulate
import git
import os

# Set up Splinter
mobile_user_agent = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 "
    "Mobile/15E148 Safari/604.1"
)
config = Config(user_agent=mobile_user_agent, incognito=True, headless=True)

# Set up base url
base_url = "https://www.facebook.com/marketplace/108205955874066/search?"

# Set up search parameters
min_price = 1000
max_price = 30000
days_listed = 7
min_mileage = 50000
max_mileage = 200000
min_year = 2000
max_year = 2020
transmission = "automatic"
make = "Honda"
model = "Civic"
#Set up full url
url = f"{base_url}minPrice={min_price}&maxPrice={max_price}&daysSinceListed={days_listed}&maxMileage={max_mileage}&maxYear={max_year}&minMileage={min_mileage}&minYear={min_year}&transmissionType={transmission}&query={make}{model}&exact=false"

# Define the number of times to scroll the page
scroll_count = 1

# Define the delay (in seconds) between each scroll
scroll_delay = 1


repo_path = "/home/daniel/git/marketplace"
repo_url = "https://github.com/daniel-campa/marketplace.git"

content_path = os.path.join(repo_path, "docs/index.html")


while True:
    try:
        browser = Browser('chrome', config=config)
        browser.driver.maximize_window()

        # Visit the website
        browser.visit(url)

        if browser.is_element_present_by_css('div[aria-label="Close"]', wait_time=5):
            # Click on the element once it's found
            browser.find_by_css('div[aria-label="Close"]').first.click()


        # Loop to perform scrolling
        for _ in range(scroll_count):
            # Execute JavaScript to scroll to the bottom of the page
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Pause for a moment to allow the content to load
            time.sleep(scroll_delay)

        # Create a BeautifulSoup object from the scraped HTML
        market_soup = soup(browser.html, 'html.parser')

        # End the automated browsing session
        browser.quit()

        listings = market_soup.find_all('a', class_='x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1heor9g x1sur9pj xkrqix3 x1lku1pv')

        listings_df = pd.DataFrame()

        for item in listings:
            item_link = item.attrs['href']
            # image_link = item.findChild('img').attrs['src']
            item_data_div = item.findChild('div', class_='x9f619 x78zum5 xdt5ytf x1qughib x1rdy4ex xz9dl7a xsag5q8 xh8yej3 xp0eagm x1nrcals')

            price, name, location, mileage = [item_data.text for item_data in item_data_div.children]

            city, state = location.split(', ')
            
            item_dict = {
                'name': name,
                'price': price.split('$')[1],
                'mileage': mileage,
                'city': city,
                'state': state,
                'link': item_link
                # 'image': image_link
            }

            listings_df = pd.concat([listings_df, pd.DataFrame([item_dict])], ignore_index=True)

        listings_df.price = listings_df.price.str.replace(',','').astype(int)
        listings_df.mileage = listings_df.mileage.str.removesuffix('K miles').str.removesuffix('K miles · Dealership').astype(int) * 1000
        listings_df.insert(3, 'mp_ratio', listings_df.mileage / listings_df.price)

        listings_df.link = 'https://www.facebook.com' + listings_df.link

        out_df = listings_df.nsmallest(20, 'price')

        print(
            tabulate(out_df, headers='keys', tablefmt='psql', showindex=False, maxcolwidths=[None, None, None, None, None, None, 60])
        )

        out_df.to_html(content_path, index=False)


        repo = git.Repo(repo_path)
        repo.git.add(all=True)
        repo.index.commit("Updated dashboard")
        origin = repo.remote(name="origin")
        origin.push()

        time.sleep(900)

    except KeyboardInterrupt:
        print()
        break

# discord_url = 'https://discord.com/api/v9/channels/1315518691718463521/messages'

# payload = {'content': message}

# headers = {'authorization': 'token__'}

# response = requests.post(discord_url, payload, headers)