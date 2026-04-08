from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from statiegeld.database import SessionLocal, init_db
from statiegeld.models import Product, ProductType

KNOWN_PRODUCTS = [
    # Cans (€0.15)
    ("5449000000996", "Coca-Cola 33cl can", ProductType.CAN),
    ("5449000131805", "Coca-Cola Zero 33cl can", ProductType.CAN),
    ("5449000014535", "Fanta Orange 33cl can", ProductType.CAN),
    ("5449000009067", "Sprite 33cl can", ProductType.CAN),
    ("8714800011662", "Heineken 33cl can", ProductType.CAN),
    ("8712000032678", "Amstel 33cl can", ProductType.CAN),
    ("5060466515826", "Monster Energy 50cl can", ProductType.CAN),
    ("90162909", "Red Bull 25cl can", ProductType.CAN),
    ("8718452098057", "AH Pilsener 33cl can", ProductType.CAN),
    ("5449000054227", "Coca-Cola Cherry 33cl can", ProductType.CAN),
    ("8710398533647", "Grolsch Radler 33cl can", ProductType.CAN),
    ("5449000131300", "Fanta Zero 33cl can", ProductType.CAN),
    # Bottles (€0.25)
    ("5449000000439", "Coca-Cola 1L bottle", ProductType.BOTTLE),
    ("5449000000453", "Coca-Cola 1.5L bottle", ProductType.BOTTLE),
    ("5449000014559", "Fanta Orange 1.5L bottle", ProductType.BOTTLE),
    ("5449000009081", "Sprite 1.5L bottle", ProductType.BOTTLE),
    ("8715600221237", "Spa Rood 1L bottle", ProductType.BOTTLE),
    ("5000112659580", "Chaudfontaine 1L bottle", ProductType.BOTTLE),
    ("5449000131812", "Coca-Cola Zero 1.5L bottle", ProductType.BOTTLE),
    ("8710398170095", "Grolsch Premium Pilsner bottle", ProductType.BOTTLE),
]


def seed():
    init_db()
    db = SessionLocal()
    try:
        added = 0
        for barcode, name, product_type in KNOWN_PRODUCTS:
            exists = db.execute(
                select(Product).where(Product.barcode == barcode)
            ).scalar_one_or_none()
            if not exists:
                try:
                    db.add(Product(barcode=barcode, name=name, type=product_type))
                    db.flush()
                    added += 1
                except IntegrityError:
                    db.rollback()
        db.commit()
        print(f"{added} products added ({len(KNOWN_PRODUCTS) - added} already existed)")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
