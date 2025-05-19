from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
import logging
import time
from urls import urls


# Elasticsearch connection
try:
    es_connection = Elasticsearch("http://localhost:9200", verify_certs=True)
    if not es_connection.ping():
        print("Elasticsearch connection failed.")
    else:
        print("Connected to Elasticsearch successfully.")
except ConnectionError:
    print("Error: Unable to connect to Elasticsearch. Check your host and network settings.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

index_name = "mana_products"


# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")



# Setup Chrome options
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("log-level=3")

for url in urls:
    print("***********************************************************")
    logging.info(f"Scraping URL: {url}")

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        time.sleep(4)  # Wait for the page to load
    except WebDriverException as e:
        logging.error(f"WebDriver error: {e}")
        continue

    try:
        # Use BeautifulSoup for parsing the HTML
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        product_data = {}

        # ✅ Extract availability
        availability_tag = soup.select_one("div.stock.available span")
        product_data['availability'] = availability_tag.text.strip() if availability_tag else None

        # ✅ Extract product code
        product_code_tag = soup.select_one("div.product.attribute.sku > div.value")
        product_data['product_code'] = product_code_tag.text.strip() if product_code_tag else None

        # ✅ Extract price
        price_tag = soup.select_one("span.price-wrapper span.price")
        product_data['price'] = price_tag.text.strip() if price_tag else None

        # ✅ Extract technical specs from table
        table = soup.find("tbody")
        data_technical = {}

        if table:
            rows = table.find_all("tr")
            for row in rows:
                key_tag = row.find("th")
                value_tag = row.find("td")
                if key_tag and value_tag:
                    key = key_tag.get_text(strip=True).replace(":", "")
                    value = value_tag.get_text(strip=True)
                    data_technical[key] = value
        else:
            logging.warning(f"No technical table found at {url}")

        # ✅ Merge technical data
        product_data['technical_specs'] = data_technical

        # ✅ index the result
        response = es_connection.index(index=index_name, document=product_data)

    except (NoSuchElementException, TimeoutException) as e:
        logging.error(f"Error parsing {url}: {e}")

    finally:
        driver.quit()
