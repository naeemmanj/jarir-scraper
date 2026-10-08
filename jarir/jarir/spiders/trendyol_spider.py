import json
from urllib.parse import urljoin
from scrapling.fetchers import StealthyFetcher


START_URL = "https://www.trendyol.sa/en/sr?tag=flashsale1"
BASE_URL = "https://www.trendyol.sa"

PRODUCT_XPATH = "//a[contains(@class,'product-card')]/@href"

NAME_XPATH = "//h1[@data-testid='product-title']/text()[normalize-space()]"

CURRENT_PRICE_XPATH = (
    "(//div[@class='p-sale-price']//span[@class='integer-part'])[1]/text()"
)

OLD_PRICE_XPATH = (
    "//section[@class='main']//div[@class='p-strikethrough-price']/text()"
    " | "
    "//span[@class='original-price']/text()"
)

DISCOUNT_XPATH = (
    "//div[@data-drroot='product-detail']"
    "//div[@data-testid='discount-badge']//text()"
)

IMAGE_XPATH = (
    "(//img[contains(@class,'_carouselImage_abb7111')]/@src)[1]"
)

MAX_SCROLLS = 1
SCROLL_WAIT = 4000

all_product_urls = set()


def scroll_page(page):
    previous_url = ""

    for scroll in range(1, MAX_SCROLLS + 1):

        # Get currently loaded product links
        links = page.locator(
            "xpath=//a[contains(@class,'product-card')]"
        ).all()

        # Collect URLs
        for link in links:
            href = link.get_attribute("href")

            if href:
                url = urljoin(BASE_URL, href)
                all_product_urls.add(url)

        current_url = page.url

        print(
            f"Scroll {scroll}: "
            f"{len(links)} visible | "
            f"{len(all_product_urls)} total unique | "
            f"{current_url}"
        )

        # Scroll down
        page.evaluate("""
            window.scrollBy({
                top: window.innerHeight * 5,
                behavior: 'instant'
            });
        """)

        # Wait for new products
        page.wait_for_timeout(SCROLL_WAIT)

        # Check URL after scrolling
        new_url = page.url

        if new_url != previous_url:
            print(f"Page changed: {new_url}")

        previous_url = new_url

    # Final collection
    links = page.locator(
        "xpath=//a[contains(@class,'product-card')]"
    ).all()

    for link in links:
        href = link.get_attribute("href")

        if href:
            url = urljoin(BASE_URL, href)
            all_product_urls.add(url)

    print(
        f"\nTotal unique product URLs: "
        f"{len(all_product_urls)}"
    )


def get_text(response, xpath):
    values = response.xpath(xpath)

    if not values:
        return None

    return str(values[0]).strip()


def scrape_product(url, number, total):
    print(f"\n========== PRODUCT {number}/{total} ==========")
    print(f"URL: {url}")

    try:
        response = StealthyFetcher.fetch(
            url,
            headless=False,
            load_dom=True,
            network_idle=True,
            wait=1000,
        )

        print(f"Status: {response.status}")

        name = get_text(
            response,
            NAME_XPATH
        )

        current_price = get_text(
            response,
            CURRENT_PRICE_XPATH
        )

        old_price = get_text(
            response,
            OLD_PRICE_XPATH
        )

        discount = get_text(
            response,
            DISCOUNT_XPATH
        )

        image_url = get_text(
            response,
            IMAGE_XPATH
        )

        product = {
            "url": url,
            "name": name,
            "current_price": current_price,
            "old_price": old_price,
            "discount": discount,
            "image_url": image_url,
        }

        print(f"Name: {name}")
        print(f"Current price: {current_price}")
        print(f"Old price: {old_price}")
        print(f"Discount: {discount}")
        print(f"Image: {image_url}")

        return product

    except Exception as e:
        print(f"Error: {e}")

        return {
            "url": url,
            "name": None,
            "current_price": None,
            "old_price": None,
            "discount": None,
            "image_url": None,
            "error": str(e),
        }


def main():
    print("Opening Trendyol flash sale page...")

    # Step 1: Scrape listing page
    result = StealthyFetcher.fetch(
        START_URL,
        headless=False,
        load_dom=True,
        network_idle=True,
        wait=1000,
        page_action=scroll_page,
    )

    print(f"Status: {result.status}")

    product_urls = sorted(all_product_urls)

    print(
        f"\nTotal products found: "
        f"{len(product_urls)}"
    )

    # Step 2: Save product URLs
    with open(
        "trendyol_products_urls.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            product_urls,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("Product URLs saved.")

    # Step 3: Scrape every product
    products = []
    total = len(product_urls)

    for number, url in enumerate(
        product_urls,
        start=1
    ):
        product = scrape_product(
            url,
            number,
            total,
        )

        products.append(product)

    # Step 4: Save product details
    with open(
        "trendyol_products.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            products,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(
        f"\nFinished scraping {len(products)} products."
    )

    print(
        "Product details saved to trendyol_products.json"
    )


if __name__ == "__main__":
    main()