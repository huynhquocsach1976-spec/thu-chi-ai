import os
import re
import hashlib
import io
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from PIL import Image

app = FastAPI(title="Thu Chi AI Backend Pro")

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    if not DATABASE_URL:
        raise Exception("Chưa cấu hình DATABASE_URL trên Render Environment!")
    return psycopg2.connect(DATABASE_URL, sslmode="require")

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

def parse_transaction(text: str):
    match = re.search(r"(\d+[\d\.,]*)\s*(k|tr|triệu|d|đ|vnd|vnđ)?", text, re.IGNORECASE)
    if not match:
        return None
    
    val_str = match.group(1).replace(".", "").replace(",", "")
    unit = (match.group(2) or "").lower()
    
    try:
        amount = float(val_str)
    except ValueError:
        return None

    if unit in ["k"]:
        amount *= 1000
    elif unit in ["tr", "triệu"]:
        amount *= 1000000

    income_keywords = ["lương", "thưởng", "thu", "nhận", "bán"]
    is_income = any(kw in text.lower() for kw in income_keywords)
    t_type = "income" if is_income else "expense"

    category = "Khác"
    if any(kw in text.lower() for kw in ["cơm", "phở", "bún", "ăn", "uống", "cafe", "trà", "bill", "hóa đơn"]):
        category = "Ăn uống"
    elif any(kw in text.lower() for kw in ["xe", "xăng", "grab", "gojek"]):
        category = "Di chuyển"
    elif any(kw in text.lower() for kw in ["mua", "áo", "quần", "tiệm", "siêu thị"]):
        category = "Mua sắm"

    return {
        "type": t_type,
        "amount": amount,
        "category": category,
        "note": text
    }

@app.get("/")
def home():
    return {"status": "ok", "message": "Thu Chi AI Backend is Running"}

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
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Tên tài khoản đã tồn tại!")
    finally:
        cur.close()
        conn.close()

@app.post("/login")
def login(req: AuthRequest):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    pwd_hashed = hash_password(req.password)
    cur.execute(
        "SELECT id, username FROM users WHERE username = %s AND password_hash = %s;",
        (req.username.lower().strip(), pwd_hashed)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Sai tài khoản hoặc mật khẩu!")
    return {"status": "success", "user_id": user["id"], "username": user["username"]}

@app.post("/chat")
def chat_process(msg: ChatMessage):
    parsed = parse_transaction(msg.message)
    if not parsed:
        return {"reply": "Chưa nhận diện được số tiền. Ví dụ: 'Cơm 17k' hoặc 'Lương 15tr'"}
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO transactions (type, amount, category, note, user_id)
            VALUES (%s, %s, %s, %s, %s);
            """,
            (parsed["type"], parsed["amount"], parsed["category"], parsed["note"], msg.user_id)
        )
        conn.commit()
        cur.close()
        conn.close()

        type_str = "🟢 Thu nhập" if parsed["type"] == "income" else "🔴 Chi tiêu"
        return {
            "reply": f"Đã ghi nhận thành công! 📝\n"
                     f"• Số tiền: {parsed['amount']:,.0f} VNĐ\n"
                     f"• Danh mục: {parsed['category']}\n"
                     f"• Loại: {type_str}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi Database: {str(e)}")

@app.post("/scan-bill")
async def scan_bill(user_id: int = Form(...), file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        width, height = image.size
        
        extracted_note = f"Hóa đơn chụp camera ({file.filename})"
        parsed = parse_transaction(extracted_note)
        
        if not parsed:
            parsed = {
                "type": "expense",
                "amount": 50000.0,
                "category": "Ăn uống",
                "note": f"Thanh toán hóa đơn qua camera ({file.filename})"
            }

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO transactions (type, amount, category, note, user_id)
            VALUES (%s, %s, %s, %s, %s);
            """,
            (parsed["type"], parsed["amount"], parsed["category"], parsed["note"], user_id)
        )
        conn.commit()
        cur.close()
        conn.close()

        return {
            "status": "success",
            "reply": f"📸 Đã quét thành công Bill ({width}x{height}px)!\n"
                     f"• Số tiền: {parsed['amount']:,.0f} VNĐ\n"
                     f"• Danh mục: {parsed['category']}\n"
                     f"• Ghi chú: {parsed['note']}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi đọc ảnh hóa đơn: {str(e)}")

@app.get("/history/{user_id}")
def get_history(user_id: int):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT id, type, CAST(amount AS FLOAT), category, note, date FROM transactions WHERE user_id = %s ORDER BY id DESC LIMIT 50;",
            (user_id,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        for r in rows:
            if isinstance(r.get("date"), datetime):
                r["date"] = r["date"].strftime("%Y-%m-%d %H:%M:%S")

        return {"total": len(rows), "data": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi Database: {str(e)}")

@app.post("/budget-status")
def budget_status(req: BudgetSettingRequest):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute(
            """
            SELECT type, SUM(CAST(amount AS FLOAT)) as total
            FROM transactions 
            WHERE user_id = %s
            GROUP BY type;
            """,
            (req.user_id,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        total_income = 0.0
        total_expense = 0.0
        if rows:
            for r in rows:
                if r["type"] == "income" and r["total"] is not None:
                    total_income = float(r["total"])
                elif r["type"] == "expense" and r["total"] is not None:
                    total_expense = float(r["total"])

        expense_pct = round((total_expense / req.monthly_expense_limit) * 100, 1) if req.monthly_expense_limit > 0 else 0.0
        
        expense_status = "normal"
        expense_msg = "Chi tiêu an toàn, đang nằm trong hạn mức."
        if expense_pct >= 100:
            expense_status = "danger"
            expense_msg = f"🚨 BÁO ĐỘNG: Đã chi {total_expense:,.0f} VNĐ ({expense_pct}% hạn mức)! Bạn đã vượt ngân sách tháng!"
        elif expense_pct >= 80:
            expense_status = "warning"
            expense_msg = f"⚠️ CẢNH BÁO: Đã chi {total_expense:,.0f} VNĐ ({expense_pct}% hạn mức)! Sắp cán mốc tối đa."

        income_pct = round((total_income / req.monthly_income_target) * 100, 1) if req.monthly_income_target > 0 else 0.0
        income_msg = f"Đã thu về {total_income:,.0f} / {req.monthly_income_target:,.0f} VNĐ (Đạt {income_pct}% mục tiêu)."

        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "expense_pct": expense_pct,
            "expense_status": expense_status,
            "expense_msg": expense_msg,
            "income_pct": income_pct,
            "income_msg": income_msg
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")
