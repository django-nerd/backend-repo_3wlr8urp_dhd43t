import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product, Cart, Order, OrderItem

app = FastAPI(title="E-Commerce API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Utilities
class ObjectIdStr(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        try:
            return str(ObjectId(str(v)))
        except Exception:
            raise ValueError("Invalid ObjectId")


class ProductCreate(Product):
    pass

class ProductOut(Product):
    id: str

class CartItemOut(BaseModel):
    id: str
    user_id: str
    product_id: str
    quantity: int

class OrderCreate(BaseModel):
    user_id: str


# Routes
@app.get("/")
def root():
    return {"message": "E-Commerce Backend Running"}


# Products
@app.post("/products", response_model=dict)
def create_product(product: ProductCreate):
    inserted_id = create_document("product", product)
    return {"id": inserted_id}

@app.get("/products", response_model=List[ProductOut])
def list_products():
    docs = get_documents("product")
    out: List[ProductOut] = []
    for d in docs:
        d["id"] = str(d.get("_id"))
        d.pop("_id", None)
        out.append(ProductOut(**d))
    return out


# Cart
@app.post("/cart", response_model=dict)
def add_to_cart(item: Cart):
    # If the same product for same user exists, increment quantity
    existing = db["cart"].find_one({"user_id": item.user_id, "product_id": item.product_id})
    if existing:
        db["cart"].update_one({"_id": existing["_id"]}, {"$inc": {"quantity": item.quantity}, "$set": {"updated_at": existing.get("updated_at")}})
        return {"id": str(existing["_id"]) }
    inserted_id = create_document("cart", item)
    return {"id": inserted_id}

@app.get("/cart/{user_id}", response_model=List[CartItemOut])
def get_cart(user_id: str):
    docs = get_documents("cart", {"user_id": user_id})
    out: List[CartItemOut] = []
    for d in docs:
        out.append(CartItemOut(id=str(d.get("_id")), user_id=d["user_id"], product_id=d["product_id"], quantity=d["quantity"]))
    return out

@app.delete("/cart/{item_id}")
def remove_cart_item(item_id: str):
    try:
        oid = ObjectId(item_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid item id")
    res = db["cart"].delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"status": "deleted"}


# Orders
@app.post("/orders", response_model=dict)
def place_order(payload: OrderCreate):
    # Get cart items
    cart_items = list(db["cart"].find({"user_id": payload.user_id}))
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Fetch product details
    items: List[OrderItem] = []
    total = 0.0
    for ci in cart_items:
        prod = db["product"].find_one({"_id": ci["product_id"]})
        # if stored product_id is as string ObjectId, ensure matching
        prod = db["product"].find_one({"_id": ObjectId(ci["product_id"])}) if not prod else prod
        if not prod:
            continue
        price = float(prod.get("price", 0))
        qty = int(ci.get("quantity", 1))
        total += price * qty
        items.append(OrderItem(product_id=str(prod["_id"]), title=prod.get("title", ""), price=price, quantity=qty))

    order_doc = Order(user_id=payload.user_id, items=items, total=round(total, 2))
    inserted_id = create_document("order", order_doc)

    # Clear cart
    db["cart"].delete_many({"user_id": payload.user_id})

    return {"id": inserted_id, "total": order_doc.total}


@app.get("/orders/{user_id}")
def list_orders(user_id: str):
    orders = get_documents("order", {"user_id": user_id})
    for o in orders:
        o["id"] = str(o.pop("_id"))
    return orders


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
