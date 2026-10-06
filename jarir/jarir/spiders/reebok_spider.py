from urllib.parse import urljoin

from scrapling.fetchers import StealthyFetcher


START_URL = "https://www.reebok.sa/en/collections/sale"
BASE_URL = "https://www.reebok.sa"

PRODUCT_XPATH = '//h3[@class="card__heading"]/a/@href'
LOAD_MORE_XPATH = "//span[contains(text(),'Load More')]"

NAME_XPATH = "//div[contains(@class,'product__title')]/h1/text()"

CURRENT_PRICE_XPATH = (
    "//div[starts-with(@id,'price-template')]"
    "//span[contains(@class,'price-item--sale')][1]/text()"
)

OLD_PRICE_XPATH = (
    "//div[starts-with(@id,'price-template')]"
    "[.//span[contains(@class,'product-discount-off')][not(contains(.,'0 %'))]]"
    "//s[contains(@class,'price-item--regular')]/text()"
)

DISCOUNT_XPATH = (
    "//div[starts-with(@id,'price-template')]"
    "//span[contains(@class,'product-discount-off')]/text()"
)

IMAGE_XPATH = (
    "//meta[@property='og:image:secure_url']/@content"
)

MAX_LOAD_MORE = 100


def load_more(page):
    """Click Load More until the button disappears."""

    for i in range(MAX_LOAD_MORE):

        button = page.locator(
            f"xpath={LOAD_MORE_XPATH}"
        )

        if button.count() == 0:
            print("Load More button not found.")
            break

        try:
            print(f"Clicking Load More {i + 1}...")

            button.first.scroll_into_view_if_needed()
            button.first.click()

            page.wait_for_timeout(3000)

        except Exception as e:
            print(f"Load More failed: {e}")
            break


def get_product_urls():
    """Scrape all product URLs from the sale page."""

    print("Opening Reebok sale page...")

    response = StealthyFetcher.fetch(
        START_URL,
        headless=False,
        load_dom=True,
        network_idle=True,
        page_action=load_more,
    )

    print(f"Status: {response.status}")

    products = set()

    links = response.xpath(PRODUCT_XPATH).getall()

    for link in links:
        products.add(urljoin(BASE_URL, link))

    print(f"\nTotal products found: {len(products)}")

    return list(products)


def scrape_product(url, index, total):
    """Scrape details from one product page."""

    print(f"\n========== PRODUCT {index}/{total} ==========")
    print(f"URL: {url}")

    try:
        page = StealthyFetcher.fetch(
            url,
            headless=False,
            load_dom=True,
            network_idle=True,
        )

        print(f"Status: {page.status}")

        name = page.xpath(NAME_XPATH).get()
        current_price = page.xpath(CURRENT_PRICE_XPATH).get()
        old_price = page.xpath(OLD_PRICE_XPATH).get()
        discount = page.xpath(DISCOUNT_XPATH).get()
        image = page.xpath(IMAGE_XPATH).get()

        print(f"Name: {name}")
        print(f"Current price: {current_price}")
        print(f"Old price: {old_price}")
        print(f"Discount: {discount}")
        print(f"Image: {image}")

        return {
            "url": url,
            "name": name,
            "current_price": current_price,
            "old_price": old_price,
            "discount": discount,
            "image": image,
        }

    except Exception as e:
        print(f"Error scraping product: {e}")

        return {
            "url": url,
            "name": None,
            "current_price": None,
            "old_price": None,
            "discount": None,
            "image": None,
        }


def scrape_products():
    """Scrape URLs first, then scrape every product."""

    product_urls = get_product_urls()

    total = len(product_urls)
    results = []

    print("\nStarting product detail scraping...")

    for index, url in enumerate(product_urls, start=1):
        product = scrape_product(
            url,
            index,
            total,
        )

        results.append(product)

    print("\n========================================")
    print(f"Finished scraping {len(results)} products")
    print("========================================")

    return results


if __name__ == "__main__":
    scrape_products()