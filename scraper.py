from playwright.sync_api import sync_playwright
import re
from decimal import Decimal


def get_notino_price(url: str):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                page.goto(url, timeout=30000)

                price_element = page.wait_for_selector('span[data-testid="price-component"]', timeout=10000)

                if not price_element:
                    raise ValueError("Nie znaleziono elementu z ceną na stronie.")

                price_text = price_element.inner_text()

                clean_price = re.sub(r'[^\d,]', '', price_text).replace(',', '.')
                price_in_cents = int(Decimal(clean_price) * 100)

                return {"success": True, "price_in_cents": price_in_cents, "currency": "PLN"}

            finally:
                browser.close()

    except Exception as e:
        print(f"Scraper error for {url}: {e}")
        return {"success": False, "error_message": str(e)}