from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from scraper import get_notino_price
from sqlalchemy import desc
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from database import SessionLocal, engine, get_db, Base
from models import Product, PriceHistory
from schemas import ProductRequest


def run_sync_job():
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        if not products:
            print("Auto-Sync: No products to sync yet.")
            return

        print(f"Auto-Sync: Starting mass sync for {len(products)} products...")
        success_count = 0

        for product in products:
            scraped_data = get_notino_price(product.url)

            if scraped_data and scraped_data["price_in_cents"] is not None:
                new_price = PriceHistory(
                    product_id=product.id,
                    price_in_cents=scraped_data["price_in_cents"],
                    currency=scraped_data["currency"]
                )
                db.add(new_price)
                success_count += 1
                print(f"Auto-Sync: Successfully updated {product.url}")
            else:
                print(f"Auto-Sync: Failed to update {product.url}")

        db.commit()
        print(f"Auto-Sync: Completed! Updated {success_count}/{len(products)}")
    except Exception as e:
        print(f"Auto-Sync Error: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    scheduler = BackgroundScheduler()
    scheduler.add_job(run_sync_job, 'interval', hours=2)
    scheduler.start()

    yield

    scheduler.shutdown()

app = FastAPI(
    title="Smart Web Tracker API",
    description="API for tracking product prices in e-commerce stores",
    version="1.0.0",
    lifespan=lifespan
)

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

@app.get("/api/products")
def get_all_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    result = []
    for product in products:
        latest_price = db.query(PriceHistory).filter(PriceHistory.product_id == product.id).order_by(desc(PriceHistory.scraped_at)).first()
        result.append({
            "id": str(product.id),
            "url": product.url,
            "latest_price": latest_price.price_in_cents if latest_price else None,
        })
    return {"status": "success", "data": result}

@app.post("/api/sync")
def trigger_manual_sync():
    run_sync_job()
    return {"status": "success", "message": "Manual sync completed."}