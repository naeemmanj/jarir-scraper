from scrapling.fetchers import StealthyFetcher
from urllib.parse import urljoin
import json

BASE_URL = "https://www.jarir.com"
START_URL = "https://www.jarir.com/sa-en/clearance-offers.html"

MAX_SCROLLS = 20

def scroll_page(page):
    """
    Scroll the listing page a maximum of 20 times.
    """

    previous_count = 0

    for scroll_no in range(1, MAX_SCROLLS + 1):

        current_count = page.locator("xpath=//a[contains(@class, 'product-tile__link')]").count()

        print(f"[Scroll {scroll_no}/{MAX_SCROLLS}] "f"Products loaded: {current_count}")

        # Scroll to bottom
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

        # Give JavaScript time to load products
        page.wait_for_timeout(3000)

        new_count = page.locator("xpath=//a[contains(@class, 'product-tile__link')]").count()

        print(f"[Scroll {scroll_no}/{MAX_SCROLLS}] "f"Products after scroll: {new_count}")

        # If no new products appeared
        if new_count <= previous_count:
            print(f"[Scroll {scroll_no}/{MAX_SCROLLS}] ""No new products loaded.")

        previous_count = new_count

    print("20 scroll rounds completed.")


def get_product_urls(page):
    """
    Extract all unique product URLs from the listing page.
    """

    urls = page.xpath("//a[contains(@class,'product-tile__link')]/@href").getall()

    product_urls = []

    for url in urls:

        if not url:
            continue

        # Convert relative URL to absolute URL
        full_url = urljoin(BASE_URL, url)

        if full_url not in product_urls:
            product_urls.append(full_url)

    return product_urls


def scrape_product(product_url):
    """
    Open one product page and extract all product information.
    """

    print(f"\nScraping product: {product_url}")

    product_page = StealthyFetcher.fetch(
        product_url,
        headless=True,
        load_dom=True,
        network_idle=True,
    )

    product = {
        "product_url": product_url,

        "product_name": product_page.xpath("//h1[@data-product-id]/text()").get(),
        "current_price": product_page.xpath("(//div[contains(@class,'price--pdp')]""//span[@class='price_alignment']""/text()[normalize-space()])[1]").get(),
        "old_price": product_page.xpath("(//div[contains(@class, 'page__main')]""//div[contains(@class,'price--old-red')]""//span[@class='price_alignment']""/text()[normalize-space()])[1]").get(),
        "discount": product_page.xpath("(//span[contains(@class,'badge--discount')]/text())[1]").get(),
        "currency": product_page.xpath("(//span[@class='price_alignment'])[3]""/span[1]/text()").get(),
        "image_url": product_page.xpath("(//img[contains(@src,'akeneo-prod') ""and contains(@src,'.jpg')]/@src)[1]").get(),
        "sku_id": product_page.xpath("(//b[@itemprop='sku'])[1]/text()").get(),
    }

    return product


def main():

    # ==========================================================
    # PHASE 1: OPEN LISTING PAGE AND COLLECT PRODUCT URLS
    # ==========================================================

    print("=" * 60)
    print("PHASE 1: SCRAPING LISTING PAGE")
    print("=" * 60)

    page = StealthyFetcher.fetch(
        START_URL,
        headless=True,
        load_dom=True,
        network_idle=True,
        page_action=scroll_page,
    )

    print("\nStatus:", page.status)
    print("URL:", page.url)
    print("Title:",page.xpath("//title/text()").get())

    product_urls = get_product_urls(page)

    print("\nTotal Product URLs:", len(product_urls))

    # Show URLs
    for index, product_url in enumerate(product_urls, start=1):
        print(f"{index}. {product_url}")

    # ==========================================================
    # PHASE 2: SCRAPE PRODUCT DETAILS
    # ==========================================================

    print("\n" + "=" * 60)
    print("PHASE 2: SCRAPING PRODUCT DETAILS")
    print("=" * 60)

    products = []

    for index, product_url in enumerate(product_urls, start=1):

        print(f"\nProduct {index}/{len(product_urls)}")

        try:
            product = scrape_product(product_url)
            products.append(product)

            print("Name:", product["product_name"])
            print("Current price:", product["current_price"])
            print("Old price:", product["old_price"])
            print("Discount:", product["discount"])
            print("Currency:", product["currency"])
            print("SKU:", product["sku_id"])
            print("Image:", product["image_url"])

        except Exception as e:

            print(f"ERROR scraping {product_url}: {e}")
    # ==========================================================
    # SAVE DATA TO JSON
    # ==========================================================
    with open("products.json", "w") as file:
        json.dump(
            products,
            file,
            indent=4,
        )
    print("\nProduct data saved to products.json")
    print("Product URLs found:", len(product_urls))
    print("Products scraped:", len(products))

    # ==========================================================
    # FINAL RESULT
    # ==========================================================

    print("\n" + "=" * 60)
    print("SCRAPING COMPLETED")
    print("=" * 60)

    print("Product URLs found:", len(product_urls))
    print("Products scraped:", len(products))

    for product in products:
        print("\n", product)


if __name__ == "__main__":
    main()