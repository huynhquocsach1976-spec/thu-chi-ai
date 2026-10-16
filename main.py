```python
import os
import re
import json
import hashlib
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import psycopg2
from psycopg2.extras import RealDictCursor

from google import genai
from google.genai import types


# =========================================================
# CONFIG
# =========================================================

DATABASE_URL = os.getenv("DATABASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL = "gemini-2.5-flash"


if not DATABASE_URL:
    raise RuntimeError("Thiếu DATABASE_URL")

if not GEMINI_API_KEY:
    raise RuntimeError("Thiếu GEMINI_API_KEY")


# =========================================================
# GEMINI
# =========================================================

client = genai.Client(api_key=GEMINI_API_KEY)


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="Thu Chi AI Pro",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# DATABASE
# =========================================================

def get_connection():
    return psycopg2.connect(
        DATABASE_URL,
        sslmode="require"
    )


def hash_password(password: str) -> str:
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# =========================================================
# CREATE TABLES
# =========================================================

def create_tables():

    conn = get_connection()
    cur = conn.cursor()

    try:

        # -------------------------------------------------
        # USERS
        # -------------------------------------------------

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # Nếu bảng users cũ đã tồn tại
        cur.execute(
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
            """
        )

        # -------------------------------------------------
        # TRANSACTIONS
        # -------------------------------------------------

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                transaction_type VARCHAR(20) NOT NULL,
                amount NUMERIC(15,2) NOT NULL,
                description TEXT,
                category VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        conn.commit()

        print("Database tables OK")

    except Exception as e:

        conn.rollback()

        print("Database initialization error:", e)

        raise

    finally:

        cur.close()
        conn.close()


# =========================================================
# STARTUP
# =========================================================

@app.on_event("startup")
def startup_event():

    print("Starting Thu Chi AI Pro...")

    create_tables()

    print("Thu Chi AI Pro started successfully")


# =========================================================
# MODELS
# =========================================================

class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AITransactionRequest(BaseModel):
    user_id: int
    text: str


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "status": "ok",
        "message": "Backend Thu Chi AI đang chạy bình thường"
    }


# =========================================================
# REGISTER
# =========================================================

@app.post("/register")
def register(data: RegisterRequest):

    username = data.username.strip()
    password = data.password.strip()

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Tên đăng nhập không được để trống"
        )

    if not password:
        raise HTTPException(
            status_code=400,
            detail="Mật khẩu
