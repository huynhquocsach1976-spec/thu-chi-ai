import os
import re
import hashlib
import base64
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import google.generativeai as genai

app = FastAPI(title="Thu Chi AI Pro Backend")

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def get_db_connection():
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="Chưa cấu hình DATABASE_URL trong Environment Variable!")
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi kết nối Postgres DB: {str(e)}")

@app.on_event("startup")
def startup_event():
    if not DATABASE_URL:
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
    except Exception as e:
        print(f"Lỗi khởi tạo Database: {e}")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

class AuthRequest(BaseModel):
    username: str
    password: str

class TransactionRequest(BaseModel):
    user_id: int
    text: str

class BillScanRequest(BaseModel):
    user_id: int
    image_base64: str

# --- ENDPOINTS ---

@app.get("/")
def home():
    return {"status": "ok", "message": "Backend Thu Chi AI Pro đang hoạt động"}

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
        raise HTTPException(status_code=400, detail=f"Tài khoản đã tồn tại hoặc có lỗi: {str(e)}")
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
            raise HTTPException(status_code=401, detail="Sai thông tin đăng nhập!")
        return {"status": "success", "user_id": user["id"], "username": user["username"]}
    finally:
        cur.close()
        conn.close()

@app.post("/add-transaction-ai")
def add_transaction_ai(req: TransactionRequest):
    text = req.text.lower().strip()
    
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
        raise HTTPException(status_code=400, detail="Không tìm thấy số tiền hợp lệ trong câu nhập!")

    tx_type = "chi"
    if any(kw in text for kw in ["lương", "luong", "thu", "được", "cho", "thưởng", "thu nhập"]):
        tx_type = "thu"

    category = "Khác"
    if any(kw in text for kw in ["cơm", "com", "bún", "phở", "cà phê", "ca phe", "ăn", "uống"]):
        category = "Ăn uống"
    elif any(kw in text for kw in ["xăng", "xang", "xe", "grab", "taxi"]):
        category = "Di chuyển"
    elif any(kw in text for kw in ["tiền nhà", "điện", "nước", "mạng"]):
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
            "message": f"Đã ghi nhận: {req.text}",
            "data": {"id": tx_id, "type": tx_type, "amount": amount, "category": category, "note": req.text}
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi lưu Database: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.post("/scan-bill")
def scan_bill(req: BillScanRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Chưa cấu hình GEMINI_API_KEY!")
    
    try:
        image_bytes = base64.b64decode(req.image_base64)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = """
        Phân tích hình ảnh hóa đơn/bill/mã QR này và trả về JSON thuần túy có cấu trúc:
        {
          "amount": (số tiền tổng thanh toán kiểu float),
          "category": (danh mục phù hợp như "Ăn uống", "Mua sắm", "Di chuyển", "Hóa đơn", "Khác"),
          "note": (tên cửa hàng hoặc nội dung thanh toán ngắn gọn)
        }
        Chỉ trả về JSON, không kèm chuỗi markdown hay văn bản thừa.
        """
        
        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": image_bytes}
        ])
        
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        
        amount = float(data.get("amount", 0))
        category = data.get("category", "Khác")
        note = data.get("note", "Quét hóa đơn QR/Ảnh")
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO transactions (user_id, type, amount, category, note) VALUES (%s, %s, %s, %s, %s) RETURNING id;",
            (req.user_id, "chi", amount, category, note)
        )
        tx_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return {
            "status": "success",
            "data": {"id": tx_id, "amount": amount, "category": category, "note": note}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý hóa đơn AI: {str(e)}")

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
        raise HTTPException(status_code=500, detail=f"Lỗi lấy lịch sử giao dịch: {str(e)}")
    finally:
        cur.close()
        conn.close()
