import os
import re
import hashlib
import base64
import json

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import psycopg2
from psycopg2.extras import RealDictCursor

import google.generativeai as genai


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(title="Thu Chi AI Pro Backend")


# =========================================================
# ENVIRONMENT VARIABLES
# =========================================================

DATABASE_URL = os.getenv("DATABASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# Render/PostgreSQL đôi khi trả về postgres://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1
    )


# Cấu hình Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


# =========================================================
# DATABASE
# =========================================================

def get_db_connection():

    if not DATABASE_URL:
        raise HTTPException(
            status_code=500,
            detail="Chưa cấu hình DATABASE_URL trong Environment Variable!"
        )

    try:
        return psycopg2.connect(DATABASE_URL)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi kết nối PostgreSQL: {str(e)}"
        )


# =========================================================
# KHỞI TẠO DATABASE
# =========================================================

@app.on_event("startup")
def startup_event():

    if not DATABASE_URL:
        print("WARNING: Chưa có DATABASE_URL")
        return

    conn = None
    cur = None

    try:

        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # -------------------------
        # USERS
        # -------------------------

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # -------------------------
        # TRANSACTIONS
        # -------------------------

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

        print("Database initialization OK")

    except Exception as e:

        if conn:
            conn.rollback()

        print(f"Lỗi khởi tạo Database: {e}")

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# PASSWORD
# =========================================================

def hash_password(password: str) -> str:

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# =========================================================
# MODELS
# =========================================================

class AuthRequest(BaseModel):

    username: str
    password: str


class TransactionRequest(BaseModel):

    user_id: int
    text: str


class BillScanRequest(BaseModel):

    user_id: int
    image_base64: str


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "status": "ok",
        "message": "Backend Thu Chi AI Pro đang chạy bình thường"
    }


# =========================================================
# REGISTER
# =========================================================

@app.post("/register")
def register(req: AuthRequest):

    conn = get_db_connection()
    cur = conn.cursor()

    username = req.username.lower().strip()
    password_hash = hash_password(req.password)

    try:

        cur.execute(
            """
            INSERT INTO users
            (username, password_hash)
            VALUES (%s, %s)
            RETURNING id;
            """,
            (
                username,
                password_hash
            )
        )

        user_id = cur.fetchone()[0]

        conn.commit()

        return {
            "status": "success",
            "user_id": user_id,
            "username": username
        }

    except Exception as e:

        conn.rollback()

        raise HTTPException(
            status_code=400,
            detail=f"Tài khoản đã tồn tại hoặc có lỗi: {str(e)}"
        )

    finally:

        cur.close()
        conn.close()


# =========================================================
# LOGIN
# =========================================================

@app.post("/login")
def login(req: AuthRequest):

    conn = get_db_connection()

    cur = conn.cursor(
        cursor_factory=RealDictCursor
    )

    username = req.username.lower().strip()
    password_hash = hash_password(req.password)

    try:

        cur.execute(
            """
            SELECT id, username
            FROM users
            WHERE username = %s
            AND password_hash = %s;
            """,
            (
                username,
                password_hash
            )
        )

        user = cur.fetchone()

        if not user:

            raise HTTPException(
                status_code=401,
                detail="Sai thông tin đăng nhập!"
            )

        return {
            "status": "success",
            "user_id": user["id"],
            "username": user["username"]
        }

    finally:

        cur.close()
        conn.close()


# =========================================================
# THÊM GIAO DỊCH BẰNG AI / TEXT
# =========================================================

@app.post("/add-transaction-ai")
def add_transaction_ai(req: TransactionRequest):

    text = req.text.lower().strip()

    if not text:

        raise HTTPException(
            status_code=400,
            detail="Nội dung giao dịch không được để trống!"
        )

    # -----------------------------------------------------
    # TÌM SỐ TIỀN
    # -----------------------------------------------------

    amount = 0.0

    match = re.search(
        r'(\d+(?:[.,]\d+)?)\s*(k|m|tr|triệu|nghìn|ngan)?',
        text
    )

    if match:

        raw_num = float(
            match.group(1).replace(",", ".")
        )

        unit = match.group(2)

        if unit in ["k", "nghìn", "ngan"]:

            amount = raw_num * 1000

        elif unit in ["m", "tr", "triệu"]:

            amount = raw_num * 1000000

        else:

            if raw_num >= 1000:
                amount = raw_num
            else:
                amount = raw_num * 1000

    else:

        raise HTTPException(
            status_code=400,
            detail="Không tìm thấy số tiền hợp lệ trong câu nhập!"
        )

    # -----------------------------------------------------
    # PHÂN BIỆT THU / CHI
    # -----------------------------------------------------

    tx_type = "chi"

    income_keywords = [
        "lương",
        "luong",
        "thu",
        "được",
        "duoc",
        "cho",
        "thưởng",
        "thu nhập",
        "thu nhap",
        "nhận",
        "nhan"
    ]

    if any(keyword in text for keyword in income_keywords):

        tx_type = "thu"

    # -----------------------------------------------------
    # PHÂN LOẠI
    # -----------------------------------------------------

    category = "Khác"

    food_keywords = [
        "cơm",
        "com",
        "bún",
        "bun",
        "phở",
        "pho",
        "cà phê",
        "ca phe",
        "ăn",
        "an",
        "uống",
        "uong"
    ]

    transport_keywords = [
        "xăng",
        "xang",
        "xe",
        "grab",
        "taxi",
        "be",
        "di chuyển",
        "di chuyen"
    ]

    bill_keywords = [
        "tiền nhà",
        "tien nha",
        "điện",
        "dien",
        "nước",
        "nuoc",
        "mạng",
        "mang",
        "internet"
    ]

    shopping_keywords = [
        "mua",
        "quần áo",
        "quan ao",
        "giày",
        "giay",
        "điện thoại",
        "dien thoai"
    ]

    if any(keyword in text for keyword in food_keywords):

        category = "Ăn uống"

    elif any(keyword in text for keyword in transport_keywords):

        category = "Di chuyển"

    elif any(keyword in text for keyword in bill_keywords):

        category = "Hóa đơn"

    elif any(keyword in text for keyword in shopping_keywords):

        category = "Mua sắm"

    # -----------------------------------------------------
    # LƯU DATABASE
    # -----------------------------------------------------

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            INSERT INTO transactions
            (
                user_id,
                type,
                amount,
                category,
                note
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (
                req.user_id,
                tx_type,
                amount,
                category,
                req.text
            )
        )

        tx_id = cur.fetchone()[0]

        conn.commit()

        return {
            "status": "success",
            "message": f"Đã ghi nhận: {req.text}",
            "data": {
                "id": tx_id,
                "type": tx_type,
                "amount": amount,
                "category": category,
                "note": req.text
            }
        }

    except Exception as e:

        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Lỗi lưu Database: {str(e)}"
        )

    finally:

        cur.close()
        conn.close()


# =========================================================
# LẤY LỊCH SỬ GIAO DỊCH
# =========================================================
# ĐÂY LÀ ROUTE ĐANG BỊ THIẾU TRÊN RENDER
# =========================================================

@app.get("/transactions/{user_id}")
def get_transactions(user_id: int):

    conn = get_db_connection()

    cur = conn.cursor(
        cursor_factory=RealDictCursor
    )

    try:

        cur.execute(
            """
            SELECT
                id,
                type,
                amount,
                category,
                note,
                date
            FROM transactions
            WHERE user_id = %s
            ORDER BY date DESC;
            """,
            (user_id,)
        )

        records = cur.fetchall()

        # Chuyển datetime thành chuỗi JSON
        data = []

        for record in records:

            item = dict(record)

            if item.get("date"):

                item["date"] = item["date"].isoformat()

            data.append(item)

        return {
            "status": "success",
            "data": data
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Lỗi lấy lịch sử giao dịch: {str(e)}"
        )

    finally:

        cur.close()
        conn.close()


# =========================================================
# QUÉT HÓA ĐƠN BẰNG GEMINI AI
# =========================================================

@app.post("/scan-bill")
def scan_bill(req: BillScanRequest):

    if not GEMINI_API_KEY:

        raise HTTPException(
            status_code=500,
            detail="Chưa cấu hình GEMINI_API_KEY!"
        )

    try:

        # ---------------------------------------------
        # GIẢI MÃ BASE64
        # ---------------------------------------------

        image_bytes = base64.b64decode(
            req.image_base64
        )

        # ---------------------------------------------
        # GEMINI
        # ---------------------------------------------

        model = genai.GenerativeModel(
            "gemini-1.5-flash"
        )

        prompt = """
Phân tích hình ảnh hóa đơn/bill/mã QR này.

Hãy trả về JSON thuần túy theo cấu trúc:

{
    "amount": 0,
    "category": "Ăn uống",
    "note": "Tên cửa hàng hoặc nội dung thanh toán"
}

Quy tắc:

- amount là tổng tiền thanh toán kiểu số.
- category chỉ nên thuộc:
  "Ăn uống",
  "Mua sắm",
  "Di chuyển",
  "Hóa đơn",
  "Khác".
- note là tên cửa hàng hoặc nội dung thanh toán ngắn gọn.
- Chỉ trả về JSON.
- Không được trả về Markdown.
- Không được thêm ```json.
"""

        response = model.generate_content(
            [
                prompt,
                {
                    "mime_type": "image/jpeg",
                    "data": image_bytes
                }
            ]
        )

        clean_text = response.text.strip()

        clean_text = clean_text.replace(
            "```json",
            ""
        )

        clean_text = clean_text.replace(
            "```",
            ""
        )

        clean_text = clean_text.strip()

        data = json.loads(clean_text)

        amount = float(
            data.get("amount", 0)
        )

        category = data.get(
            "category",
            "Khác"
        )

        note = data.get(
            "note",
            "Quét hóa đơn"
        )

        # ---------------------------------------------
        # LƯU DATABASE
        # ---------------------------------------------

        conn = get_db_connection()
        cur = conn.cursor()

        try:

            cur.execute(
                """
                INSERT INTO transactions
                (
                    user_id,
                    type,
                    amount,
                    category,
                    note
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (
                    req.user_id,
                    "chi",
                    amount,
                    category,
                    note
                )
            )

            tx_id = cur.fetchone()[0]

            conn.commit()

            return {
                "status": "success",
                "data": {
                    "id": tx_id,
                    "amount": amount,
                    "category": category,
                    "note": note
                }
            }

        except Exception as e:

            conn.rollback()

            raise HTTPException(
                status_code=500,
                detail=f"Lỗi lưu Database: {str(e)}"
            )

        finally:

            cur.close()
            conn.close()

    except json.JSONDecodeError:

        raise HTTPException(
            status_code=500,
            detail="Gemini không trả về JSON hợp lệ!"
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Lỗi xử lý hóa đơn AI: {str(e)}"
        )
