from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqladmin import Admin, BaseView, ModelView, expose
from sqlalchemy import select
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from statiegeld.auth import AdminAuth
from statiegeld.config import API_KEY, SECRET_KEY
from statiegeld.database import engine, get_db, init_db
from statiegeld.models import Product, ProductType, Scan
from statiegeld.models import Session as ScanSession
from statiegeld.openfoodfacts import lookup as off_lookup
from statiegeld.seed import seed

BASE_DIR = Path(__file__).parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed()
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

TZ = ZoneInfo("Europe/Amsterdam")


def to_local(dt: datetime) -> datetime:
    """Convert a UTC datetime to Amsterdam local time."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(TZ)


def nl_datetime(dt: datetime) -> str:
    """Format a datetime in Dutch format: 02 april 2026, 14:35."""
    months = [
        "",
        "januari",
        "februari",
        "maart",
        "april",
        "mei",
        "juni",
        "juli",
        "augustus",
        "september",
        "oktober",
        "november",
        "december",
    ]
    local = to_local(dt)
    return f"{local.day} {months[local.month]} {local.year}, {local.strftime('%H:%M')}"


templates.env.filters["nl_datetime"] = nl_datetime


def get_unknown_products(db: Session) -> list[Product]:
    return (
        db.execute(select(Product).where(Product.type == ProductType.UNKNOWN))
        .scalars()
        .all()
    )


def render(request: Request, template: str, db: Session, context: dict = {}):
    unknown_products = get_unknown_products(db)
    return templates.TemplateResponse(
        request,
        template,
        {
            **context,
            "unknown_count": len(unknown_products),
            "unknown_products": unknown_products,
        },
    )


# --- Admin panel at /admin ---


class ProductAdmin(ModelView, model=Product):
    column_list = [Product.id, Product.barcode, Product.name, Product.type]
    column_searchable_list = [Product.barcode, Product.name]
    column_default_sort = ("id", True)
    page_size = 50
    icon = "fa-solid fa-wine-bottle"


class SessionAdmin(ModelView, model=ScanSession):
    column_list = [
        ScanSession.id,
        ScanSession.started_at,
        ScanSession.closed_at,
        ScanSession.is_active,
    ]
    column_default_sort = ("id", True)
    page_size = 50
    icon = "fa-solid fa-database"


class ScanAdmin(ModelView, model=Scan):
    column_list = [Scan.id, Scan.session_id, Scan.product_id, Scan.scanned_at]
    column_default_sort = ("id", True)
    page_size = 50
    icon = "fa-solid fa-barcode"


class HomeLink(BaseView):
    name = "Home"
    icon = "fa-solid fa-arrow-left"

    @expose("/home", methods=["GET"])
    async def home(self, request: Request):
        return RedirectResponse(url="/")


admin = Admin(
    app,
    engine,
    authentication_backend=AdminAuth(SECRET_KEY),
    templates_dir=str(BASE_DIR / "templates"),
)
admin.add_view(ProductAdmin)
admin.add_view(SessionAdmin)
admin.add_view(ScanAdmin)
admin.add_base_view(HomeLink)


def find_or_lookup_product(barcode: str, db: Session) -> Product:
    """Find a product in the DB, or look it up via Open Food Facts, or create as UNKNOWN."""
    product = db.execute(
        select(Product).where(Product.barcode == barcode)
    ).scalar_one_or_none()
    if product:
        return product

    result = off_lookup(barcode)
    if result:
        product = Product(barcode=barcode, name=result["name"], type=result["type"])
    else:
        product = Product(
            barcode=barcode, name=f"Unknown ({barcode})", type=ProductType.UNKNOWN
        )

    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def get_or_create_active_session(db: Session) -> ScanSession:
    session = db.execute(
        select(ScanSession).where(ScanSession.is_active == True)
    ).scalar_one_or_none()
    if not session:
        session = ScanSession()
        db.add(session)
        db.commit()
        db.refresh(session)
    return session


# --- HTML routes ---


@app.get("/", response_class=HTMLResponse)
async def index():
    return RedirectResponse(url="/session", status_code=302)


@app.get("/session", response_class=HTMLResponse)
async def session_page(request: Request, db: Session = Depends(get_db)):
    active_session = get_or_create_active_session(db)
    scans = (
        db.execute(select(Scan).where(Scan.session_id == active_session.id))
        .scalars()
        .all()
    )

    cans = [s for s in scans if s.product.type == ProductType.CAN]
    bottles = [s for s in scans if s.product.type == ProductType.BOTTLE]
    unknown = [s for s in scans if s.product.type == ProductType.UNKNOWN]
    total_cans = len(cans) * ProductType.CAN.deposit
    total_bottles = len(bottles) * ProductType.BOTTLE.deposit
    total = total_cans + total_bottles

    now = to_local(datetime.now(UTC))

    return render(
        request,
        "session.html",
        db,
        {
            "session": active_session,
            "cans": len(cans),
            "bottles": len(bottles),
            "unknown": len(unknown),
            "total_cans": total_cans,
            "total_bottles": total_bottles,
            "total": total,
            "now": now,
        },
    )


@app.post("/session/close")
async def close_session(db: Session = Depends(get_db)):
    active_session = get_or_create_active_session(db)
    active_session.is_active = False
    active_session.closed_at = datetime.now(UTC)
    db.commit()
    return RedirectResponse(url="/session", status_code=303)


@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request, db: Session = Depends(get_db)):
    sessions = (
        db.execute(
            select(ScanSession)
            .where(ScanSession.is_active == False)
            .order_by(ScanSession.closed_at.desc())
        )
        .scalars()
        .all()
    )

    session_data = []
    for s in sessions:
        cans = len([scan for scan in s.scans if scan.product.type == ProductType.CAN])
        bottles = len(
            [scan for scan in s.scans if scan.product.type == ProductType.BOTTLE]
        )
        total = cans * ProductType.CAN.deposit + bottles * ProductType.BOTTLE.deposit
        session_data.append(
            {"session": s, "cans": cans, "bottles": bottles, "total": total}
        )

    return render(request, "history.html", db, {"sessions": session_data})


@app.get("/products", response_class=HTMLResponse)
async def products_page(request: Request, db: Session = Depends(get_db)):
    products = db.execute(select(Product).order_by(Product.name)).scalars().all()
    return render(request, "products.html", db, {"products": products})


@app.post("/products")
async def add_product(
    barcode: str = Form(...),
    name: str = Form(...),
    type: str = Form(...),
    db: Session = Depends(get_db),
):
    exists = db.execute(
        select(Product).where(Product.barcode == barcode)
    ).scalar_one_or_none()
    if not exists:
        db.add(Product(barcode=barcode, name=name, type=ProductType(type)))
        db.commit()
    return RedirectResponse(url="/products", status_code=303)


# --- JSON API for scanner ---


class ScanRequest(BaseModel):
    barcode: str


def verify_api_key(x_api_key: str = Header()):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.post("/api/scan", dependencies=[Depends(verify_api_key)])
async def api_scan(scan_req: ScanRequest, db: Session = Depends(get_db)):
    active_session = get_or_create_active_session(db)
    product = find_or_lookup_product(scan_req.barcode, db)

    scan = Scan(session_id=active_session.id, product_id=product.id)
    db.add(scan)
    db.commit()
    return {
        "status": "ok",
        "product": product.name,
        "type": product.type.value,
        "deposit": product.deposit,
    }
