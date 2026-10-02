import json
from urllib.parse import urljoin
from scrapling.fetchers import StealthyFetcher


START_URL = (
    "https://stylishop.com/sa/en/list/women/"
    "context/up-to-80-percent-off-w"
)

BASE_URL = "https://stylishop.com"
# LISTING PAGE
PRODUCT_XPATH = "//a[contains(@href,'/sa/en/product-')]"
NEXT_BUTTON_XPATH = "//button[@aria-label='Next page']"
MAX_PAGES = 2

# PRODUCT DETAIL
# IMPORTANT:
# These are element XPaths.
# Do NOT use /text() or /@src with Playwright locator().
PRODUCT_NAME_XPATH = ("//div[contains(@class,'fs-16')]//h1")
CURRENT_PRICE_XPATH = ("(//div[contains(@class,'fw-6 c-dark-gray middle-xs')]""//div[@class='d-il-block'])[1]")
OLD_PRICE_XPATH = ("(//div[contains(@class,'fw-6 c-dark-gray middle-xs')]""//del)[1]")
DISCOUNT_XPATH = ("(//span[contains(@class,'c-red-1')])[1]")
IMAGE_XPATH = ("(//img[contains(@class,'pdp-image-aspect-ratio')])[1]")
# LISTING FUNCTIONS

def load_products(page):
    # Scroll to trigger lazy loading
    for i in range(5):

        page.evaluate(
            "window.scrollTo(0, document.body.scrollHeight)"
        )

        page.wait_for_timeout(3000)
    # Go back to top
    page.evaluate(
        "window.scrollTo(0, 0)"
    )

def get_product_urls(page):

    product_links = page.locator(f"xpath={PRODUCT_XPATH}").all()

    product_urls = []

    for link in product_links:

        href = link.get_attribute("href")

        if not href:
            continue

        url = urljoin(BASE_URL,href)

        if url not in product_urls:
            product_urls.append(url)

    return product_urls


def load_and_retry(page):

    print("Loading products...")

    load_products(page)

    product_urls = get_product_urls(page)

    print(
        "Products found:",
        len(product_urls)
    )
    # Reload if no products
    if not product_urls:

        print("No products found.")
        print("Reloading page...")
        page.reload(wait_until="domcontentloaded",timeout=120000,)

        load_products(page)

        product_urls = get_product_urls(page)
        print("Products found after reload:",len(product_urls))

    return product_urls


def scrape_all_pages(page):

    all_product_urls = []

    for page_number in range(1,MAX_PAGES + 1):

        print(f"\n========== PAGE {page_number} ==========")

        page_products = load_and_retry(page)

        # Stop if no products

        if not page_products:

            print("No products found on this page.")
            print("Stopping scraper.")
            break

        # Add products
        
        new_products = 0

        for url in page_products:

            if url not in all_product_urls:

                all_product_urls.append(url)

                new_products += 1

        print("New products:",new_products)
        print("Total products:",len(all_product_urls))
        
        # Find Next button

        next_button = page.locator(f"xpath={NEXT_BUTTON_XPATH}")

        if next_button.count() == 0:

            print("Next page button not found.")
            print("Pagination finished.")

            break

        # Check visibility

        if not next_button.first.is_visible():

            print("Next page button is not visible.")
            print("Pagination finished.")

            break

        # Check disabled

        if next_button.first.is_disabled():

            print("Next page button is disabled.")
            print("Pagination finished.")

            break

        # Click Next

        print("Clicking Next page...")

        next_button.first.click()

        print("Next page clicked.")

    return all_product_urls

# PRODUCT DETAIL FUNCTIONS

def get_text(page, xpath):

    element = page.locator(f"xpath={xpath}").first

    try:

        element.wait_for(
            state="visible",
            timeout=30000,
        )

        text = element.text_content()

        if text:

            return text.strip()

    except Exception as error:

        print(
            "Text extraction error:",
            error
        )

    return None


def get_attribute(page, xpath, attribute):

    element = page.locator(
        f"xpath={xpath}"
    ).first

    try:

        element.wait_for(state="attached",timeout=30000,)
        value = element.get_attribute(attribute)

        if value:

            return value.strip()

    except Exception as error:

        print("Attribute extraction error:",error)

    return None

def scrape_product(page, product_url):

    print("\nScraping product:")

    print(product_url)

    try:
        # Open product page

        page.goto(product_url,wait_until="load",timeout=120000,)

        print("Product page loaded.")
        product_name = get_text(page,PRODUCT_NAME_XPATH,)
        current_price = get_text(page,CURRENT_PRICE_XPATH,)
        old_price = get_text(page,OLD_PRICE_XPATH,)
        discount = get_text(page,DISCOUNT_XPATH,)
        image_url = get_attribute(page,IMAGE_XPATH,"src",)

        product = {
            "product_url": product_url,
            "product_name": product_name,
            "current_price": current_price,
            "old_price": old_price,
            "discount": discount,
            "image_url": image_url,
        }

        # Print result

        print("Name:",product_name)
        print("Current price:",current_price)
        print("Old price:",old_price)
        print("Discount:",discount)
        print("Image:",image_url)

        return product

    except Exception as error:

        print("Error scraping product:",error)

        return {
            "product_url": product_url,
            "product_name": None,
            "current_price": None,
            "old_price": None,
            "discount": None,
            "image_url": None,
        }

# MAIN

def main():

    collected_products = []

    product_details = []

    def page_action(page):

        nonlocal collected_products
        nonlocal product_details

        # ===================================
        # STEP 1
        # Collect all product URLs
        # ===================================

        collected_products = scrape_all_pages(
            page
        )

        print("\n================================")
        print("Finished collecting product URLs")
        print("Total URLs:",len(collected_products))
        print("================================")

        # ===================================
        # STEP 2
        # Scrape product details
        # ===================================

        for index, product_url in enumerate(
            collected_products,
            start=1,
        ):

            print(f"\n========== PRODUCT " f"{index}/{len(collected_products)} ==========")
            product = scrape_product(page,product_url,)
            product_details.append(product)

        return product_details

    # Start browser

    page = StealthyFetcher.fetch(
        START_URL,
        headless=False,
        load_dom=True,
        network_idle=True,
        solve_cloudflare=True,
        real_chrome=False,
        timeout=120000,
        page_action=page_action,
        wait=5000,
    )

    # Save JSON

    with open("styli_products.json","w",encoding="utf-8",) as file:

        json.dump(
            product_details,
            file,
            indent=4,
            ensure_ascii=False,
        )

    # Final output
    
    print("\n================================")
    print("Scraping finished")
    print("Total product URLs:",len(collected_products))
    print("Total product details:",len(product_details))
    print("Saved: styli_products.json")
    print("================================")


if __name__ == "__main__":
    main()