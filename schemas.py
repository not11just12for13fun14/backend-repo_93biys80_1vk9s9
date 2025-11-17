"""
Database Schemas for Laser Engraving Shop

Each Pydantic model represents a MongoDB collection.
Collection name is the lowercase of the class name.
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    avatar_url: Optional[str] = Field(None, description="Profile image URL")


class Category(BaseModel):
    name: str = Field(..., description="Category name")
    slug: str = Field(..., description="URL friendly slug")
    description: Optional[str] = Field(None, description="Short description")


class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Category slug")
    in_stock: bool = Field(True, description="Whether product is in stock")
    image_url: Optional[str] = Field(None, description="Image URL")


class Portfolio(BaseModel):
    title: str = Field(..., description="Project title")
    description: Optional[str] = Field(None, description="Project description")
    image_url: Optional[str] = Field(None, description="Showcase image URL")
    client_name: Optional[str] = Field(None, description="Client name")


class OrderItem(BaseModel):
    product_id: str = Field(..., description="Product ObjectId as string")
    qty: int = Field(1, ge=1, description="Quantity")


class Order(BaseModel):
    user_email: str = Field(..., description="Customer email")
    items: List[OrderItem] = Field(default_factory=list)
    status: str = Field("pending", description="Order status")
    notes: Optional[str] = Field(None, description="Customization notes")
    contact_phone: Optional[str] = Field(None, description="Phone number")
