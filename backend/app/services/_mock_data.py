"""Mock data for the sample e-commerce project used in MOCK_MODE."""


def get_mock_files() -> dict[str, str]:
    return {
        "app/main.py": _MAIN,
        "app/routers/auth.py": _AUTH,
        "app/routers/users.py": _USERS,
        "app/routers/products.py": _PRODUCTS,
        "app/routers/orders.py": _ORDERS,
        "app/models/user.py": _USER_MODEL,
        "app/models/product.py": _PRODUCT_MODEL,
        "app/services/auth_service.py": _AUTH_SERVICE,
        "src/App.tsx": _APP_TSX,
        "src/pages/ProductsPage.tsx": _PRODUCTS_PAGE,
    }


_MAIN = '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users, products, orders, auth

app = FastAPI(title="E-Commerce API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
'''

_AUTH = '''from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    if not request.password or len(request.password) < 8:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token="jwt-token")

@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    return TokenResponse(access_token="jwt-token")

@router.post("/logout")
async def logout():
    return {"message": "Logged out"}

@router.post("/refresh")
async def refresh_token():
    return TokenResponse(access_token="new-token")
'''

_USERS = '''from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class UserProfile(BaseModel):
    id: int
    email: str
    full_name: str
    role: str = "customer"
    is_active: bool = True

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None

@router.get("/me", response_model=UserProfile)
async def get_current_user():
    return UserProfile(id=1, email="user@example.com", full_name="John Doe")

@router.put("/me", response_model=UserProfile)
async def update_profile(request: UpdateProfileRequest):
    return UserProfile(id=1, email="user@example.com", full_name=request.full_name or "John Doe")

@router.get("/", response_model=list[UserProfile])
async def list_users(skip: int = Query(0, ge=0), limit: int = Query(20, le=100)):
    return []

@router.delete("/{user_id}")
async def delete_user(user_id: int):
    if user_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    return {"message": f"User {user_id} deleted"}
'''

_PRODUCTS = '''from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()

class Product(BaseModel):
    id: int
    name: str
    price: float = Field(gt=0)
    category: str
    stock: int = Field(ge=0)

class CreateProductRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(max_length=2000)
    price: float = Field(gt=0)
    category: str
    stock: int = Field(ge=0, default=0)

@router.get("/", response_model=list[Product])
async def list_products(
    category: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
):
    return []

@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: int):
    if product_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid product ID")
    return Product(id=product_id, name="Sample", price=29.99, category="Electronics", stock=10)

@router.post("/", response_model=Product)
async def create_product(request: CreateProductRequest):
    return Product(id=1, name=request.name, price=request.price, category=request.category, stock=request.stock)

@router.delete("/{product_id}")
async def delete_product(product_id: int):
    return {"message": f"Product {product_id} deleted"}
'''

_ORDERS = '''from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

router = APIRouter()

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderItem(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)

class CreateOrderRequest(BaseModel):
    items: list[OrderItem] = Field(min_length=1)
    shipping_address: str
    payment_method: str

class Order(BaseModel):
    id: int
    items: list[OrderItem]
    total_amount: float
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime

@router.post("/", response_model=Order)
async def create_order(request: CreateOrderRequest):
    total = sum(i.price * i.quantity for i in request.items)
    if total <= 0:
        raise HTTPException(status_code=400, detail="Order total must be positive")
    return Order(id=1, items=request.items, total_amount=total, created_at=datetime.utcnow())

@router.get("/{order_id}", response_model=Order)
async def get_order(order_id: int):
    return Order(id=order_id, items=[], total_amount=0, created_at=datetime.utcnow())

@router.put("/{order_id}/cancel")
async def cancel_order(order_id: int):
    return {"message": f"Order {order_id} cancelled"}
'''

_USER_MODEL = '''from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

class User:
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=False)
    role = Column(String(50), default="customer")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
'''

_PRODUCT_MODEL = '''from sqlalchemy import Column, Integer, String, Float, Boolean, Text

class Product:
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category = Column(String(100), index=True)
    stock = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
'''

_AUTH_SERVICE = '''import hashlib
from datetime import datetime, timedelta

class AuthService:
    SECRET_KEY = "your-secret-key"

    async def authenticate(self, email: str, password: str):
        if not email or not password or len(password) < 8:
            return None
        return f"jwt-token-for-{email}"

    async def user_exists(self, email: str) -> bool:
        return False

    async def register(self, email: str, password: str, full_name: str) -> str:
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        return f"jwt-token-for-{email}"
'''

_APP_TSX = '''import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import ProductsPage from "./pages/ProductsPage";
import OrdersPage from "./pages/OrdersPage";

function App() {
    const [isAuthenticated, setIsAuthenticated] = React.useState(false);
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/login" element={<LoginPage onLogin={() => setIsAuthenticated(true)} />} />
                <Route path="/" element={isAuthenticated ? <DashboardPage /> : <Navigate to="/login" />} />
                <Route path="/products" element={<ProductsPage />} />
                <Route path="/orders" element={<OrdersPage />} />
            </Routes>
        </BrowserRouter>
    );
}
export default App;
'''

_PRODUCTS_PAGE = '''import React, { useState, useEffect } from "react";
import axios from "axios";

interface Product { id: number; name: string; price: number; category: string; stock: number; }

const ProductsPage: React.FC = () => {
    const [products, setProducts] = useState<Product[]>([]);
    const [search, setSearch] = useState("");

    useEffect(() => {
        axios.get("/api/products", { params: { search } }).then(r => setProducts(r.data));
    }, [search]);

    return (
        <div>
            <h1>Products</h1>
            <input placeholder="Search..." value={search} onChange={e => setSearch(e.target.value)} />
            {products.map(p => <div key={p.id}><h3>{p.name}</h3><p>${p.price}</p></div>)}
        </div>
    );
};
export default ProductsPage;
'''
