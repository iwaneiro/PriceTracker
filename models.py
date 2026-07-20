from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
import uuid
from database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    url = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    product_id = Column(String, index=True, nullable=False)
    price_in_cents = Column(Integer, nullable=False)
    currency = Column(String, default="PLN")
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())