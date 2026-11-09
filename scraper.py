import requests
import pandas as pd
import time

from bs4 import BeautifulSoup
from urllib.parse import urljoin


BASE_URL = "https://books.toscrape.com/catalogue/"


def scrape_page(page_number):

    # Fetch and parse the webpage
    url = f"{BASE_URL}page-{page_number}.html"

    response = requests.get(url, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Find all books
    books = soup.select("article.product_pod")

    # Extract book information
    book_data = []

    for book in books:

        title_tag = book.select_one("h3 a")

        title = title_tag.get("title")

        product_url = urljoin(
            url,
            title_tag.get("href")
        )

        price = book.select_one(
            ".price_color"
        ).get_text(strip=True)

        rating_tag = book.select_one("p.star-rating")

        rating = next(
            (
                cls for cls in rating_tag.get("class", [])
                if cls in ["One", "Two", "Three", "Four", "Five"]
            ),
            None
        )

        availability = book.select_one(
            ".instock.availability"
        ).get_text(strip=True)

        book_data.append({
            "title": title,
            "price": price,
            "rating": rating,
            "availability": availability,
            "product_url": product_url
        })

    return book_data

# Scrape three pages

all_books = []

for page in range(1,4):
    print(f"Scraping page {page}...")

    books = scrape_page(page)

    all_books.extend(books)

    print(f"Extracted {len(books)} books")

    time.sleep(1)

df = pd.DataFrame(all_books)

# Inspect data

print(f"\nTotal books scraped: {len(df)}")

print(df.head())

print(df.info())

print(df.isnull().sum())

# Check for duplicate books
print("Duplicate URLs:", df["product_url"].duplicated().sum())

# Convert prices to numerical values
df["price"] = (
    df["price"]
    .str.replace(r"[^\d.]", "", regex=True)
    .astype(float)
)

# Convert ratings to integers
rating_map = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5
}

df["rating"] = df ["rating"].map(rating_map)

# Remove duplicates
df = df.drop_duplicates(subset=["product_url"])

print(df.isnull().sum())

# Validate
assert df["product_url"].is_unique
assert df["price"].notna().all()
assert df["rating"].between(1, 5).all()

print("Dataset validation passed!")

# Export to CSV
import os

os.makedirs("data", exist_ok=True)

df.to_csv("data/books.csv", index=False)

print("Dataset saved successfully!")