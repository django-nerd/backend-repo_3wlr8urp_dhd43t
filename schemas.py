"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    image_url: Optional[str] = Field(None, description="Product image URL")
    in_stock: bool = Field(True, description="Whether product is in stock")

class Cart(BaseModel):
    """
    Shopping cart items
    Collection name: "cart"
    """
    user_id: str = Field(..., description="User or guest identifier")
    product_id: str = Field(..., description="Product ID")
    quantity: int = Field(1, ge=1, description="Quantity of the product")

class OrderItem(BaseModel):
    product_id: str
    title: str
    price: float
    quantity: int

class Order(BaseModel):
    """
    Orders collection schema
    Collection name: "order"
    """
    user_id: str
    items: List[OrderItem]
    total: float
    status: str = Field("placed", description="Order status")
