import os
import re
import hashlib
import json
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="Thu Chi AI Backend Pro")

# 1. Lấy và chuẩn hóa DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_db_connection():
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="Chưa cấu hình DATABASE_URL trong Environment!")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Không thể kết nối Database Postgres: {str(e)}")

# 2. TỰ ĐỘNG TẠO BẢNG DATABASE KHI SERVER KHỞI CHẠY
@app.on_event("startup")
def startup_event():
    if not DATABASE_URL:
        print("⚠️ Bỏ qua khởi tạo DB do thiếu DATABASE_URL")
        return
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                type VARCHAR(50) NOT NULL,
                amount DOUBLE PRECISION NOT NULL,
                category VARCHAR(100),
                note TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Khởi tạo các bảng Database thành công!")
    except Exception as e:
        print(f"❌ Lỗi khởi tạo Database lúc Startup: {e}")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

class AuthRequest(BaseModel):
    username: str
    password: str

class ChatMessage(BaseModel):
    message: str
    user_id: int

class BudgetSettingRequest(BaseModel):
    user_id: int
    monthly_expense_limit: float
    monthly_income_target: float

@app.get("/")
def home():
    return {"status": "ok", "message": "Backend Thu Chi AI đang chạy bình thường"}

@app.post("/register")
def register(req: AuthRequest):
    conn = get_db_connection()
    cur = conn.cursor()
    pwd_hashed = hash_password(req.password)
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id;",
            (req.username.lower().strip(), pwd_hashed)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        return {"status": "success", "user_id": user_id, "username": req.username}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Tài khoản đã tồn tại hoặc lỗi DB: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.post("/login")
def login(req: AuthRequest):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        pwd_hashed = hash_password(req.password)
        cur.execute(
            "SELECT id, username FROM users WHERE username = %s AND password_hash = %s;",
            (req.username.lower().strip(), pwd_hashed)
        )
        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="Sai tên đăng nhập hoặc mật khẩu!")
        return {"status": "success", "user_id": user["id"], "username": user["username"]}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi Server xử lý Đăng nhập: {str(e)}")
    finally:
        cur.close()
        conn.close()
