import json
import re
from decimal import Decimal
from bs4 import BeautifulSoup
from curl_cffi import requests


def extract_price_from_text(text: str):
    if not text:
        return None
    match = re.search(r"(\d+[\s\d]*[,.]\d{2})", str(text))
    if match:
        clean_str = (
            match.group(1).replace(" ", "").replace("\xa0", "").replace(",", ".")
        )
        try:
            return int(Decimal(clean_str) * 100)
        except Exception:
            return None
    return None


def get_notino_price(url: str):
    try:
        # 1. Safari 17
        session = requests.Session(impersonate="safari17_0")
        response = session.get(
            url,
            timeout=20,
            headers={
                "Referer": "https://www.google.pl/",
            },
        )

        # 2. Chrome 120
        if response.status_code in [403, 429, 503]:
            print(f"Scraper: Kod {response.status_code}. Ponawiam próbę jako Chrome...")
            session = requests.Session(impersonate="chrome120")
            response = session.get(
                url,
                timeout=20,
                headers={
                    "Referer": "https://www.google.pl/",
                    "Upgrade-Insecure-Requests": "1",
                },
            )

        if response.status_code != 200:
            raise ValueError(
                f"Błąd HTTP {response.status_code} (Cloudflare odrzuciło zapytanie)."
            )

        soup = BeautifulSoup(response.text, "html.parser")
        price_in_cents = None

        # 1: Selektory HTML
        target_selectors = [
            'span[data-testid="pd-price"]:not([data-testid="currency-variant"])',
            '[data-testid="pd-price-wrapper"] span[content]:not([data-testid="currency-variant"])',
            '#pd-price span[content]:not([data-testid="currency-variant"])',
            'span[itemprop="price"]',
        ]

        for selector in target_selectors:
            elements = soup.select(selector)
            for el in elements:
                is_old_price = False
                for parent in el.find_parents():
                    test_id = str(parent.get("data-testid", ""))
                    cls_name = " ".join(parent.get("class", []))
                    if (
                        "originalPrice" in test_id
                        or "original-price" in test_id
                        or "line-through" in test_id.lower()
                    ):
                        is_old_price = True
                        break
                    if "originalprice" in cls_name.lower():
                        is_old_price = True
                        break

                if is_old_price:
                    continue

                val = el.get("content") or el.get_text()
                price_in_cents = extract_price_from_text(val)
                if price_in_cents:
                    print(
                        f"Scraper: Znaleziono cenę aktualną ({price_in_cents/100} zł) z selektora: {selector}"
                    )
                    break
            if price_in_cents:
                break

        # 2. Tagi <meta> w nagłówku strony (tylko jeśli HTML zawiódł)
        if not price_in_cents:
            for meta_sel in [
                'meta[property="product:price:amount"]',
                'meta[itemprop="price"]',
            ]:
                meta_tag = soup.select_one(meta_sel)
                if meta_tag and meta_tag.get("content"):
                    price_in_cents = extract_price_from_text(meta_tag["content"])
                    if price_in_cents:
                        print(
                            f"Scraper: Znaleziono cenę ({price_in_cents/100} zł) w tagu meta"
                        )
                        break

        # 3. Dane strukturalne SEO / Google (JSON-LD - fallback)
        if not price_in_cents:
            ld_scripts = soup.find_all("script", type="application/ld+json")
            for script in ld_scripts:
                try:
                    data = json.loads(script.string)
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        offers = item.get("offers", {})
                        if isinstance(offers, list):
                            for off in offers:
                                if "price" in off:
                                    price_in_cents = int(
                                        Decimal(str(off["price"])) * 100
                                    )
                                    print(
                                        f"Scraper: Znaleziono cenę w JSON-LD: {off['price']} zł"
                                    )
                                    break
                        elif isinstance(offers, dict) and "price" in offers:
                            price_in_cents = int(Decimal(str(offers["price"])) * 100)
                            print(
                                f"Scraper: Znaleziono cenę w JSON-LD: {offers['price']} zł"
                            )
                            break
                except Exception:
                    continue
                if price_in_cents:
                    break

        # 4. Szukanie w obiekcie stanu aplikacji React
        if not price_in_cents:
            match = re.search(r'"price"\s*:\s*(\d+[\d.]*)', response.text)
            if match:
                price_in_cents = int(Decimal(match.group(1)) * 100)
                print(
                    f"Scraper: Znaleziono cenę ({price_in_cents/100} zł) w kodzie JS strony"
                )

        if not price_in_cents:
            raise ValueError("Nie udało się wyciągnąć ceny z pobranego kodu strony.")

        return {
            "success": True,
            "price_in_cents": price_in_cents,
            "currency": "PLN",
        }

    except Exception as e:
        print(f"Scraper error for {url}: {e}")
        return {"success": False, "error_message": str(e)}