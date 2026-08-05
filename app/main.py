from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from .scraper import get_notino_price
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from .database import SessionLocal, engine, get_db, Base
from .models import Product, PriceHistory, ErrorLog
from .schemas import ProductRequest
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os


def run_sync_job():
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        if not products:
            print("Auto-Sync: No products to sync yet.")
            return

        print(f"Auto-Sync: Starting mass sync for {len(products)} products...")
        success_count = 0
        error_count = 0

        for product in products:
            try:
                scraped_data = get_notino_price(product.url)

                if scraped_data.get("success"):
                    new_price = PriceHistory(
                        product_id=product.id,
                        price_in_cents=scraped_data["price_in_cents"],
                        currency=scraped_data["currency"]
                    )
                    db.add(new_price)
                    try:
                        db.commit()
                        success_count += 1
                        print(f"Auto-Sync: Successfully updated {product.url}")
                    except IntegrityError:
                        # Race condition: równoległy job lub request zdążył już zapisać ten rekord.
                        db.rollback()
                        success_count += 1
                        print(f"Auto-Sync: IntegrityError (race condition) for {product.url} - skipped duplicate.")
                else:
                    new_error = ErrorLog(
                        product_id=product.id,
                        url=product.url,
                        error_message=scraped_data.get("error_message", "Unknown error")
                    )
                    db.add(new_error)
                    try:
                        db.commit()
                    except SQLAlchemyError:
                        db.rollback()
                    error_count += 1
                    print(f"Auto-Sync: Failed to update {product.url} - Logged to DB")
            except Exception as e:
                # Izolacja błędów per-produkt: jeden nieudany scraping nie zatrzymuje całej pętli.
                db.rollback()
                error_count += 1
                print(f"Auto-Sync: Unexpected error for {product.url}: {e}")

        print(f"Auto-Sync: Completed! {success_count} success, {error_count} errors.")
    except Exception as e:
        print(f"Auto-Sync Critical Error: {e}")
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/scrape")
def scrape_product_price(request: ProductRequest, db: Session = Depends(get_db)):
    print(f"Received request to track URL: {request.url}")

    scraped_data = get_notino_price(request.url)

    product = db.query(Product).filter(Product.url == request.url).first()

    if not product:
        print("New product detected! Adding to database...")
        product = Product(url=request.url)
        db.add(product)
        try:
            db.commit()
            db.refresh(product)
        except IntegrityError:
            db.rollback()
            product = db.query(Product).filter(Product.url == request.url).first()
            print("Race condition resolved: Fetched existing product created by another request.")
    else:
        print("Product found in database. Adding new price record...")

    if not scraped_data.get("success"):
        print(f"Failed to scrape. Logging error for product: {product.url}")
        new_error = ErrorLog(
            product_id=product.id,
            url=product.url,
            error_message=scraped_data.get("error_message", "Unknown error")
        )
        db.add(new_error)
        db.commit()

        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch price: {scraped_data.get('error_message')}"
        )

    print("Product scraped successfully. Adding new price record...")
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
    subquery = (
        db.query(
            PriceHistory.product_id,
            func.max(PriceHistory.scraped_at).label("max_time"),
        )
        .group_by(PriceHistory.product_id)
        .subquery()
    )

    latest_prices = (
        db.query(Product, PriceHistory.price_in_cents)
        .outerjoin(subquery, Product.id == subquery.c.product_id)
        .outerjoin(
            PriceHistory,
            (PriceHistory.product_id == Product.id)
            & (PriceHistory.scraped_at == subquery.c.max_time),
        )
        .all()
    )

    result = [
        {
            "id": str(product.id),
            "url": product.url,
            "latest_price": price,
        }
        for product, price in latest_prices
    ]

    return {"status": "success", "data": result}

@app.post("/api/sync")
def trigger_manual_sync():
    run_sync_job()
    return {"status": "success", "message": "Manual sync completed."}


@app.get("/api/products/{product_id}/history")
def get_product_history(product_id: str, db: Session = Depends(get_db)):
    history_entries = db.query(PriceHistory).filter(PriceHistory.product_id == product_id).order_by(
        PriceHistory.scraped_at.asc()).all()

    if not history_entries:
        return {"status": "success", "data": []}

    data = [
        {
            "price_in_cents": entry.price_in_cents,
            "checked_at": entry.scraped_at.isoformat()
        }
        for entry in history_entries
    ]

    return {"status": "success", "data": data}


@app.delete("/api/products/{product_id}")
def delete_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    db.delete(product)
    db.commit()

    return {"status": "success", "message": "Product deleted."}


if os.path.isdir("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")