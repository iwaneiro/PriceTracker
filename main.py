from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from scraper import get_notino_price
from database import SessionLocal, Product, PriceHistory, init_db

app = FastAPI(
    title="Smart Web Tracker API",
    description="API for tracking product prices in e-commerce stores",
    version="1.0.0"
)

init_db()


class ProductRequest(BaseModel):
    url: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/api/scrape")
def scrape_product_price(request: ProductRequest, db: Session = Depends(get_db)):
    print(f"Received request to track URL: {request.url}")

    scraped_data = get_notino_price(request.url)

    if not scraped_data or scraped_data["price_in_cents"] is None:
        raise HTTPException(
            status_code=400,
            detail="Failed to fetch price. Check the URL or scraper configuration."
        )

    product = db.query(Product).filter(Product.url == request.url).first()

    if not product:
        print("New product detected! Adding to database...")
        product = Product(url=request.url)
        db.add(product)
        db.commit()
        db.refresh(product)
    else:
        print("Product found in database. Adding new price record...")

    new_price_record = PriceHistory(
        product_id=product.id,
        price_in_cents=scraped_data["price_in_cents"],
        currency=scraped_data["currency"]
    )

    db.add(new_price_record)
    db.commit()

    return {
        "status": "success",
        "message": "Price successfully scraped and saved to database.",
        "data": scraped_data
    }