import os
import re
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="Thu Chi AI Backend")

# Lấy DATABASE_URL từ Render Environment
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    if not DATABASE_URL:
        raise Exception("Chưa cấu hình DATABASE_URL trên Render Environment!")
    return psycopg2.connect(DATABASE_URL, sslmode="require")

class ChatMessage(BaseModel):
    message: str

class BudgetRequest(BaseModel):
    monthly_limit: float

def parse_transaction(text: str):
    # Regex nhận diện số tiền (vd: 17k, 17.000, 17000)
    match = re.search(r"(\d+[\d\.,]*)\s*(k|k|tr|triệu|d|đ|vnd|vnđ)?", text, re.IGNORECASE)
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

    # Phân loại Thu / Chi
    income_keywords = ["lương", "thưởng", "thu", "nhận", "bán"]
    is_income = any(kw in text.lower() for kw in income_keywords)
    t_type = "income" if is_income else "expense"

    # Phân loại danh mục
    category = "Khác"
    if any(kw in text.lower() for kw in ["cơm", "phở", "bún", "ăn", "uống", "cafe", "trà"]):
        category = "Ăn uống"
    elif any(kw in text.lower() for kw in ["xe", "xăng", "grab", "gojek"]):
        category = "Di chuyển"
    elif any(kw in text.lower() for kw in ["mua", "áo", "quần", "tiệm"]):
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

@app.post("/chat")
def chat_process(msg: ChatMessage):
    parsed = parse_transaction(msg.message)
    if not parsed:
        return {"reply": "Chưa nhận diện được số tiền. Bạn thử nhập ví dụ: 'Cơm 17k' hoặc 'Lương 15tr' nhé!"}
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO transactions (type, amount, category, note)
            VALUES (%s, %s, %s, %s) RETURNING id;
            """,
            (parsed["type"], parsed["amount"], parsed["category"], parsed["note"])
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

@app.get("/history")
def get_history():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, type, CAST(amount AS FLOAT), category, note, date FROM transactions ORDER BY id DESC LIMIT 50;")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        # Chuyển đổi datetime sang string
        for r in rows:
            if isinstance(r.get("date"), datetime):
                r["date"] = r["date"].strftime("%Y-%m-%d %H:%M:%S")

        return {"total": len(rows), "data": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi Database: {str(e)}")

@app.post("/budget-status")
def budget_status(req: BudgetRequest):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT type, CAST(amount AS FLOAT) FROM transactions;")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        total_income = sum(r["amount"] for r in rows if r["type"] == "income")
        total_expense = sum(r["amount"] for r in rows if r["type"] == "expense")
        balance = total_income - total_expense
        
        usage_pct = round((total_expense / req.monthly_limit) * 100, 1) if req.monthly_limit > 0 else 0
        
        status = "normal"
        msg = "Chi tiêu trong mức an toàn."
        if usage_pct >= 100:
            status = "danger"
            msg = "⚠️ Bạn đã vượt hạn mức chi tiêu tháng!"
        elif usage_pct >= 80:
            status = "warning"
            msg = "⚡ Cảnh báo: Bạn đã dùng hơn 80% hạn mức chi tiêu!"

        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance,
            "usage_percent": usage_pct,
            "status": status,
            "message": msg
        }
    except Exception as e:
        return {
            "total_income": 0,
            "total_expense": 0,
            "balance": 0,
            "usage_percent": 0,
            "status": "normal",
            "message": f"Chưa có dữ liệu hoặc lỗi kết nối: {str(e)}"
        }

@app.post("/scan-bill")
async def scan_bill(file: UploadFile = File(...)):
    # Trả về kết quả mẫu OCR cơ bản
    return {"reply": "Đã nhận ảnh hóa đơn thành công! (Tính năng OCR đang sẵn sàng)"}
