from splinter import Browser, Config
from bs4 import BeautifulSoup as soup
import pandas as pd
import locale
from locale import atof
import time
# import requests
from datetime import datetime
from tabulate import tabulate
import git
import os
import argparse

pd.set_option('display.max_colwidth', None)

parser = argparse.ArgumentParser(description="Filter listings based on criteria.")

parser.add_argument("--base-url", type=str, default="https://www.facebook.com/marketplace/108205955874066/search?", help="Base url")

parser.add_argument("--name", type=str, default="iPhone", help="Name of the item")
parser.add_argument("--min-price", type=int, default=100, help="Minimum price of the item")
parser.add_argument("--max-price", type=int, default=2500, help="Maximum price of the item")
parser.add_argument("--days-listed", type=int, default=1, help="Maximum number of days the item has been listed")

parser.add_argument("--scroll-count", type=int, default=4, help="Scroll count")
parser.add_argument("--scroll-delay", type=int, default=2, help="Scroll delay")

parser.add_argument("--headless", action="store_true", help="Browser config option")

args = parser.parse_args()


# Set up base url
base_url = args.base_url

# Set up search parameters
name = args.name
min_price = args.min_price
max_price = args.max_price
days_listed = args.days_listed

#Set up full url
url = f"{base_url}minPrice={min_price}&maxPrice={max_price}&daysSinceListed={days_listed}&query={name}&exact=false"

# Define the number of times to scroll the page
scroll_count = args.scroll_count

# Define the delay (in seconds) between each scroll
scroll_delay = args.scroll_delay

# Set up Splinter
mobile_user_agent = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 "
    "Mobile/15E148 Safari/604.1"
)
config = Config(user_agent=mobile_user_agent, incognito=True, headless=args.headless)


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

        if browser.is_element_present_by_css('div[aria-label="OK"]', wait_time=5):
            # Click on the element once it's found
            browser.find_by_css('div[aria-label="OK"]').first.click()


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

            text_data = [item_data.text for item_data in item_data_div.children]

            price = text_data[0]
            name = text_data[1]
            location = text_data[2]

            try:
                city, state = location.split(', ')
            except ValueError:
                print(location)
                city, state = location, location

            if len(text_data) > 3:
                extra = text_data[3:]
            else:
                extra = []
            
            item_dict = {
                'name': name,
                'price': price,
                'city': city,
                'state': state,
                'extra': extra,
                'link': item_link
                # 'image': image_link
            }

            listings_df = pd.concat([listings_df, pd.DataFrame([item_dict])], ignore_index=True)

        listings_df.link = 'https://www.facebook.com' + listings_df.link
        listings_df.link = listings_df.link.apply(lambda link: f'<a href="{link}" target="_blank">{link}</a>')

        try:
            listings_df.price = listings_df.price.str.replace(',','').astype(int)

            out_df = listings_df.sort_values(['price'])

        except ValueError:
            out_df = listings_df

        # listings_df.image = listings_df.image.apply(lambda img_link: f'<img src={img_link} alt="{img_link}" >')
        # out_df.drop(['image'], axis=1, inplace=True)

        print(
            tabulate(out_df, headers='keys', tablefmt='psql', showindex=False, maxcolwidths=[60, 6, 17, 5, 10, 70])
        )

        out_df.to_html(content_path, index=False, escape=False, classes=['table table-stripped'])
        print(out_df.shape)


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