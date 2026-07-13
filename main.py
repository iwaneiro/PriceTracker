from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from scraper import get_notino_price

app = FastAPI(
    title="Smart Web Tracker API",
    description="API for tracking product prices in e-commerce stores",    version="1.0.0"
)

class ProductRequest(BaseModel):
    url: str

@app.post("/api/scrape")
def scrape_product_price(request: ProductRequest):
    print(f"Received request to track URL: {request.url}")

    scraped_data = get_notino_price(request.url)

    if not scraped_data:
        raise HTTPException(status_code=400, detail="Failed to fetch price. Check the URL or scraper configuration.")

    return {
        "status": "success",
        "data": scraped_data
    }