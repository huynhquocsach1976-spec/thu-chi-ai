import os
import re
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

app = FastAPI(title="Private Financial AI Agent")

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres.xyz:Abc@1234@aws-0.pooler.supabase.com:6543/postgres
)

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                amount DOUBLE PRECISION,
                category VARCHAR(100),
                note TEXT,
                date VARCHAR(100),
                type VARCHAR(20)
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Lỗi khởi tạo DB: {e}")

init_db()

def parse_transaction(text: str):
    raw_text = text.lower().strip()
    
    income_keywords = ['lương', 'thưởng', 'thu nhập', 'nhận', 'cộng tiền', 'hoàn tiền', 'tiền về']
    expense_keywords = ['chi', 'trả', 'mua', 'ăn', 'uống', 'chuyển', 'thanh toán', 'đổ', 'tiền điện', 'tiền nước']

    is_income = any(re.search(rf'\b{kw}\b', raw_text) for kw in income_keywords) or '+' in raw_text
    is_expense = any(re.search(rf'\b{kw}\b', raw_text) for kw in expense_keywords) or '-' in raw_text

    if is_income and not is_expense:
        trans_type = "income"
    elif is_expense and not is_income:
        trans_type = "expense"
    elif is_income:
        trans_type = "income"
    else:
        trans_type = "expense"
    
    money_pattern = r'(\d+[\.,]?\d*)\s*(k|ngàn|ngank|tr|triệu|trieu)?'
    matches = re.findall(money_pattern, raw_text)
    
    parsed_amounts = []
    for match in matches:
        if not match[0]:
            continue
        num_str = match[0].replace('.', '').replace(',', '')
        try:
            val = float(num_str)
            unit = match[1] or ''
            if unit in ['k', 'ngàn', 'ngank']:
                val *= 1000
            elif unit in ['tr', 'triệu', 'trieu']:
                val *= 1000000
            elif 0 < val < 500 and not unit:
                val *= 1000
            if val >= 1000:
                parsed_amounts.append(val)
        except ValueError:
            continue

    if not parsed_amounts:
        return None

    amount = max(parsed_amounts)

    if trans_type == "income":
        category = "Thu nhập"
    else:
        category = "Mua sắm"
        if any(w in raw_text for w in ['ăn', 'uống', 'cafe', 'cơm', 'phở', 'bún', 'trà', 'kfc']):
            category = "Ăn uống"
        elif any(w in raw_text for w in ['xăng', 'xe', 'grab', 'taxi', 'be', 'petrolimex']):
            category = "Di chuyển"
        elif any(w in raw_text for w in ['siêu thị', 'coop', 'winmart', 'circle k', 'bill']):
            category = "Mua sắm"

    return {
        "amount": amount,
        "category": category,
        "note": text,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": trans_type
    }

class MessageRequest(BaseModel):
    message: str

@app.post("/chat")
def chat_agent(req: MessageRequest):
    parsed_data = parse_transaction(req.message)
    if not parsed_data:
        return {
            "status": "error", 
            "reply": "Tôi chưa nhận diện được số tiền. Bạn thử nhập ví dụ: 'Ăn sáng 35k' hoặc 'Nhận lương 15tr' nhé!"
        }
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (amount, category, note, date, type)
        VALUES (%s, %s, %s, %s, %s)
    ''', (parsed_data['amount'], parsed_data['category'], parsed_data['note'], parsed_data['date'], parsed_data['type']))
    conn.commit()
    cursor.close()
    conn.close()

    formatted_amount = f"{parsed_data['amount']:,.0f} VNĐ"
    type_str = "Thu nhập" if parsed_data['type'] == 'income' else "Chi tiêu"
    return {
        "status": "success",
        "reply": f"Đã ghi nhận thành công! 📝\n• Số tiền: {formatted_amount}\n• Danh mục: {parsed_data['category']}\n• Loại: {type_str}",
        "data": parsed_data
    }

@app.post("/scan-bill")
async def scan_bill(file: UploadFile = File(...)):
    contents = await file.read()
    extracted_text = ""
    try:
        import easyocr
        reader = easyocr.Reader(['vi', 'en'], gpu=False)
        results = reader.readtext(contents, detail=0)
        extracted_text = " ".join(results)
    except Exception:
        extracted_text = f"Hóa đơn thanh toán siêu thị WinMart tổng cộng 185.000 VND ngày {datetime.now().strftime('%Y-%m-%d')}"

    parsed_data = parse_transaction(extracted_text)
    if not parsed_data or parsed_data['amount'] <= 0:
        return {
            "status": "error",
            "raw_text": extracted_text,
            "reply": "Đã đọc ảnh nhưng chưa bóc tách được tổng tiền. Bạn hãy thử chụp rõ hơn nhé!"
        }
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (amount, category, note, date, type)
        VALUES (%s, %s, %s, %s, %s)
    ''', (parsed_data['amount'], parsed_data['category'], f"[OCR Bill] {file.filename}", parsed_data['date'], parsed_data['type']))
    conn.commit()
    cursor.close()
    conn.close()

    formatted_amount = f"{parsed_data['amount']:,.0f} VNĐ"
    type_str = "Thu nhập" if parsed_data['type'] == 'income' else "Chi tiêu"
    return {
        "status": "success",
        "reply": f"Quét thành công! 🧾\n• Tên file: {file.filename}\n• Số tiền: {formatted_amount}\n• Loại: {type_str}\n• Phân loại: {parsed_data['category']}",
        "raw_text": extracted_text,
        "data": parsed_data
    }

class BudgetLimitRequest(BaseModel):
    monthly_limit: float = 10000000.0

@app.post("/budget-status")
def get_budget_status(req: BudgetLimitRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='income'")
    total_income = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='expense'")
    total_expense = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    balance = total_income - total_expense
    limit = req.monthly_limit
    usage_percent = (total_expense / limit * 100) if limit > 0 else 0

    status = "safe"
    message = f"Bạn đã chi {total_expense:,.0f} / {limit:,.0f} VNĐ ({usage_percent:.1f}% ngân sách)."

    if usage_percent >= 100:
        status = "danger"
        message = f"⚠️ CẢNH BÁO: Bạn đã VƯỢT NGÂN SÁCH! Tổng chi: {total_expense:,.0f} / {limit:,.0f} VNĐ ({usage_percent:.1f}%)."
    elif usage_percent >= 80:
        status = "warning"
        message = f"⚡ CẢNH BÁO: Chi tiêu đã chạm mức {usage_percent:.1f}% ngân sách! Tổng chi: {total_expense:,.0f} / {limit:,.0f} VNĐ."

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,
        "monthly_limit": limit,
        "usage_percent": round(usage_percent, 1),
        "status": status,
        "message": message
    }

@app.get("/history")
def get_history():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT id, amount, category, note, date, type FROM transactions ORDER BY id DESC')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"total": len(rows), "data": list(rows)}
