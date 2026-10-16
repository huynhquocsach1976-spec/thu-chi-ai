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
# CẤU HÌNH
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


DATABASE_URL = os.getenv("DATABASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not DATABASE_URL:
    raise RuntimeError("Thiếu biến môi trường DATABASE_URL")

if not GEMINI_API_KEY:
    raise RuntimeError("Thiếu biến môi trường GEMINI_API_KEY")


# =========================================================
# GEMINI - SDK MỚI
# =========================================================

client = genai.Client(api_key=GEMINI_API_KEY)

GEMINI_MODEL = "gemini-2.5-flash"


# =========================================================
# DATABASE
# =========================================================

def get_db_connection():
    database_url = DATABASE_URL

    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1
        )

    return psycopg2.connect(database_url)


@app.on_event("startup")
def startup():

    conn = get_db_connection()
    cur = conn.cursor()

    # Bảng users
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Bảng transactions
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            transaction_type VARCHAR(20) NOT NULL,
            amount NUMERIC(15,2) NOT NULL,
            description TEXT,
            category VARCHAR(100),
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


# =========================================================
# HỖ TRỢ
# =========================================================

def hash_password(password: str) -> str:
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def clean_json_text(text: str) -> str:

    text = text.strip()

    # Loại bỏ markdown ```json ... ```
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

    return text.strip()


def parse_money(value):

    if value is None:
        return 0

    if isinstance(value, (int, float)):
        return float(value)

    value = str(value)

    value = value.replace("₫", "")
    value = value.replace("đ", "")
    value = value.replace("Đ", "")
    value = value.replace("VND", "")
    value = value.replace("vnd", "")
    value = value.replace(" ", "")
    value = value.replace(",", "")

    try:
        return float(value)
    except Exception:
        return 0


def normalize_transaction_type(value):

    if not value:
        return "chi"

    value = str(value).lower().strip()

    if value in [
        "thu",
        "income",
        "revenue",
        "receive",
        "nhan"
    ]:
        return "thu"

    return "chi"


# =========================================================
# MODELS
# =========================================================

class AuthRequest(BaseModel):
    username: str
    password: str


class TransactionRequest(BaseModel):
    user_id: int
    text: str = ""


class BillScanRequest(BaseModel):
    user_id: int


# =========================================================
# TEST API
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
def register(data: AuthRequest):

    username = data.username.strip()
    password = data.password

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Username không được để trống"
        )

    if not password:
        raise HTTPException(
            status_code=400,
            detail="Password không được để trống"
        )

    password_hash = hash_password(password)

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            SELECT id
            FROM users
            WHERE username = %s
            """,
            (username,)
        )

        if cur.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Tên đăng nhập đã tồn tại"
            )

        cur.execute(
            """
            INSERT INTO users
                (username, password_hash)
            VALUES
                (%s, %s)
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
            "status": "success",
            "message": "Đăng ký thành công",
            "user_id": user_id,
            "username": username
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Lỗi đăng ký: {str(e)}"
        )

    finally:
        cur.close()
        conn.close()


# =========================================================
# LOGIN
# =========================================================

@app.post("/login")
def login(data: AuthRequest):

    username = data.username.strip()
    password_hash = hash_password(data.password)

    conn = get_db_connection()
    cur = conn.cursor(
        cursor_factory=RealDictCursor
    )

    try:

        cur.execute(
            """
            SELECT id, username
            FROM users
            WHERE username = %s
            AND password_hash = %s
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
                detail="Sai tên đăng nhập hoặc mật khẩu"
            )

        return {
            "status": "success",
            "message": "Đăng nhập thành công",
            "user_id": user["id"],
            "username": user["username"]
        }

    finally:
        cur.close()
        conn.close()


# =========================================================
# THÊM GIAO DỊCH BẰNG AI
# =========================================================

@app.post("/add-transaction-ai")
def add_transaction_ai(data: TransactionRequest):

    if not data.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Nội dung giao dịch không được để trống"
        )

    prompt = f"""
Bạn là AI chuyên phân tích giao dịch thu chi cá nhân.

Hãy phân tích câu sau:

"{data.text}"

Trả về DUY NHẤT JSON hợp lệ, không markdown:

{{
    "transaction_type": "thu hoặc chi",
    "amount": 0,
    "description": "",
    "category": ""
}}

Quy tắc:

- transaction_type chỉ được là "thu" hoặc "chi".
- amount là số tiền thực tế.
- "50 nghìn" = 50000.
- "100k" = 100000.
- "1 triệu" = 1000000.
- "15 triệu" = 15000000.
- description là nội dung giao dịch.
- category là nhóm chi tiêu phù hợp.
"""

    try:

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        result_text = clean_json_text(
            response.text or ""
        )

        result = json.loads(result_text)

        transaction_type = normalize_transaction_type(
            result.get("transaction_type")
        )

        amount = parse_money(
            result.get("amount")
        )

        description = str(
            result.get("description")
            or data.text
        ).strip()

        category = str(
            result.get("category")
            or "Khác"
        ).strip()

        if amount <= 0:
            raise ValueError(
                "AI không xác định được số tiền"
            )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Lỗi xử lý giao dịch AI: {str(e)}"
        )

    conn = get_db_connection()
    cur = conn.cursor()

    try:

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
            (%s, %s, %s, %s, %s)
            RETURNING id, transaction_date
            """,
            (
                data.user_id,
                transaction_type,
                amount,
                description,
                category
            )
        )

        row = cur.fetchone()

        conn.commit()

        return {
            "status": "success",
            "message": "Đã thêm giao dịch",
            "data": {
                "id": row[0],
                "user_id": data.user_id,
                "transaction_type": transaction_type,
                "amount": amount,
                "description": description,
                "category": category,
                "transaction_date": (
                    row[1].isoformat()
                    if row[1]
                    else None
                )
            }
        }

    except Exception as e:

        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Lỗi lưu giao dịch: {str(e)}"
        )

    finally:

        cur.close()
        conn.close()


# =========================================================
# LẤY DANH SÁCH GIAO DỊCH
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
                user_id,
                transaction_type,
                amount,
                description,
                category,
                transaction_date
            FROM transactions
            WHERE user_id = %s
            ORDER BY transaction_date DESC, id DESC
            """,
            (user_id,)
        )

        rows = cur.fetchall()

        result = []

        for row in rows:

            item = dict(row)

            if item.get("transaction_date"):
                item["transaction_date"] = (
                    item["transaction_date"].isoformat()
                )

            if item.get("amount") is not None:
                item["amount"] = float(
                    item["amount"]
                )

            result.append(item)

        return {
            "status": "success",
            "data": result
        }

    finally:

        cur.close()
        conn.close()


# =========================================================
# QUÉT HÓA ĐƠN BẰNG GEMINI
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
                detail="File hình ảnh rỗng"
            )

        content_type = file.content_type or "image/jpeg"

        if not content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="Vui lòng tải lên file hình ảnh"
            )

        prompt = """
Bạn là AI chuyên đọc hóa đơn mua hàng.

Hãy đọc hình ảnh hóa đơn và trích xuất thông tin.

Trả về DUY NHẤT JSON hợp lệ, không markdown:

{
    "transaction_type": "chi",
    "amount": 0,
    "description": "",
    "category": "",
    "merchant": "",
    "date": ""
}

Quy tắc:

1. amount phải là tổng tiền thanh toán cuối cùng nếu xác định được.
2. Chuyển "50.000đ" thành 50000.
3. Chuyển "1.500.000đ" thành 1500000.
4. transaction_type thường là "chi".
5. description mô tả ngắn gọn nội dung mua hàng.
6. category chọn nhóm phù hợp như:
   - Ăn uống
   - Mua sắm
   - Di chuyển
   - Hóa đơn
   - Y tế
   - Giáo dục
   - Giải trí
   - Khác
7. merchant là tên cửa hàng nếu đọc được.
8. date là ngày trên hóa đơn nếu đọc được.
9. Nếu không đọc được thông tin nào thì để chuỗi rỗng hoặc amount = 0.
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

        result_text = clean_json_text(
            response.text or ""
        )

        result = json.loads(result_text)

        transaction_type = normalize_transaction_type(
            result.get("transaction_type", "chi")
        )

        amount = parse_money(
            result.get("amount")
        )

        description = str(
            result.get("description")
            or "Chi từ hóa đơn"
        ).strip()

        category = str(
            result.get("category")
            or "Khác"
        ).strip()

        merchant = str(
            result.get("merchant")
            or ""
        ).strip()

        bill_date = str(
            result.get("date")
            or ""
        ).strip()

        # -------------------------------------------------
        # LƯU GIAO DỊCH NẾU AI ĐỌC ĐƯỢC SỐ TIỀN
        # -------------------------------------------------

        saved_transaction = None

        if amount > 0:

            conn = get_db_connection()
            cur = conn.cursor()

            try:

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
                    (%s, %s, %s, %s, %s)
                    RETURNING id, transaction_date
                    """,
                    (
                        user_id,
                        transaction_type,
                        amount,
                        description,
                        category
                    )
                )

                row = cur.fetchone()

                conn.commit()

                saved_transaction = {
                    "id": row[0],
                    "user_id": user_id,
                    "transaction_type": transaction_type,
                    "amount": amount,
                    "description": description,
                    "category": category,
                    "transaction_date": (
                        row[1].isoformat()
                        if row[1]
                        else None
                    )
                }

            except Exception:
                conn.rollback()
                raise

            finally:

                cur.close()
                conn.close()

        return {
            "status": "success",
            "message": (
                "Đã quét và lưu hóa đơn"
                if saved_transaction
                else "Đã quét hóa đơn nhưng chưa xác định được số tiền"
            ),
            "data": {
                "transaction_type": transaction_type,
                "amount": amount,
                "description": description,
                "category": category,
                "merchant": merchant,
                "date": bill_date,
                "saved": saved_transaction is not None,
                "transaction": saved_transaction
            }
        }

    except HTTPException:
        raise

    except json.JSONDecodeError:

        raise HTTPException(
            status_code=500,
            detail="AI trả về dữ liệu không đúng định dạng JSON"
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Lỗi xử lý hóa đơn AI: {str(e)}"
        )


# =========================================================
# CHẠY LOCAL
# =========================================================

if __name__ == "__main__":

    import uvicorn

    port = int(
        os.getenv("PORT", "8000")
    )

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port
    )
