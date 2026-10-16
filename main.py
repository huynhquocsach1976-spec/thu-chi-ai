import os
import re
import json
import hmac
import hashlib
import secrets
from contextlib import asynccontextmanager, contextmanager

import psycopg2
from psycopg2 import errors as pg_errors
from psycopg2.extras import RealDictCursor

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from google import genai
from google.genai import types


# =========================================================
# CONFIG
# =========================================================

DATABASE_URL = os.getenv("DATABASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
DB_SSLMODE = os.getenv("DB_SSLMODE", "require")

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
PBKDF2_ITERATIONS = 200_000

if not DATABASE_URL:
    raise RuntimeError("Thiếu DATABASE_URL")

if not GEMINI_API_KEY:
    raise RuntimeError("Thiếu GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)


# =========================================================
# DATABASE
# =========================================================

def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode=DB_SSLMODE)


@contextmanager
def db_cursor():
    """Tự commit / rollback / đóng kết nối, không bao giờ rò rỉ connection."""
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    finally:
        conn.close()


def create_tables():
    with db_cursor() as cur:
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
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);"
        )
        # Hỗ trợ bảng users cũ có cột "password" (tránh lỗi khi đăng nhập / đăng ký)
        cur.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS password VARCHAR(255);"
        )
        cur.execute(
            "ALTER TABLE users ALTER COLUMN password DROP NOT NULL;"
        )

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
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_transactions_user
            ON transactions (user_id, created_at DESC);
            """
        )
    print("DATABASE: OK")


# =========================================================
# APP
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Thu Chi AI Pro...")
    create_tables()
    print("Thu Chi AI Pro started.")
    yield


app = FastAPI(title="Thu Chi AI Pro", version="1.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# PASSWORD (PBKDF2 có salt, vẫn đăng nhập được tài khoản cũ)
# =========================================================

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PBKDF2_ITERATIONS,
    ).hex()
    return f"pbkdf2${PBKDF2_ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored: str):
    """Trả về (đúng_mật_khẩu, cần_nâng_cấp_hash)."""
    if not stored:
        return False, False

    if stored.startswith("pbkdf2$"):
        try:
            _, iterations, salt, digest = stored.split("$")
            check = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                bytes.fromhex(salt),
                int(iterations),
            ).hex()
            return hmac.compare_digest(check, digest), False
        except Exception:
            return False, False

    # Tài khoản cũ: SHA256 thuần hoặc mật khẩu lưu thẳng
    legacy_sha = hashlib.sha256(password.encode("utf-8")).hexdigest()
    if hmac.compare_digest(legacy_sha, stored) or hmac.compare_digest(password, stored):
        return True, True

    return False, False


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
# ROOT / HEALTH
# =========================================================

@app.get("/")
def root():
    return {"status": "ok", "message": "Backend Thu Chi AI đang chạy bình thường"}


@app.get("/health")
def health():
    try:
        with db_cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": "error", "message": str(e)}


# =========================================================
# REGISTER
# =========================================================

@app.post("/register")
def register(data: RegisterRequest):
    username = data.username.strip()
    password = data.password.strip()

    if not username:
        raise HTTPException(400, "Tên đăng nhập không được để trống")
    if len(username) < 3:
        raise HTTPException(400, "Tên đăng nhập phải có ít nhất 3 ký tự")
    if not password:
        raise HTTPException(400, "Mật khẩu không được để trống")
    if len(password) < 4:
        raise HTTPException(400, "Mật khẩu phải có ít nhất 4 ký tự")

    try:
        with db_cursor() as cur:
            cur.execute(
                "SELECT id FROM users WHERE LOWER(username) = LOWER(%s) LIMIT 1",
                (username,),
            )
            if cur.fetchone():
                raise HTTPException(400, "Tên đăng nhập đã tồn tại")

            cur.execute(
                """
                INSERT INTO users (username, password_hash)
                VALUES (%s, %s)
                RETURNING id, username
                """,
                (username, hash_password(password)),
            )
            user = cur.fetchone()

        return {
            "status": "success",
            "message": "Đăng ký thành công",
            "user_id": user["id"],
            "username": user["username"],
        }

    except HTTPException:
        raise
    except pg_errors.UniqueViolation:
        raise HTTPException(400, "Tên đăng nhập đã tồn tại")
    except Exception as e:
        print("REGISTER ERROR:", repr(e))
        raise HTTPException(500, "Lỗi đăng ký tài khoản: " + str(e))


# =========================================================
# LOGIN
# =========================================================

@app.post("/login")
def login(data: LoginRequest):
    username = data.username.strip()
    password = data.password.strip()

    if not username or not password:
        raise HTTPException(400, "Vui lòng nhập tên đăng nhập và mật khẩu")

    try:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT id, username, password_hash, password
                FROM users
                WHERE LOWER(TRIM(username)) = LOWER(TRIM(%s))
                LIMIT 1
                """,
                (username,),
            )
            user = cur.fetchone()

            if not user:
                raise HTTPException(401, "Sai tên đăng nhập hoặc mật khẩu")

            stored = user.get("password_hash") or user.get("password")

            if not stored:
                raise HTTPException(401, "Tài khoản chưa có mật khẩu hợp lệ")

            ok, need_upgrade = verify_password(password, stored)

            if not ok:
                raise HTTPException(401, "Sai tên đăng nhập hoặc mật khẩu")

            if need_upgrade:
                cur.execute(
                    "UPDATE users SET password_hash = %s WHERE id = %s",
                    (hash_password(password), user["id"]),
                )

        return {
            "status": "success",
            "message": "Đăng nhập thành công",
            "user_id": user["id"],
            "username": user["username"],
        }

    except HTTPException:
        raise
    except Exception as e:
        print("LOGIN ERROR:", repr(e))
        raise HTTPException(500, "Lỗi đăng nhập: " + str(e))


# =========================================================
# AI HELPERS
# =========================================================

def clean_json(text):
    if not text:
        raise ValueError("AI không trả về dữ liệu")

    text = text.strip()
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("AI không trả về JSON hợp lệ")

    return text[start:end + 1].strip()


def parse_amount(value):
    if isinstance(value, (int, float)):
        return float(value)

    s = re.sub(r"[^\d.,]", "", str(value or ""))
    if not s:
        return 0.0

    # 1.000.000 hoặc 1,000,000 -> dấu phân cách hàng nghìn
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", s):
        s = s.replace(".", "").replace(",", "")
    else:
        s = s.replace(",", ".")

    try:
        return float(s)
    except ValueError:
        return 0.0


def normalize_transaction(data, fallback_description):
    if not isinstance(data, dict):
        raise ValueError("AI trả về dữ liệu không hợp lệ")

    amount = parse_amount(data.get("amount", 0))
    if amount <= 0:
        raise ValueError("AI không xác định được số tiền")
    if amount >= 10 ** 13:
        raise ValueError("Số tiền quá lớn")

    transaction_type = str(data.get("transaction_type", "Chi")).strip().capitalize()
    if transaction_type not in ("Thu", "Chi"):
        transaction_type = "Chi"

    category = str(data.get("category") or "").strip()[:100] or "Khác"
    description = str(data.get("description") or "").strip() or fallback_description

    return {
        "amount": amount,
        "transaction_type": transaction_type,
        "category": category,
        "description": description,
    }


def call_gemini_json(contents):
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0,
        ),
    )
    return json.loads(clean_json(response.text))


def insert_transaction(user_id, transaction):
    with db_cursor() as cur:
        cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cur.fetchone():
            raise HTTPException(404, "Không tìm thấy người dùng")

        cur.execute(
            """
            INSERT INTO transactions
                (user_id, transaction_type, amount, description, category)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, user_id, transaction_type, amount,
                      description, category, created_at
            """,
            (
                user_id,
                transaction["transaction_type"],
                transaction["amount"],
                transaction["description"],
                transaction["category"],
            ),
        )
        return cur.fetchone()


def transaction_response(row, message):
    return {
        "status": "success",
        "message": message,
        "id": row["id"],
        "user_id": row["user_id"],
        "amount": float(row["amount"]),
        "transaction_type": row["transaction_type"],
        "category": row["category"],
        "description": row["description"],
        "created_at": row["created_at"].isoformat(),
    }


# =========================================================
# ADD TRANSACTION AI
# =========================================================

TEXT_PROMPT = """
Bạn là AI quản lý thu chi.

Chỉ trả về JSON, không Markdown, không giải thích.

Định dạng:
{{
    "amount": 0,
    "transaction_type": "Chi",
    "category": "Khác",
    "description": ""
}}

QUY TẮC:
- 40k = 40000, 100k = 100000
- 1tr = 1000000, 1 triệu = 1000000, 2tr5 = 2500000
- transaction_type chỉ được là "Thu" hoặc "Chi"

Ví dụ: "ăn cơm 40k"
{{"amount": 40000, "transaction_type": "Chi", "category": "Ăn uống", "description": "ăn cơm"}}

Ví dụ: "nhận lương 20 triệu"
{{"amount": 20000000, "transaction_type": "Thu", "category": "Lương", "description": "nhận lương"}}

Hãy phân tích giao dịch sau:
{text}
"""


@app.post("/add-transaction-ai")
def add_transaction_ai(data: AITransactionRequest):
    text = data.text.strip()

    if not text:
        raise HTTPException(400, "Nội dung giao dịch không được để trống")

    try:
        raw = call_gemini_json(TEXT_PROMPT.format(text=text))
        transaction = normalize_transaction(raw, text)
    except Exception as e:
        print("AI PARSE ERROR:", repr(e))
        raise HTTPException(400, "Lỗi AI: " + str(e))

    try:
        row = insert_transaction(data.user_id, transaction)
        return transaction_response(row, "Đã thêm giao dịch thành công!")
    except HTTPException:
        raise
    except Exception as e:
        print("ADD TRANSACTION ERROR:", repr(e))
        raise HTTPException(500, "Không thể thêm giao dịch: " + str(e))


# =========================================================
# GET TRANSACTIONS
# =========================================================

@app.get("/transactions/{user_id}")
def get_transactions(user_id: int, limit: int = 500):
    limit = max(1, min(limit, 2000))

    try:
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, transaction_type, amount,
                       description, category, created_at
                FROM transactions
                WHERE user_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            rows = cur.fetchall()

        result = []
        for row in rows:
            item = dict(row)
            item["amount"] = float(item["amount"])
            if item.get("created_at"):
                item["created_at"] = item["created_at"].isoformat()
            result.append(item)

        return result

    except Exception as e:
        print("TRANSACTIONS ERROR:", repr(e))
        raise HTTPException(500, "Không thể lấy giao dịch: " + str(e))


# =========================================================
# SCAN BILL
# (dùng def thường để không chặn event loop khi gọi Gemini)
# =========================================================

BILL_PROMPT = """
Đọc hóa đơn trong ảnh.

Chỉ trả về JSON:
{
    "amount": 0,
    "transaction_type": "Chi",
    "category": "Khác",
    "description": ""
}

amount = tổng tiền thanh toán (số, đơn vị VND).
description = tên cửa hàng / nội dung chính của hóa đơn.
Không Markdown. Không giải thích.
"""


@app.post("/scan-bill")
def scan_bill(user_id: int, file: UploadFile = File(...)):
    file_bytes = file.file.read()

    if not file_bytes:
        raise HTTPException(400, "File ảnh rỗng")

    if len(file_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(400, "Ảnh quá lớn (tối đa 10MB)")

    mime_type = (file.content_type or "image/jpeg").lower()
    if mime_type not in ALLOWED_IMAGE_TYPES:
        mime_type = "image/jpeg"

    # Kiểm tra user trước khi tốn tiền gọi AI
    with db_cursor() as cur:
        cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cur.fetchone():
            raise HTTPException(404, "Không tìm thấy người dùng")

    try:
        raw = call_gemini_json(
            [
                BILL_PROMPT,
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
            ]
        )
        transaction = normalize_transaction(raw, "Hóa đơn")
    except Exception as e:
        print("SCAN BILL ERROR:", repr(e))
        raise HTTPException(400, "Lỗi đọc hóa đơn: " + str(e))

    try:
        row = insert_transaction(user_id, transaction)
        return transaction_response(row, "Đã quét và lưu hóa đơn!")
    except HTTPException:
        raise
    except Exception as e:
        print("SCAN BILL SAVE ERROR:", repr(e))
        raise HTTPException(500, "Không thể lưu hóa đơn: " + str(e))
