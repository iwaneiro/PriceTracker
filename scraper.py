from playwright.sync_api import sync_playwright
from decimal import Decimal
import re


def get_notino_price(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            print(f"Navigating to Notino: {url}")
            page.goto(url)

            price_selector = "span[content]"

            print("Loading prices...")
            page.wait_for_selector(price_selector, timeout=10000)

            raw_price = page.locator(price_selector).first.get_attribute("content")
            print(f"Raw text found: '{raw_price}'")

            # Converting prices
            clean_text = re.sub(r'[^\d,]', '', raw_price)
            clean_text = clean_text.replace(',', '.')

            if clean_text:
                decimal_price = Decimal(clean_text)
                final_price = int(decimal_price * 100)
            else:
                final_price = None

            result = {
                "url": url,
                "price_in_cents": final_price,
                "currency": "PLN"
            }

        except Exception as e:
            print(f"Failed to extract price. Check selector! Details: {e}")
            result = None

        finally:
            browser.close()

        return result


if __name__ == "__main__":
    test_url = "https://www.notino.pl/xerjoff/erba-pura-woda-perfumowana-unisex/p-16129562/"

    data = get_notino_price(test_url)

    if data:
        print("\nSuccess! Returned data:")
        print(data)