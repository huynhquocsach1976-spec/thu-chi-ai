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

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="Thu Chi AI Pro",
    version="1.0"
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
    return psycopg2.connect(DATABASE_URL)


def create_tables():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS password VARCHAR(255);
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            transaction_type VARCHAR(20) NOT NULL,
            amount NUMERIC(15,2) NOT NULL,
            description TEXT,
            category VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()

    cur.close()
    conn.close()


@app.on_event("startup")
def startup_event():

    create_tables()


# =========================================================
# PASSWORD
# =========================================================

def hash_password(password):

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


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
# HOME
# =========================================================

@app.get("/")
def home():

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
    password = data.password

    if len(username) < 3:

        raise HTTPException(
            status_code=400,
            detail="Tên đăng nhập phải có ít nhất 3 ký tự"
        )

    if len(password) < 4:

        raise HTTPException(
            status_code=400,
            detail="Mật khẩu phải có ít nhất 4 ký tự"
        )

    conn = get_connection()
    cur = conn.cursor()

    try:

        password_hash = hash_password(password)

        cur.execute(
            """
            INSERT INTO users
            (username, password)
            VALUES (%s, %s)
            RETURNING id
            """,
            (
                username,
                password_hash
            )
        )

        user_id = cur.fetchone()[0]

        conn.commit()

        return {
            "status": "ok",
            "message": "Đăng ký thành công",
            "user_id": user_id
        }

    except psycopg2.errors.UniqueViolation:

        conn.rollback()

        raise HTTPException(
            status_code=400,
            detail="Tên đăng nhập đã tồn tại"
        )

    finally:

        cur.close()
        conn.close()


# =========================================================
# LOGIN
# =========================================================

@app.post("/login")
def login(data: LoginRequest):

    username = data.username.strip()
    password_hash = hash_password(
        data.password
    )

    conn = get_connection()

    cur = conn.cursor(
        cursor_factory=RealDictCursor
    )

    cur.execute(
        """
        SELECT id, username
        FROM users
        WHERE username = %s
        AND password = %s
        """,
        (
            username,
            password_hash
        )
    )

    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Sai tên đăng nhập hoặc mật khẩu"
        )

    return {
        "status": "ok",
        "message": "Đăng nhập thành công",
        "user_id": user["id"],
        "username": user["username"]
    }


# =========================================================
# CLEAN JSON GEMINI
# =========================================================

def clean_json(text):

    text = text.strip()

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^```\s*",
        "",
        text
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    start = text.find("{")
    end = text.rfind("}")

    if start >= 0 and end >= 0:

        text = text[start:end + 1]

    return text.strip()


# =========================================================
# AI PHÂN TÍCH
# =========================================================

def parse_ai_transaction(text):

    prompt = f"""
Bạn là AI quản lý thu chi cá nhân.

Phân tích câu:

{text}

BẮT BUỘC trả về JSON hợp lệ.

Cấu trúc:

{{
  "transaction_type": "expense",
  "amount": 40000,
  "description": "ăn cơm",
  "category": "Ăn uống"
}}

Quy tắc:

1. transaction_type chỉ được:
expense hoặc income

2. amount phải là số nguyên.

3. Quy đổi:
40k = 40000
50k = 50000
100k = 100000
1tr = 1000000
1 triệu = 1000000

4. Nếu là chi tiêu:
transaction_type = expense

5. Nếu là tiền nhận được:
transaction_type = income

6. category có thể:
Ăn uống
Mua sắm
Đi lại
Hóa đơn
Lương
Thưởng
Y tế
Giải trí
Khác

Ví dụ:

ăn cơm 40k

JSON:

{{
  "transaction_type": "expense",
  "amount": 40000,
  "description": "ăn cơm",
  "category": "Ăn uống"
}}

CHỈ TRẢ JSON.
KHÔNG GIẢI THÍCH.
"""

    try:

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        if not response.text:

            raise Exception(
                "Gemini không trả về dữ liệu"
            )

        result = clean_json(
            response.text
        )

        data = json.loads(result)

        if not isinstance(data, dict):

            raise Exception(
                "Gemini trả về dữ liệu không hợp lệ"
            )

        amount = data.get(
            "amount",
            0
        )

        try:

            amount = float(amount)

        except:

            amount = 0

        if amount <= 0:

            raise Exception(
                "AI không xác định được số tiền"
            )

        transaction_type = data.get(
            "transaction_type",
            "expense"
        )

        if transaction_type not in [
            "income",
            "expense"
        ]:

            transaction_type = "expense"

        description = str(
            data.get(
                "description",
                text
            )
        )

        category = str(
            data.get(
                "category",
                "Khác"
            )
        )

        return {
            "transaction_type": transaction_type,
            "amount": amount,
            "description": description,
            "category": category
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Lỗi AI: {str(e)}"
        )


# =========================================================
# ADD TRANSACTION
# =========================================================

@app.post("/add-transaction-ai")
def add_transaction_ai(
    data: AITransactionRequest
):

    text = data.text.strip()

    if not text:

        raise HTTPException(
            status_code=400,
            detail="Vui lòng nhập nội dung giao dịch"
        )

    ai_data = parse_ai_transaction(
        text
    )

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO transactions
        (
            user_id,
            transaction_type,
            amount,
            description,
            category
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            data.user_id,
            ai_data["transaction_type"],
            ai_data["amount"],
            ai_data["description"],
            ai_data["category"]
        )
    )

    transaction_id = cur.fetchone()[0]

    conn.commit()

    cur.close()
    conn.close()

    return {
        "status": "ok",
        "message": "Đã thêm giao dịch",
        "transaction_id": transaction_id,
        "transaction_type": ai_data["transaction_type"],
        "amount": ai_data["amount"],
        "description": ai_data["description"],
        "category": ai_data["category"]
    }


# =========================================================
# GET TRANSACTIONS
# =========================================================

@app.get("/transactions/{user_id}")
def get_transactions(user_id: int):

    conn = get_connection()

    cur = conn.cursor(
        cursor_factory=RealDictCursor
    )

    cur.execute(
        """
        SELECT
            id,
            transaction_type,
            amount,
            description,
            category,
            created_at
        FROM transactions
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (user_id,)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    result = []

    for row in rows:

        result.append({
            "id": row["id"],
            "transaction_type": row[
                "transaction_type"
            ],
            "amount": float(
                row["amount"]
            ),
            "description": row[
                "description"
            ],
            "category": row[
                "category"
            ],
            "created_at": (
                row["created_at"].strftime(
                    "%d/%m/%Y %H:%M"
                )
                if isinstance(
                    row["created_at"],
                    datetime
                )
                else str(
                    row["created_at"]
                )
            )
        })

    return result


# =========================================================
# SCAN BILL
# =========================================================

@app.post("/scan-bill")
async def scan_bill(
    user_id: int,
    file: UploadFile = File(...)
):

    try:

        image_bytes = await file.read()

        if not image_bytes:

            raise HTTPException(
                status_code=400,
                detail="File ảnh rỗng"
            )

        content_type = (
            file.content_type
            or "image/jpeg"
        )

        prompt = """
Đọc hóa đơn trong hình ảnh.

Trả về JSON:

{
  "transaction_type": "expense",
  "amount": 0,
  "description": "",
  "category": ""
}

amount là tổng tiền phải trả.

Chỉ trả JSON.
"""

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=content_type
                ),
                prompt
            ]
        )

        result = clean_json(
            response.text
        )

        ai_data = json.loads(result)

        amount = float(
            ai_data.get(
                "amount",
                0
            )
        )

        if amount <= 0:

            raise HTTPException(
                status_code=400,
                detail="Không đọc được số tiền"
            )

        description = str(
            ai_data.get(
                "description",
                "Hóa đơn"
            )
        )

        category = str(
            ai_data.get(
                "category",
                "Khác"
            )
        )

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO transactions
            (
                user_id,
                transaction_type,
                amount,
                description,
                category
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                user_id,
                "expense",
                amount,
                description,
                category
            )
        )

        transaction_id = cur.fetchone()[0]

        conn.commit()

        cur.close()
        conn.close()

        return {
            "status": "ok",
            "message": "Đã quét và lưu hóa đơn",
            "transaction_id": transaction_id,
            "transaction_type": "expense",
            "amount": amount,
            "description": description,
            "category": category
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Lỗi xử lý ảnh: {str(e)}"
        )
