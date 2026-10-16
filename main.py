import os
import re
import hashlib
import json
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
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
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

def hash_password(password: str):

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
    password = data.password.strip()

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
            INSERT INTO users (username, password)
            VALUES (%s, %s)
            RETURNING id
            """,
            (username, password_hash)
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
    password = data.password.strip()

    password_hash = hash_password(password)

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT id, username
        FROM users
        WHERE username = %s
        AND password = %s
        """,
        (username, password_hash)
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
# AI PHÂN TÍCH GIAO DỊCH
# =========================================================

def parse_ai_transaction(text):

    prompt = f"""
Bạn là AI quản lý thu chi cá nhân.

Hãy phân tích câu sau:

"{text}"

Trả về DUY NHẤT JSON hợp lệ theo cấu trúc:

{{
    "transaction_type": "expense",
    "amount": 0,
    "description": "",
    "category": ""
}}

Quy tắc:

- transaction_type chỉ được là:
  "income" hoặc "expense"

- amount là số tiền Việt Nam.
- Nếu người dùng viết "40k" thì amount = 40000.
- "100k" = 100000.
- "1 triệu" = 1000000.
- "2tr" = 2000000.

Ví dụ:

"ăn cơm 40k"

=> 

{{
    "transaction_type": "expense",
    "amount": 40000,
    "description": "ăn cơm",
    "category": "Ăn uống"
}}

"lương tháng 15 triệu"

=>

{{
    "transaction_type": "income",
    "amount": 15000000,
    "description": "lương tháng",
    "category": "Lương"
}}

Chỉ trả về JSON.
Không giải thích.
"""

    try:

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        result = response.text.strip()

        # Loại bỏ markdown ```json nếu Gemini trả về
        result = re.sub(
            r"^```json\s*",
            "",
            result,
            flags=re.IGNORECASE
        )

        result = re.sub(
            r"\s*```$",
            "",
            result
        )

        data = json.loads(result)

        return data

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Lỗi Gemini: {str(e)}"
        )


# =========================================================
# ADD TRANSACTION AI
# =========================================================

@app.post("/add-transaction-ai")
def add_transaction_ai(data: AITransactionRequest):

    if not data.text.strip():

        raise HTTPException(
            status_code=400,
            detail="Vui lòng nhập nội dung giao dịch"
        )

    ai_data = parse_ai_transaction(data.text)

    transaction_type = ai_data.get(
        "transaction_type",
        "expense"
    )

    amount = float(
        ai_data.get("amount", 0)
    )

    description = ai_data.get(
        "description",
        data.text
    )

    category = ai_data.get(
        "category",
        "Khác"
    )

    if amount <= 0:

        raise HTTPException(
            status_code=400,
            detail="Không xác định được số tiền"
        )

    if transaction_type not in ["income", "expense"]:

        transaction_type = "expense"

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
            transaction_type,
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
        "message": "Đã thêm giao dịch",
        "transaction_id": transaction_id,
        "transaction_type": transaction_type,
        "amount": amount,
        "description": description,
        "category": category
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

    for row in rows:

        if isinstance(
            row.get("created_at"),
            datetime
        ):
            row["created_at"] = row[
                "created_at"
            ].strftime("%d/%m/%Y %H:%M")

        row["amount"] = float(
            row["amount"]
        )

    return rows


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
Bạn là AI đọc hóa đơn.

Hãy đọc hình ảnh hóa đơn này và trả về DUY NHẤT JSON:

{
    "transaction_type": "expense",
    "amount": 0,
    "description": "",
    "category": ""
}

Quy tắc:

- amount là tổng tiền phải trả.
- transaction_type mặc định là expense.
- description là nội dung mua hàng.
- category có thể là:
  Ăn uống
  Mua sắm
  Đi lại
  Hóa đơn
  Y tế
  Giải trí
  Khác

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

        result = response.text.strip()

        result = re.sub(
            r"^```json\s*",
            "",
            result,
            flags=re.IGNORECASE
        )

        result = re.sub(
            r"\s*```$",
            "",
            result
        )

        ai_data = json.loads(result)

        transaction_type = ai_data.get(
            "transaction_type",
            "expense"
        )

        amount = float(
            ai_data.get("amount", 0)
        )

        description = ai_data.get(
            "description",
            "Hóa đơn"
        )

        category = ai_data.get(
            "category",
            "Khác"
        )

        if amount <= 0:

            raise HTTPException(
                status_code=400,
                detail="Không đọc được tổng tiền trên hóa đơn"
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
                transaction_type,
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
            "transaction_type": transaction_type,
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
