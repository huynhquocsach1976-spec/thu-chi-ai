```python
import os
import re
import json
import hashlib

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


# =========================================================
# PASSWORD
# =========================================================

def hash_password(password: str) -> str:

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# =========================================================
# DATABASE TABLES
# =========================================================

def create_tables():

    conn = get_connection()
    cur = conn.cursor()

    try:

        # USERS
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

        cur.execute(
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
            """
        )

        # TRANSACTIONS
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

        print("DATABASE: OK")

    except Exception as e:

        conn.rollback()

        print(
            "DATABASE ERROR:",
            repr(e)
        )

        raise

    finally:

        cur.close()
        conn.close()


# =========================================================
# STARTUP
# =========================================================

@app.on_event("startup")
def startup():

    print("Starting Thu Chi AI Pro...")

    create_tables()

    print("Thu Chi AI Pro started.")


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

    if len(username) < 3:

        raise HTTPException(
            status_code=400,
            detail="Tên đăng nhập phải có ít nhất 3 ký tự"
        )

    if not password:

        raise HTTPException(
            status_code=400,
            detail="Mật khẩu không được để trống"
        )

    if len(password) < 4:

        raise HTTPException(
            status_code=400,
            detail="Mật khẩu phải có ít nhất 4 ký tự"
        )

    password_hash = hash_password(password)

    conn = get_connection()
    cur = conn.cursor(
        cursor_factory=RealDictCursor
    )

    try:

        # Kiểm tra username
        cur.execute(
            """
            SELECT id
            FROM users
            WHERE LOWER(username) = LOWER(%s)
            LIMIT 1
            """,
            (username,)
        )

        existing = cur.fetchone()

        if existing:

            raise HTTPException(
                status_code=400,
                detail="Tên đăng nhập đã tồn tại"
            )

        # Tạo tài khoản
        cur.execute(
            """
            INSERT INTO users
            (
                username,
                password_hash
            )
            VALUES
            (
                %s,
                %s
            )
            RETURNING id, username
            """,
            (
                username,
                password_hash
            )
        )

        user = cur.fetchone()

        conn.commit()

        return {
            "status": "success",
            "message": "Đăng ký thành công",
            "user_id": user["id"],
            "username": user["username"]
        }

    except HTTPException:

        conn.rollback()
        raise

    except Exception as e:

        conn.rollback()

        print(
            "REGISTER ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Lỗi đăng ký tài khoản: " + str(e)
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

    if not username or not password:

        raise HTTPException(
            status_code=400,
            detail="Vui lòng nhập tên đăng nhập và mật khẩu"
        )

    password_hash = hash_password(password)

    conn = get_connection()
    cur = conn.cursor(
        cursor_factory=RealDictCursor
    )

    try:

        cur.execute(
            """
            SELECT
                id,
                username,
                password_hash,
                password
            FROM users
            WHERE LOWER(TRIM(username)) = LOWER(TRIM(%s))
            LIMIT 1
            """,
            (username,)
        )

        user = cur.fetchone()

        if not user:

            raise HTTPException(
                status_code=401,
                detail="Sai tên đăng nhập hoặc mật khẩu"
            )

        stored_hash = user.get("password_hash")

        # Hỗ trợ tài khoản cũ
        if not stored_hash:

            old_password = user.get("password")

            if old_password:
                stored_hash = old_password

        if not stored_hash:

            raise HTTPException(
                status_code=401,
                detail="Tài khoản chưa có mật khẩu hợp lệ"
            )

        if stored_hash != password_hash:

            raise HTTPException(
                status_code=401,
                detail="Sai tên đăng nhập hoặc mật khẩu"
            )

        # Nếu tài khoản cũ chưa có password_hash
        # thì cập nhật sang password_hash
        if not user.get("password_hash"):

            cur.execute(
                """
                UPDATE users
                SET password_hash = %s
                WHERE id = %s
                """,
                (
                    password_hash,
                    user["id"]
                )
            )

            conn.commit()

        return {
            "status": "success",
            "message": "Đăng nhập thành công",
            "user_id": user["id"],
            "username": user["username"]
        }

    except HTTPException:

        conn.rollback()
        raise

    except Exception as e:

        conn.rollback()

        print(
            "LOGIN ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Lỗi đăng nhập: " + str(e)
        )

    finally:

        cur.close()
        conn.close()


# =========================================================
# CLEAN AI JSON
# =========================================================

def clean_json(text):

    if not text:

        raise ValueError(
            "AI không trả về dữ liệu"
        )

    text = text.strip()

    # Xóa ```json
    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    # Xóa ```
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

    # Lấy JSON object
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:

        raise ValueError(
            "AI không trả về JSON hợp lệ"
        )

    return text[start:end + 1].strip()


# =========================================================
# PARSE AI TRANSACTION
# =========================================================

def parse_ai_transaction(text):

    prompt = f"""
Bạn là AI quản lý thu chi.

Phân tích giao dịch:

{text}

Chỉ trả về JSON, không Markdown, không giải thích.

Định dạng:

{{
    "amount": 0,
    "transaction_type": "Chi",
    "category": "Khác",
    "description": ""
}}

QUY TẮC:

- 40k = 40000
- 50k = 50000
- 100k = 100000
- 1tr = 1000000
- 1 triệu = 1000000
- 2tr5 = 2500000

transaction_type chỉ được:
"Thu" hoặc "Chi"

Ví dụ:

ăn cơm 40k

Kết quả:

{{
    "amount": 40000,
    "transaction_type": "Chi",
    "category": "Ăn uống",
    "description": "ăn cơm"
}}

Ví dụ:

nhận lương 20 triệu

Kết quả:

{{
    "amount": 20000000,
    "transaction_type": "Thu",
    "category": "Lương",
    "description": "nhận lương"
}}

Hãy phân tích:
{text}
"""

    try:

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        ai_text = response.text

        json_text = clean_json(
            ai_text
        )

        data = json.loads(
            json_text
        )

        if not isinstance(data, dict):

            raise ValueError(
                "AI trả về dữ liệu không hợp lệ"
            )

        amount = data.get(
            "amount",
            0
        )

        if isinstance(amount, str):

            amount = (
                amount
                .replace(",", "")
                .replace("đ", "")
                .replace("₫", "")
                .strip()
            )

        amount = float(amount)

        if amount <= 0:

            raise ValueError(
                "AI không xác định được số tiền"
            )

        transaction_type = str(
            data.get(
                "transaction_type",
                "Chi"
            )
        ).strip()

        if transaction_type not in [
            "Thu",
            "Chi"
        ]:

            transaction_type = "Chi"

        category = str(
            data.get(
                "category",
                "Khác"
            )
        ).strip()

        if not category:

            category = "Khác"

        description = str(
            data.get(
                "description",
                text
            )
        ).strip()

        if not description:

            description = text

        return {
            "amount": amount,
            "transaction_type": transaction_type,
            "category": category,
            "description": description
        }

    except Exception as e:

        print(
            "AI PARSE ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=400,
            detail="Lỗi AI: " + str(e)
        )


# =========================================================
# ADD TRANSACTION AI
# =========================================================

@app.post("/add-transaction-ai")
def add_transaction_ai(
    data: AITransactionRequest
):

    text = data.text.strip()

    if not text:

        raise HTTPException(
            status_code=400,
            detail="Nội dung giao dịch không được để trống"
        )

    transaction = parse_ai_transaction(
        text
    )

    conn = get_connection()
    cur = conn.cursor(
        cursor_factory=RealDictCursor
    )

    try:

        # Kiểm tra user
        cur.execute(
            """
            SELECT id
            FROM users
            WHERE id = %s
            """,
            (data.user_id,)
        )

        user = cur.fetchone()

        if not user:

            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy người dùng"
            )

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
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING
                id,
                user_id,
                transaction_type,
                amount,
                description,
                category,
                created_at
            """,
            (
                data.user_id,
                transaction["transaction_type"],
                transaction["amount"],
                transaction["description"],
                transaction["category"]
            )
        )

        result = cur.fetchone()

        conn.commit()

        return {
            "status": "success",
            "message": "Đã thêm giao dịch thành công!",
            "amount": float(result["amount"]),
            "transaction_type": result["transaction_type"],
            "category": result["category"],
            "description": result["description"],
            "id": result["id"],
            "user_id": result["user_id"],
            "created_at": result["created_at"].isoformat()
        }

    except HTTPException:

        conn.rollback()
        raise

    except Exception as e:

        conn.rollback()

        print(
            "ADD TRANSACTION ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Không thể thêm giao dịch: " + str(e)
        )

    finally:

        cur.close()
        conn.close()


# =========================================================
# GET TRANSACTIONS
# =========================================================

@app.get("/transactions/{user_id}")
def get_transactions(user_id: int):

    conn = get_connection()
    cur = conn.cursor(
        cursor_factory=RealDictCursor
    )

    try:

        cur.execute(
            """
            SELECT
                id,
                user_id,
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

        result = []

        for row in rows:

            item = dict(row)

            item["amount"] = float(
                item["amount"]
            )

            if item.get("created_at"):

                item["created_at"] = (
                    item["created_at"]
                    .isoformat()
                )

            result.append(item)

        return result

    except Exception as e:

        print(
            "TRANSACTIONS ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Không thể lấy giao dịch: " + str(e)
        )

    finally:

        cur.close()
        conn.close()


# =========================================================
# SCAN BILL
# =========================================================

@app.post("/scan-bill")
async def scan_bill(
    user_id: int,
    file: UploadFile = File(...)
):

    file_bytes = await file.read()

    if not file_bytes:

        raise HTTPException(
            status_code=400,
            detail="File ảnh rỗng"
        )

    try:

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        user = cur.fetchone()

        cur.close()
        conn.close()

        if not user:

            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy người dùng"
            )

        mime_type = (
            file.content_type
            or "image/jpeg"
        )

        prompt = """
Đọc hóa đơn trong ảnh.

Chỉ trả về JSON:

{
    "amount": 0,
    "transaction_type": "Chi",
    "category": "Khác",
    "description": ""
}

amount = tổng tiền thanh toán.

Không Markdown.
Không giải thích.
"""

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                prompt,
                types.Part.from_bytes(
                    data=file_bytes,
                    mime_type=mime_type
                )
            ]
        )

        data = json.loads(
            clean_json(
                response.text
            )
        )

        amount = float(
            data.get(
                "amount",
                0
            )
        )

        if amount <= 0:

            raise ValueError(
                "Không đọc được số tiền"
            )

        transaction_type = data.get(
            "transaction_type",
            "Chi"
        )

        category = data.get(
            "category",
            "Khác"
        )

        description = data.get(
            "description",
            "Hóa đơn"
        )

        conn = get_connection()
        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

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
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING
                id,
                user_id,
                transaction_type,
                amount,
                description,
                category,
                created_at
            """,
            (
                user_id,
                transaction_type,
                amount,
                description,
                category
            )
        )

        result = cur.fetchone()

        conn.commit()

        cur.close()
        conn.close()

        return {
            "status": "success",
            "message": "Đã quét và lưu hóa đơn!",
            "amount": float(result["amount"]),
            "transaction_type": result["transaction_type"],
            "category": result["category"],
            "description": result["description"],
            "id": result["id"],
            "user_id": result["user_id"],
            "created_at": result["created_at"].isoformat()
        }

    except HTTPException:

        raise

    except Exception as e:

        print(
            "SCAN BILL ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=400,
            detail="Lỗi đọc hóa đơn: " + str(e)
        )


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    try:

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT 1")

        cur.fetchone()

        cur.close()
        conn.close()

        return {
            "status": "ok",
            "database": "connected"
        }

    except Exception as e:

        return {
            "status": "error",
            "database": "error",
            "message": str(e)
        }
```
