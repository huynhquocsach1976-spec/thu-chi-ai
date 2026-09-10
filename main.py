import os
import re
import hashlib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import google.generativeai as genai

app = FastAPI(title="Thu Chi AI Pro Backend")

# ---------------------------------------------------------
# 1. CẤU HÌNH BIẾN MÔI TRƯỜNG & DATABASE
# ---------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def get_db_connection():
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="Chưa cấu hình DATABASE_URL trong Environment!")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi kết nối Database Postgres: {str(e)}")

# Khởi tạo bảng khi Server Startup
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

# ---------------------------------------------------------
# 2. SCHEMAS (PYDANTIC)
# ---------------------------------------------------------
class AuthRequest(BaseModel):
    username: str
    password: str

class TransactionRequest(BaseModel):
    user_id: int
    text: str

# ---------------------------------------------------------
# 3. API ENDPOINTS
# ---------------------------------------------------------
@app.get("/")
def home():
    return {"status": "ok", "message": "Thu Chi AI Backend đang hoạt động"}

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
        raise HTTPException(status_code=500, detail=f"Lỗi Server Đăng nhập: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.post("/add-transaction-ai")
def add_transaction_ai(req: TransactionRequest):
    text = req.text.lower().strip()
    
    # 1. Bóc tách số tiền (xử lý k, m, tr, triệu, nghìn)
    amount = 0.0
    match = re.search(r'(\d+[\.,]?\d*)\s*(k|m|tr|triệu|nghìn|ngan)?', text)
    if match:
        raw_num = float(match.group(1).replace(',', '.'))
        unit = match.group(2)
        if unit in ['k', 'nghìn', 'ngan']:
            amount = raw_num * 1000
        elif unit in ['m', 'tr', 'triệu']:
            amount = raw_num * 1000000
        else:
            amount = raw_num if raw_num >= 1000 else raw_num * 1000
    else:
        raise HTTPException(status_code=400, detail="Không tìm thấy số tiền hợp lệ trong nội dung nhập!")

    # 2. Phân loại Thu / Chi
    tx_type = "chi"
    if any(kw in text for kw in ["lương", "luong", "thu", "được", "cho", "thưởng", "thu nhập"]):
        tx_type = "thu"

    # 3. Phân loại Danh mục
    category = "Khác"
    if any(kw in text for kw in ["cơm", "com", "bún", "phở", "cà phê", "ca phe", "ăn", "uống", "bánh"]):
        category = "Ăn uống"
    elif any(kw in text for kw in ["xăng", "xang", "xe", "grab", "taxi", "gửi xe"]):
        category = "Di chuyển"
    elif any(kw in text for kw in ["tiền nhà", "điện", "nước", "mạng", "wifi"]):
        category = "Hóa đơn"

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO transactions (user_id, type, amount, category, note) VALUES (%s, %s, %s, %s, %s) RETURNING id;",
            (req.user_id, tx_type, amount, category, req.text)
        )
        tx_id = cur.fetchone()[0]
        conn.commit()
        return {
            "status": "success",
            "message": f"Đã ghi nhận giao dịch: {req.text}",
            "data": {
                "id": tx_id,
                "type": "Thu nhập" if tx_type == "thu" else "Chi tiêu",
                "amount": amount,
                "category": category,
                "note": req.text
            }
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi lưu cơ sở dữ liệu: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/transactions/{user_id}")
def get_transactions(user_id: int):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT id, type, amount, category, note, date FROM transactions WHERE user_id = %s ORDER BY date DESC;",
            (user_id,)
        )
        records = cur.fetchall()
        return {"status": "success", "data": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy dữ liệu giao dịch: {str(e)}")
    finally:
        cur.close()
        conn.close()
