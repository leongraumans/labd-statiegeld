"""Open Food Facts API client — looks up product info by barcode."""

import httpx

from statiegeld.models import ProductType

API_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
FIELDS = "product_name,packaging_tags,packaging_text,quantity"

CAN_TAGS = {"en:can", "en:drink-can", "en:aluminum-can", "en:metal-can"}
BOTTLE_TAGS = {"en:bottle", "en:pet-bottle", "en:plastic-bottle", "en:glass-bottle", "en:bouteille"}

CAN_KEYWORDS = {"can", "blik", "canette", "dose", "tin"}
BOTTLE_KEYWORDS = {"bottle", "fles", "bouteille", "flasche", "pet"}


def _classify(packaging_tags: list[str], packaging_text: str, quantity: str) -> ProductType:
    tags = {t.lower() for t in packaging_tags}

    if tags & CAN_TAGS:
        return ProductType.CAN
    if tags & BOTTLE_TAGS:
        return ProductType.BOTTLE

    text = f"{packaging_text} {quantity}".lower()
    for kw in CAN_KEYWORDS:
        if kw in text:
            return ProductType.CAN
    for kw in BOTTLE_KEYWORDS:
        if kw in text:
            return ProductType.BOTTLE

    return ProductType.UNKNOWN


def lookup(barcode: str) -> dict | None:
    """Look up a barcode via Open Food Facts.
    Returns {"name": ..., "type": ProductType} or None if not found at all."""
    try:
        response = httpx.get(
            API_URL.format(barcode=barcode),
            params={"fields": FIELDS},
            timeout=5.0,
            headers={"User-Agent": "StatiegeldTracker/1.0"},
        )
        data = response.json()

        if data.get("status") != 1:
            return None

        product = data.get("product", {})
        name = product.get("product_name", "")
        if not name:
            return None

        packaging_tags = product.get("packaging_tags") or []
        packaging_text = product.get("packaging_text") or ""
        quantity = product.get("quantity") or ""

        product_type = _classify(packaging_tags, packaging_text, quantity)
        return {"name": name, "type": product_type}
    except (httpx.HTTPError, KeyError, ValueError):
        return None
