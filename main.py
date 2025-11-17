import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, Product, Category, Portfolio, Order, OrderItem

app = FastAPI(title="Laser Engraving Shop API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Laser Engraving Shop Backend"}


# Utility for ObjectId conversion
class Doc(BaseModel):
    id: str


def serialize(doc):
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    return doc


# Seed minimal categories/products/portfolio if collections are empty
@app.post("/seed")
def seed_data():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    created = {"categories": 0, "products": 0, "portfolio": 0}

    if db["category"].count_documents({}) == 0:
        for c in [
            {"name": "Phone Cases", "slug": "phone-cases", "description": "Precision-engraved cases"},
            {"name": "Wood Gifts", "slug": "wood-gifts", "description": "Maple, walnut, oak"},
            {"name": "Metal Cards", "slug": "metal-cards", "description": "Stainless, brass"},
        ]:
            create_document("category", c)
            created["categories"] += 1

    if db["product"].count_documents({}) == 0:
        for p in [
            {"title": "Walnut Coaster Set", "description": "Laser-engraved logo on walnut.", "price": 39.0, "category": "wood-gifts", "in_stock": True, "image_url": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800"},
            {"title": "Aluminum Business Card", "description": "Ultra-thin anodized metal.", "price": 2.5, "category": "metal-cards", "in_stock": True, "image_url": "https://images.unsplash.com/photo-1581291519195-ef11498d1cf5?w=800"},
            {"title": "Matte Black Phone Case", "description": "Custom pattern engraving.", "price": 29.0, "category": "phone-cases", "in_stock": True, "image_url": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800"},
        ]:
            create_document("product", p)
            created["products"] += 1

    if db["portfolio"].count_documents({}) == 0:
        for s in [
            {"title": "Startup Swag", "description": "Branded coasters for offsite.", "image_url": "https://images.unsplash.com/photo-1616628188502-521331aac402?w=1200", "client_name": "Veridian"},
            {"title": "Wedding Keepsake", "description": "Names and vows engraved on oak.", "image_url": "https://images.unsplash.com/photo-1523419409543-8c1a8ef328d2?w=1200", "client_name": "Eden & Kai"},
        ]:
            create_document("portfolio", s)
            created["portfolio"] += 1

    return {"status": "ok", "created": created}


# Public endpoints
@app.get("/categories")
def list_categories():
    cats = [serialize(c) for c in get_documents("category")]
    return cats


@app.get("/products")
def list_products(category: Optional[str] = None):
    filt = {"category": category} if category else {}
    prods = [serialize(p) for p in get_documents("product", filt)]
    return prods


@app.get("/portfolio")
def list_portfolio():
    items = [serialize(p) for p in get_documents("portfolio")]
    return items


class LoginRequest(BaseModel):
    email: str
    name: Optional[str] = None


@app.post("/login")
def login(payload: LoginRequest):
    # Simple email-based account creation/login
    existing = db["user"].find_one({"email": payload.email}) if db else None
    if existing:
        return serialize(existing)
    user = User(name=payload.name or payload.email.split("@")[0], email=payload.email)
    uid = create_document("user", user)
    created = db["user"].find_one({"_id": ObjectId(uid)})
    return serialize(created)


class CartItem(BaseModel):
    product_id: str
    qty: int = 1


class CreateOrderRequest(BaseModel):
    user_email: str
    items: List[CartItem]
    notes: Optional[str] = None
    contact_phone: Optional[str] = None


@app.post("/order")
def create_order(payload: CreateOrderRequest):
    # Validate products exist
    for it in payload.items:
        prod = db["product"].find_one({"_id": ObjectId(it.product_id)})
        if not prod:
            raise HTTPException(status_code=404, detail=f"Product not found: {it.product_id}")

    order = Order(
        user_email=payload.user_email,
        items=[OrderItem(product_id=i.product_id, qty=i.qty) for i in payload.items],
        notes=payload.notes,
        contact_phone=payload.contact_phone,
        status="pending",
    )
    oid = create_document("order", order)
    created = db["order"].find_one({"_id": ObjectId(oid)})
    return serialize(created)


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
