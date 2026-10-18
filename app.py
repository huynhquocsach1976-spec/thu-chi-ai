"""Thu Chi AI Pro - Phiên bản đã tinh chỉnh (bỏ phụ lục)."""
import html
import os
import time
from datetime import datetime, timedelta
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Thu Chi AI Pro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Thu Chi AI Pro - Quản lý tài chính thông minh v1.2"},
)

# =========================================================
# CẤU HÌNH
# =========================================================
def get_config(name, default=""):
    value = os.getenv(name)
    if value:
        return value
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default

def clean_url(url):
    url = str(url).strip().strip('"').strip("'")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")

BACKEND_URL = clean_url(get_config("BACKEND_URL", "https://thu-chi-ai.onrender.com"))
TIMEZONE = "Asia/Ho_Chi_Minh"
REMEMBER_LOGIN = str(get_config("REMEMBER_LOGIN", "1")).strip().lower() not in ("0", "false", "no", "off")
SESSION_PARAM = "s"
TOTAL_LABEL = "Tổng chi tiêu"
CATEGORIES = [
    "Ăn uống", "Di chuyển", "Mua sắm", "Hóa đơn & Tiện ích", "Nhà ở",
    "Giải trí", "Sức khỏe", "Giáo dục", "Lương", "Thưởng", "Đầu tư", "Khác",
]
EXPENSE_CATEGORIES = [c for c in CATEGORIES if c not in ("Lương", "Thưởng")]
LEVEL_ICON = {"ok": "🟢", "warning": "🟠", "over": "🔴"}
COLD_START_HINT = "Server miễn phí có thể mất 30–60 giây để khởi động nếu lâu không dùng."

# =========================================================
# GIAO DIỆN NÂNG CẤP
# =========================================================
st.markdown(
    """
<style>
:root {
    --primary: #2563eb;
    --success: #16a34a;
    --warning: #f59e0b;
    --danger: #dc2626;
    --bg-gradient: linear-gradient(135deg, #f0f4f8 0%, #e6f0fa 50%, #f8fafc 100%);
}
.stApp {
    background: var(--bg-gradient);
    color: #1e293b;
}
[data-testid="stForm"] {
    background: rgba(255,255,255,0.9) !important;
    backdrop-filter: blur(16px);
    border: 1px solid rgba(203,213,225,0.6) !important;
    border-radius: 20px !important;
    padding: 28px 32px !important;
    box-shadow: 0 25px 35px -10px rgba(37,99,235,0.08) !important;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
[data-testid="stForm"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 30px 40px -12px rgba(37,99,235,0.12) !important;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    background: rgba(226,232,240,0.7);
    padding: 8px;
    border-radius: 16px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 12px;
    padding: 10px 20px;
    color: #64748b;
    font-weight: 500;
    transition: all 0.2s ease;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%) !important;
    color: #fff !important;
    box-shadow: 0 4px 12px rgba(37,99,235,0.25);
}
.stButton > button, [data-testid="stFormSubmitButton"] > button, .stDownloadButton > button {
    width: 100%;
    min-height: 46px;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 0.95rem;
    background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%) !important;
    color: #fff !important;
    border: none !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 20px -5px rgba(59,130,246,0.35);
}
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.9);
    border-radius: 16px;
    padding: 16px 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    transition: transform 0.2s ease;
}
[data-testid="stMetric"]:hover { transform: scale(1.02); }
[data-testid="stMetricLabel"] { font-weight: 600; color: #475569; }
[data-testid="stMetricValue"] { font-weight: 700; }
.tx-card {
    display: flex; align-items: center; gap: 14px;
    background: rgba(255,255,255,0.95);
    border: 1px solid #e2e8f0; border-radius: 16px;
    padding: 14px 16px; margin-bottom: 10px;
    box-shadow: 0 2px 8px rgba(15,23,42,0.04);
    transition: all 0.2s ease;
}
.tx-card:hover { transform: translateX(4px); box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
.tx-icon {
    flex: 0 0 44px; height: 44px; border-radius: 14px;
    background: linear-gradient(135deg, #eff6ff, #dbeafe);
    display: flex; align-items: center; justify-content: center; font-size: 1.3rem;
}
.tx-main { flex: 1 1 auto; min-width: 0; }
.tx-title { font-weight: 600; color: #1e293b; font-size: 0.95rem; }
.tx-sub { font-size: 0.8rem; color: #64748b; margin-top: 3px; }
.tx-amt { flex: 0 0 auto; font-weight: 700; font-size: 1rem; white-space: nowrap; }
.tx-in { color: #16a34a; } .tx-out { color: #dc2626; }
.sidebar-notice {
    background: linear-gradient(135deg, #fef3c7, #fde68a);
    border-radius: 12px; padding: 10px 12px; font-size: 0.85rem; color: #92400e;
    margin-top: 8px;
}
div[data-testid="stProgressBar"] > div { border-radius: 999px; }
@media (max-width: 768px) {
    .block-container { padding: 2rem 1rem 3.5rem !important; }
    h1 { font-size: 1.5rem !important; }
    h2 { font-size: 1.15rem !important; }
    [data-testid="stForm"] { padding: 20px 16px !important; }
    .tx-card { padding: 12px; }
}
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# QUẢN LÝ PHIÊN
# =========================================================
for key, default in (("token", None), ("user_id", None), ("username", ""), ("page", "📖 Giới thiệu")):
    st.session_state.setdefault(key, default)

def is_logged_in():
    return bool(st.session_state.token)

def remember(token):
    if REMEMBER_LOGIN and token:
        st.query_params[SESSION_PARAM] = token

def forget():
    try:
        if SESSION_PARAM in st.query_params:
            del st.query_params[SESSION_PARAM]
    except Exception:
        pass

def start_session(result):
    st.session_state.token = result["token"]
    st.session_state.user_id = result.get("user_id")
    st.session_state.username = result.get("username", "")
    st.session_state.pop("tx", None)
    remember(result["token"])

def logout(notice=None):
    for key in ("token", "user_id", "tx", "page", "report_xlsx", "report_pdf"):
        st.session_state.pop(key, None)
    st.session_state.username = ""
    forget()
    if notice:
        st.session_state["notice"] = notice

def notify_success(msg):
    st.session_state["notice"] = ("success", msg)
def notify_warning(msg):
    st.session_state["notice"] = ("warning", msg)
def notify_error(msg):
    st.session_state["notice"] = ("error", msg)

def show_notice():
    if notice := st.session_state.pop("notice", None):
        kind, text = notice if isinstance(notice, tuple) else ("success", notice)
        if kind == "success": st.success(f"✅ {text}")
        elif kind == "warning": st.warning(f"⚠️ {text}")
        elif kind == "error": st.error(f"❌ {text}")
        else: st.info(text)

# =========================================================
# API CÓ XỬ LÝ LỖI NÂNG CAO
# =========================================================
@st.cache_resource
def http():
    return requests.Session()

def get_error(response):
    try:
        detail = response.json().get("detail", "Có lỗi xảy ra")
        if isinstance(detail, list):
            return "; ".join(i.get("msg", str(i)) if isinstance(i, dict) else str(i) for i in detail)
        return str(detail)
    except Exception:
        return response.text or f"Mã lỗi {response.status_code}"

def api_call(method, path, timeout=60, max_retries=2, raw=False, **kwargs):
    headers = kwargs.pop("headers", {})
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = http().request(method, BACKEND_URL + path, headers=headers, timeout=timeout, **kwargs)
        except requests.exceptions.Timeout:
            last_error = "Server phản hồi quá lâu. Đang thử lại..."
        except requests.exceptions.ConnectionError:
            last_error = f"Không kết nối được. {COLD_START_HINT}"
        except requests.exceptions.RequestException as e:
            last_error = str(e)
        else:
            if response.status_code == 401 and token:
                logout("Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại.")
                st.rerun()
            if response.ok:
                if raw:
                    return True, response.content
                try:
                    return True, response.json()
                except ValueError:
                    return False, "Dữ liệu trả về không hợp lệ."
            last_error = get_error(response)
        
        if attempt < max_retries:
            time.sleep(1.5)
            continue
        return False, last_error
    return False, last_error

def restore_session():
    if is_logged_in() or not REMEMBER_LOGIN or st.session_state.get("restore_tried"):
        return
    st.session_state["restore_tried"] = True
    token = st.query_params.get(SESSION_PARAM)
    if not token:
        return
    with st.spinner("Đang khôi phục phiên đăng nhập..."):
        ok, data = api_call("GET", "/me", headers={"Authorization": f"Bearer {token}"}, timeout=90)
        if ok and data.get("token"):
            start_session(data)
            notify_success("Đã khôi phục phiên đăng nhập!")

@st.cache_data(ttl=60, show_spinner=False)
def check_backend():
    try:
        return requests.get(BACKEND_URL + "/", timeout=5).status_code == 200
    except Exception:
        return False

def load_transactions(force=False):
    if force or "tx" not in st.session_state:
        ok, data = api_call("GET", "/transactions", params={"limit": 2000})
        if not ok:
            return False, data
        if not isinstance(data, list):
            return False, "Dữ liệu giao dịch không hợp lệ."
        st.session_state.tx = data
    return True, st.session_state.tx

def invalidate_transactions():
    st.session_state.pop("tx", None)

# =========================================================
# CÔNG CỤ ĐỊNH DẠNG
# =========================================================
def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def fmt_money(value):
    amount = safe_float(value)
    if abs(amount) >= 1_000_000:
        return f"{amount/1_000_000:,.2f} triệu đ".replace(",", ".")
    elif abs(amount) >= 1_000:
        return f"{amount/1_000:,.1f}k đ".replace(",", ".")
    return f"{amount:,.0f} đ".replace(",", ".")

def fmt_money_full(value):
    return f"{safe_float(value):,.0f}".replace(",", ".") + " đ"

def fmt_month(month):
    return f"{month[5:]}/{month[:4]}"

CATEGORY_ICON = {
    "Ăn uống": "🍜", "Di chuyển": "🚗", "Mua sắm": "🛍️", "Hóa đơn & Tiện ích": "💡", "Nhà ở": "🏠",
    "Giải trí": "🎬", "Sức khỏe": "💊", "Giáo dục": "📚", "Lương": "💼", "Thưởng": "🎁",
    "Đầu tư": "📈", "Khác": "📌",
}

def show_transaction_cards(df, limit=50):
    cards = []
    for r in df.head(limit).itertuples():
        is_income = r.transaction_type == "Thu"
        title = html.escape(r.description or "(không mô tả)")
        sub = html.escape(f"{r.category} · {r.created_at:%d/%m/%Y %H:%M}")
        sign = "+" if is_income else "-"
        cards.append(f'''
        <div class="tx-card">
            <div class="tx-icon">{CATEGORY_ICON.get(r.category, "📌")}</div>
            <div class="tx-main">
                <div class="tx-title">{title}</div>
                <div class="tx-sub">{sub}</div>
            </div>
            <div class="tx-amt {"tx-in" if is_income else "tx-out"}">{sign}{fmt_money_full(r.amount)}</div>
        </div>
        ''')
    st.markdown("".join(cards), unsafe_allow_html=True)
    if len(df) > limit:
        st.caption(f"Hiển thị {limit}/{len(df)} giao dịch mới nhất. Sử dụng bộ lọc để xem thêm.")

def show_budget_alerts(alerts):
    for a in alerts or []:
        pct = safe_float(a.get("percent"))
        detail = f"**{a.get('label')}**: {fmt_money_full(a.get('spent'))} / {fmt_money_full(a.get('monthly_limit'))} ({pct:.0f}%)"
        if a.get("level") == "over":
            st.error(f"🔴 Vượt ngân sách! {detail}")
        elif a.get("level") == "warning":
            st.warning(f"🟠 Sắp hết ngân sách. {detail}")

def show_result(result, amount_label="💰 Số tiền"):
    c1, c2, c3 = st.columns(3)
    c1.metric(amount_label, fmt_money_full(result.get("amount")))
    c2.metric("Loại", result.get("transaction_type", "Chi"))
    c3.metric("Danh mục", result.get("category", "Khác"))
    st.write("**Mô tả:**", result.get("description", ""))
    show_budget_alerts(result.get("budget_alerts"))

def build_dataframe(rows):
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True).dt.tz_convert(TIMEZONE)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["category"] = df["category"].fillna("Khác")
    df["description"] = df["description"].fillna("")
    df["month"] = df["created_at"].dt.strftime("%Y-%m")
    df["date"] = df["created_at"].dt.strftime("%d/%m/%Y")
    return df

def current_month():
    return pd.Timestamp.now(tz=TIMEZONE).strftime("%Y-%m")

def month_selector(label, key):
    months = {current_month()}
    ok, tx = load_transactions()
    if ok and tx:
        df = build_dataframe([t for t in tx if isinstance(t, dict)])
        if not df.empty:
            months |= set(df["month"].unique())
    return st.selectbox(label, sorted(months, reverse=True), key=key, format_func=fmt_month)

# =========================================================
# TRANG GIỚI THIỆU — ĐÃ BỎ PHỤ LỤC / MỤC LỤC
# =========================================================
DEFAULT_INTRO = """
**💰 Thu Chi AI Pro** — Quản lý tài chính cá nhân thông minh với trí tuệ nhân tạo

### ✨ Điểm nổi bật
- 🧠 **AI hiểu ngôn ngữ tự nhiên**: chỉ cần nói "ăn cơm 40k" là xong
- 📷 **Quét hóa đơn tự động**: chụp ảnh → AI đọc hết → tự lưu
- 📊 **Thống kê trực quan**: biểu đồ rõ ràng, theo tháng/danh mục
- 🎯 **Ngân sách thông minh**: cảnh báo sớm khi sắp/vượt hạn mức
- 📑 **Xuất báo cáo**: Excel, PDF đầy đủ
- 🔒 **An toàn & riêng tư**: dữ liệu của bạn được bảo vệ

### 📌 Hướng dẫn nhanh
1. Vào **🤖 Nhập giao dịch** để ghi nhận thu/chi
2. Vào **📷 Quét hóa đơn** để nhập nhanh bằng ảnh
3. Vào **📊 Lịch sử** để xem, tìm, sửa, xóa
4. Vào **🎯 Ngân sách** để đặt hạn mức chi tiêu
5. Vào **📑 Báo cáo** để tải file về
"""

def show_intro():
    st.markdown(DEFAULT_INTRO)

def page_intro():
    show_intro()

def toggle_intro_login():
    st.session_state["show_intro_login"] = not st.session_state.get("show_intro_login", False)

# =========================================================
# TRANG ĐĂNG NHẬP / ĐĂNG KÝ
# =========================================================
def auth_page():
    _, center, _ = st.columns([0.6, 2.5, 0.6])
    with center:
        st.markdown("""
        <div style="text-align:center; margin: 20px 0;">
            <h1 style="font-size:2.3rem; background:linear-gradient(90deg,#2563eb,#1d4ed8);
                -webkit-background-clip:text; color:transparent; margin-bottom:0;">💰 Thu Chi AI Pro</h1>
            <p style="color:#64748b; font-size:1rem; margin-top:6px;">Quản lý tài chính thông minh — đơn giản, nhanh chóng, hiệu quả</p>
        </div>
        """, unsafe_allow_html=True)
        
        show_notice()
        st.button("📖 Xem giới thiệu sản phẩm", on_click=toggle_intro_login)
        if st.session_state.get("show_intro_login"):
            with st.expander("📖 Giới thiệu", expanded=True):
                show_intro()
        
        tab_login, tab_reg, tab_about = st.tabs(["🔐 Đăng nhập", "📝 Đăng ký", "ℹ️ Về dự án"])
        with tab_login:
            with st.form("login_form"):
                u = st.text_input("Tên đăng nhập", placeholder="Nhập tên của bạn")
                p = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu")
                sub = st.form_submit_button("🔐 Đăng nhập ngay")
            if sub:
                if not u.strip() or not p:
                    st.warning("Vui lòng điền đầy đủ thông tin.")
                else:
                    with st.spinner("Đang xác thực..."):
                        ok, res = api_call("POST", "/login", json={"username": u.strip(), "password": p}, timeout=90)
                    if ok and res.get("token"):
                        start_session(res)
                        notify_success("Đăng nhập thành công! Xin chào 🎉")
                        st.rerun()
                    else:
                        st.error(f"Đăng nhập thất bại: {res}")
        
        with tab_reg:
            with st.form("reg_form"):
                u2 = st.text_input("Tên đăng nhập", placeholder="Ít nhất 3 ký tự")
                p2 = st.text_input("Mật khẩu", type="password", placeholder="Ít nhất 6 ký tự")
                cf = st.text_input("Nhập lại mật khẩu", type="password")
                sub2 = st.form_submit_button("📝 Tạo tài khoản")
            if sub2:
                if len(u2.strip()) < 3:
                    st.warning("Tên đăng nhập quá ngắn (tối thiểu 3 ký tự).")
                elif len(p2) < 6:
                    st.warning("Mật khẩu quá ngắn (tối thiểu 6 ký tự).")
                elif p2 != cf:
                    st.error("Hai mật khẩu không khớp.")
                else:
                    with st.spinner("Đang tạo tài khoản..."):
                        ok, res = api_call("POST", "/register", 
                                          json={"username": u2.strip(), "password": p2}, timeout=90)
                    if ok and res.get("token"):
                        start_session(res)
                        notify_success("Tạo tài khoản thành công! 🎉")
                        st.rerun()
                    else:
                        st.error(f"Đăng ký thất bại: {res}")
        
        with tab_about:
            st.info("""
            **Thu Chi AI Pro v1.2**
            - Phát triển: Dự án mở 🚀
            - Công nghệ: Python + Streamlit + AI Backend
            - Mục tiêu: Giúp mọi người quản lý tài chính dễ dàng hơn
            """)

# =========================================================
# TRANG NHẬP GIAO DỊCH
# =========================================================
def page_ai():
    st.subheader("🤖 Nhập giao dịch bằng AI")
    st.info("💡 Ví dụ: 'ăn phở 35k', 'lương tháng này 15 triệu', 'điện 850 nghìn'")
    
    with st.form("ai_form", clear_on_submit=True):
        txt = st.text_input("Nội dung chi tiêu/thu nhập", placeholder="Nhập ở đây...", max_chars=300)
        sub = st.form_submit_button("✨ AI phân tích & lưu")
    if sub:
        if not txt.strip():
            st.warning("Vui lòng nhập nội dung!")
        else:
            with st.spinner("🤖 AI đang hiểu..."):
                ok, res = api_call("POST", "/add-transaction-ai", json={"text": txt.strip()}, timeout=120)
            if ok:
                invalidate_transactions()
                notify_success("Đã thêm giao dịch!")
                show_result(res)
            else:
                st.error(f"Lỗi: {res}")
    
    with st.expander("✍️ Nhập thủ công chi tiết hơn", icon="✍️"):
        with st.form("manual_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            loai = c1.selectbox("Loại giao dịch", ["Chi", "Thu"])
            tien = c2.number_input("Số tiền (đồng)", min_value=0.0, step=1000.0)
            c3, c4 = st.columns(2)
            dm = c3.selectbox("Danh mục", CATEGORIES, index=CATEGORIES.index("Khác"))
            mt = c4.text_input("Mô tả chi tiết")
            sub_m = st.form_submit_button("💾 Lưu giao dịch")
        if sub_m:
            if tien <= 0:
                st.warning("Số tiền phải > 0")
            else:
                ok, res = api_call("POST", "/transactions", 
                    json={"amount": tien, "transaction_type": loai, "category": dm, "description": mt.strip()})
                if ok:
                    invalidate_transactions()
                    notify_success("Đã lưu!")
                    show_result(res)
                else:
                    st.error(f"Lỗi: {res}")

# =========================================================
# TRANG QUÉT HÓA ĐƠN
# =========================================================
def page_bill():
    st.subheader("📷 Quét hóa đơn bằng AI")
    st.info("Chụp rõ nét hóa đơn → AI tự nhận diện tổng tiền & danh mục")
    
    file = st.file_uploader("Tải ảnh hóa đơn lên", type=["jpg", "jpeg", "png", "webp"])
    if not file:
        return
    st.image(file, caption="Hóa đơn của bạn", width=350)
    if st.button("🔍 Bắt đầu quét & lưu", type="primary"):
        data = file.getvalue()
        if not data:
            st.error("File rỗng!")
            return
        with st.spinner("🤖 Đang đọc hóa đơn..."):
            ok, res = api_call("POST", "/scan-bill", files={"file": (file.name, data, file.type or "image/jpeg")}, timeout=120)
        if ok:
            invalidate_transactions()
            notify_success("Quét xong & đã lưu giao dịch!")
            show_result(res, "💰 Tổng tiền")
        else:
            st.error(f"Lỗi: {res}")

# =========================================================
# TRANG LỊCH SỬ & THỐNG KÊ
# =========================================================
def edit_section(fdf):
    with st.expander("✏️ Sửa / 🗑️ Xóa giao dịch", icon="⚙️"):
        opts = {r.id: f"{r.date} | {r.description or '—'} | {fmt_money_full(r.amount)}" for r in fdf.itertuples()}
        sel = st.selectbox("Chọn giao dịch", list(opts), format_func=opts.get)
        row = fdf[fdf["id"] == sel].iloc[0]
        tid = int(sel)
        
        with st.form(f"edit_{tid}"):
            dsc = st.text_input("Mô tả", value=str(row["description"]))
            amt = st.number_input("Số tiền", min_value=1.0, value=float(row["amount"]), step=1000.0)
            c1, c2 = st.columns(2)
            typ = c1.selectbox("Loại", ["Chi", "Thu"], index=0 if row["transaction_type"] == "Chi" else 1)
            cat = c2.selectbox("Danh mục", CATEGORIES, index=CATEGORIES.index(str(row["category"])))
            confirm_del = st.checkbox("✅ Xác nhận xóa vĩnh viễn")
            col_save, col_del = st.columns(2)
            do_save = col_save.form_submit_button("💾 Cập nhật")
            do_del = col_del.form_submit_button("🗑️ Xóa")
        
        if do_save:
            ok, _ = api_call("PUT", f"/transactions/{tid}", 
                json={"amount": amt, "transaction_type": typ, "category": cat, "description": dsc.strip()})
            if ok:
                invalidate_transactions()
                notify_success("Cập nhật thành công!")
                st.rerun()
            else:
                st.error("Cập nhật thất bại!")
        if do_del:
            if not confirm_del:
                st.warning("Vui lòng tick ô xác nhận!")
            else:
                ok, _ = api_call("DELETE", f"/transactions/{tid}")
                if ok:
                    invalidate_transactions()
                    notify_success("Đã xóa!")
                    st.rerun()
                else:
                    st.error("Xóa thất bại!")

def page_history():
    st.subheader("📊 Lịch sử & Thống kê")
    reload = st.button("🔄 Làm mới dữ liệu")
    ok, tx = load_transactions(force=reload)
    if not ok:
        st.error(tx)
        return
    rows = [t for t in tx if isinstance(t, dict)]
    if not rows:
        st.info("Chưa có giao dịch nào. Hãy nhập giao dịch đầu tiên!")
        return
    
    df = build_dataframe(rows)
    
    # Bộ lọc nâng cao
    st.markdown("#### 🔎 Bộ lọc")
    c1, c2, c3, c4 = st.columns([1, 1, 1.5, 1.5])
    months = sorted(df["month"].unique(), reverse=True)
    m_sel = c1.selectbox("Tháng", ["Tất cả"] + months, format_func=lambda m: "Tất cả" if m == "Tất cả" else fmt_month(m))
    t_sel = c2.selectbox("Loại", ["Tất cả", "Thu", "Chi"])
    cats_all = sorted(df["category"].unique().tolist())
    cat_sel = c3.multiselect("Danh mục", cats_all)
    kw = c4.text_input("Tìm theo mô tả")
    
    fdf = df
    if m_sel != "Tất cả": fdf = fdf[fdf["month"] == m_sel]
    if t_sel != "Tất cả": fdf = fdf[fdf["transaction_type"] == t_sel]
    if cat_sel: fdf = fdf[fdf["category"].isin(cat_sel)]
    if kw.strip(): fdf = fdf[fdf["description"].str.contains(kw.strip(), case=False, na=False)]
    
    if fdf.empty:
        st.info("Không tìm thấy giao dịch phù hợp.")
        return
    
    # Thống kê tóm tắt
    thu = fdf[fdf["transaction_type"] == "Thu"]["amount"].sum()
    chi = fdf[fdf["transaction_type"] == "Chi"]["amount"].sum()
    du = thu - chi
    slg = len(fdf)
    
    st.markdown("#### 📈 Tổng quan")
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("💵 Tổng thu", fmt_money(thu))
    mc2.metric("💸 Tổng chi", fmt_money(chi))
    mc3.metric("💰 Số dư", fmt_money(du), delta=fmt_money(du))
    mc4.metric("🧾 Số giao dịch", f"{slg}")
    
    # Biểu đồ
    st.divider()
    bc1, bc2 = st.columns(2)
    with bc1:
        st.markdown("##### Chi theo danh mục")
        chi_df = fdf[fdf["transaction_type"] == "Chi"]
        if not chi_df.empty:
            st.bar_chart(chi_df.groupby("category")["amount"].sum().sort_values(ascending=False), color="#ef4444")
        else:
            st.info("Không có khoản chi")
    with bc2:
        st.markdown("##### Thu theo danh mục")
        thu_df = fdf[fdf["transaction_type"] == "Thu"]
        if not thu_df.empty:
            st.bar_chart(thu_df.groupby("category")["amount"].sum().sort_values(ascending=False), color="#22c55e")
        else:
            st.info("Không có khoản thu")
    
    # Xu hướng
    st.divider()
    st.markdown("##### 📊 Xu hướng Thu - Chi")
    if m_sel == "Tất cả":
        trend_df = fdf.pivot_table(index="month", columns="transaction_type", values="amount", aggfunc="sum", fill_value=0)
        st.line_chart(trend_df, height=300)
    else:
        fdf["ngày"] = fdf["created_at"].dt.strftime("%d")
        day_trend = fdf.pivot_table(index="ngày", columns="transaction_type", values="amount", aggfunc="sum", fill_value=0)
        st.line_chart(day_trend, height=300)
    
    # Danh sách
    st.divider()
    view_type = st.radio("Xem theo", ["Thẻ", "Bảng"], horizontal=True)
    if view_type == "Thẻ":
        show_transaction_cards(fdf)
    else:
        disp = fdf[["date", "transaction_type", "category", "description", "amount"]].copy()
        disp.columns = ["Ngày", "Loại", "Danh mục", "Mô tả", "Số tiền"]
        st.dataframe(disp, use_container_width=True, hide_index=True,
                     column_config={"Số tiền": st.column_config.NumberColumn(format="%.0f đ")})
    
    # Tải về
    csv_dl = fdf[["created_at", "transaction_type", "category", "description", "amount"]].copy()
    csv_dl["created_at"] = csv_dl["created_at"].dt.strftime("%d/%m/%Y %H:%M")
    csv_dl.columns = ["Thời gian", "Loại", "Danh mục", "Mô tả", "Số tiền"]
    st.download_button("📥 Tải danh sách (.csv)", data=csv_dl.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"giao_dich_{m_sel}.csv", use_container_width=True)
    
    edit_section(fdf)

# =========================================================
# TRANG NGÂN SÁCH
# =========================================================
def page_budget():
    st.subheader("🎯 Quản lý Ngân sách")
    thang = month_selector("Chọn tháng", "budget_m")
    
    ok, data = api_call("GET", "/budgets", params={"month": thang})
    if not ok:
        st.error(data)
        return
    items = data.get("items", []) if isinstance(data, dict) else []
    
    if items:
        st.markdown("#### 📋 Tình hình ngân sách")
        over_items = [i for i in items if i["level"] == "over"]
        warn_items = [i for i in items if i["level"] == "warning"]
        
        if over_items:
            st.error("🔴 Đã vượt ngân sách: " + ", ".join(i["label"] for i in over_items))
        if warn_items:
            st.warning("🟠 Sắp hết ngân sách: " + ", ".join(i["label"] for i in warn_items))
        if not over_items and not warn_items:
            st.success("🟢 Tất cả đều trong ngân sách! Tiếp tục phát huy 💪")
        
        for it in items:
            pct = safe_float(it["percent"])
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{LEVEL_ICON[it['level']]} {it['label']}**")
                st.progress(min(pct, 100) / 100)
            with col2:
                st.markdown(f"<div style='text-align:right; font-size:0.85rem; color:#64748b;'>"
                            f"{fmt_money_full(it['spent'])}<br>trong {fmt_money_full(it['monthly_limit'])}</div>",
                            unsafe_allow_html=True)
            con = safe_float(it["remaining"])
            if con >= 0:
                st.caption(f"✅ Còn lại: {fmt_money_full(con)}")
            else:
                st.caption(f"❌ Vượt: {fmt_money_full(-con)}")
    else:
        st.info("Bạn chưa đặt ngân sách nào. Hãy đặt hạn mức bên dưới 👇")
    
    st.divider()
    st.markdown("#### ➕ Đặt / Sửa ngân sách")
    with st.form("budget_form"):
        c1, c2 = st.columns(2)
        d_muc = c1.selectbox("Danh mục", [TOTAL_LABEL] + EXPENSE_CATEGORIES)
        han_muc = c2.number_input("Hạn mức/tháng (đồng)", min_value=0.0, step=100000.0)
        sub_b = st.form_submit_button("💾 Lưu ngân sách")
    if sub_b:
        if han_muc <= 0:
            st.warning("Hạn mức phải > 0")
        else:
            ok, _ = api_call("PUT", "/budgets", json={"category": d_muc, "monthly_limit": han_muc})
            if ok:
                notify_success(f"Đã lưu «{d_muc}»: {fmt_money_full(han_muc)}/tháng")
                st.rerun()
            else:
                st.error("Lỗi khi lưu!")
    
    if items:
        with st.expander("🗑️ Xóa ngân sách"):
            opts_del = {i["id"]: f"{i['label']} — {fmt_money_full(i['monthly_limit'])}" for i in items}
            sel_del = st.selectbox("Chọn để xóa", list(opts_del), format_func=opts_del.get)
            if st.button("🗑️ Xóa", type="secondary"):
                ok, _ = api_call("DELETE", f"/budgets/{sel_del}")
                if ok:
                    notify_success("Đã xóa!")
                    st.rerun()

# =========================================================
# TRANG BÁO CÁO
# =========================================================
def page_report():
    st.subheader("📑 Báo cáo tổng hợp")
    st.caption("Xuất đầy đủ số liệu, biểu đồ và danh sách giao dịch ra file")
    
    thang_r = month_selector("📅 Chọn tháng báo cáo", "rep_m")
    
    ok, tx = load_transactions()
    if ok and tx:
        df = build_dataframe([t for t in tx if isinstance(t, dict)])
        if not df.empty:
            mf = df[df["month"] == thang_r]
            thu_r = mf[mf["transaction_type"] == "Thu"]["amount"].sum()
            chi_r = mf[mf["transaction_type"] == "Chi"]["amount"].sum()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("💵 Tổng thu", fmt_money_full(thu_r))
            c2.metric("💸 Tổng chi", fmt_money_full(chi_r))
            c3.metric("💰 Số dư", fmt_money_full(thu_r - chi_r))
            c4.metric("🧾 Giao dịch", len(mf))
    
    st.divider()
    col_xl, col_pdf = st.columns(2)
    with col_xl:
        if st.button("📗 Tạo báo cáo Excel", use_container_width=True):
            with st.spinner("Đang tạo file Excel..."):
                ok, content = api_call("GET", "/reports/monthly", params={"month": thang_r, "format": "xlsx"}, 
                                       raw=True, timeout=120)
            if ok:
                st.session_state["rep_xlsx"] = (thang_r, content)
                notify_success("Đã tạo báo cáo Excel!")
            else:
                st.error(f"Lỗi: {content}")
        if saved := st.session_state.get("rep_xlsx"):
            m_saved, c_saved = saved
            if m_saved == thang_r:
                st.download_button("📥 Tải báo cáo Excel", data=c_saved, 
                                   file_name=f"bao_cao_{thang_r}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)
    
    with col_pdf:
        if st.button("📕 Tạo báo cáo PDF", use_container_width=True):
            with st.spinner("Đang tạo file PDF..."):
                ok, content = api_call("GET", "/reports/monthly", params={"month": thang_r, "format": "pdf"}, 
                                       raw=True, timeout=120)
            if ok:
                st.session_state["rep_pdf"] = (thang_r, content)
                notify_success("Đã tạo báo cáo PDF!")
            else:
                st.error(f"Lỗi: {content}")
        if saved := st.session_state.get("rep_pdf"):
            m_saved, c_saved = saved
            if m_saved == thang_r:
                st.download_button("📥 Tải báo cáo PDF", data=c_saved, 
                                   file_name=f"bao_cao_{thang_r}.pdf",
                                   mime="application/pdf",
                                   use_container_width=True)

# =========================================================
# THANH ĐIỀU HƯỚNG CHÍNH
# =========================================================
def main_app():
    with st.sidebar:
        st.title("💰 Thu Chi AI Pro")
        st.success(f"👤 {st.session_state.username}")
        st.divider()
        
        if check_backend():
            st.success("🟢 Hệ thống trực tuyến")
        else:
            st.error("🔴 Máy chủ chưa kết nối")
            st.markdown(f"<div class='sidebar-notice'>{COLD_START_HINT}</div>", unsafe_allow_html=True)
        
        st.divider()
        st.markdown("### 🧭 Điều hướng nhanh")
        nav_pages = {
            "🤖 Nhập giao dịch": page_ai,
            "📷 Quét hóa đơn": page_bill,
            "📊 Lịch sử & Thống kê": page_history,
            "🎯 Ngân sách": page_budget,
            "📑 Báo cáo": page_report,
            "📖 Giới thiệu": page_intro,
        }
        sel = st.radio("", list(nav_pages), label_visibility="collapsed", key="page")
        st.divider()
        if st.button("🚪 Đăng xuất", use_container_width=True):
            logout("Đã đăng xuất. Hẹn gặp lại!")
            st.rerun()
        st.caption("🔒 Dữ liệu được bảo mật")
    
    st.title(f"💰 {sel}")
    show_notice()
    st.divider()
    nav_pages[sel]()

# CHẠY ỨNG DỤNG
restore_session()
if is_logged_in():
    main_app()
else:
    auth_page()
