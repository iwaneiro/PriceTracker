from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    url = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    prices = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    errors = relationship("ErrorLog", back_populates="product")

class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    product_id = Column(String, ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False)
    price_in_cents = Column(Integer, nullable=False)
    currency = Column(String, default="PLN")
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="prices")

class ErrorLog(Base):
    __tablename__ = "error_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    product_id = Column(String, ForeignKey("products.id", ondelete="SET NULL"), index=True, nullable=True)
    url = Column(String, nullable=False)
    error_message = Column(String, nullable=False)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="errors")