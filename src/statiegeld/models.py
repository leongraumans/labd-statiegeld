import enum
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, relationship


class ProductType(enum.Enum):
    CAN = "can"
    BOTTLE = "bottle"
    UNKNOWN = "unknown"

    @property
    def deposit(self) -> float:
        return {
            ProductType.CAN: 0.15,
            ProductType.BOTTLE: 0.25,
            ProductType.UNKNOWN: 0.00,
        }[self]


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    barcode = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    type = Column(Enum(ProductType), nullable=False)

    @property
    def deposit(self) -> float:
        return self.type.deposit


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, default=lambda: datetime.now(UTC))
    closed_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    scans = relationship("Scan", back_populates="session")


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    scanned_at = Column(DateTime, default=lambda: datetime.now(UTC))

    session = relationship("Session", back_populates="scans")
    product = relationship("Product")
