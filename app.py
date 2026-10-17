"""Thu Chi AI Pro - Frontend (Streamlit)."""

import os

import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Thu Chi AI Pro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CONFIG
# =========================================================

def get_config(name, default=""):
    """Ưu tiên biến môi trường, sau đó tới Streamlit secrets."""
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
TIMEZONE = get_config("APP_TIMEZONE", "Asia/Ho_Chi_Minh")

CATEGORIES = [
    "Ăn uống", "Di chuyển", "Mua sắm", "Hóa đơn & Tiện ích", "Nhà ở",
    "Giải trí", "Sức khỏe", "Giáo dục", "Lương", "Thưởng", "Đầu tư", "Khác",
]
COLD_START_HINT = "Server miễn phí có thể mất 30–60 giây để khởi động nếu lâu không dùng."


# =========================================================
# STYLE
# =========================================================

st.markdown(
    """
<style>
.stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #f1f5f9 100%); color: #1e293b; }
[data-testid="stForm"] {
    background: rgba(255,255,255,0.85) !important; backdrop-filter: blur(12px);
    border: 1px solid rgba(226,232,240,0.8) !important; border-radius: 16px !important;
    padding: 24px 28px !important; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.05) !important;
}
.stTabs [data-baseweb="tab-list"] { gap: 8px; background: rgba(226,232,240,0.6); padding: 6px; border-radius: 12px; }
.stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 8px 16px; color: #64748b; font-weight: 500; }
.stTabs [aria-selected="true"] { background-color: #3b82f6 !important; color: #fff !important; }
.stButton > button, [data-testid="stFormSubmitButton"] > button {
    width: 100%; border-radius: 10px !important; font-weight: 600 !important;
    background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%) !important;
    color: #fff !important; border: none !important; transition: all .25s ease !important;
}
.stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {
    transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(59,130,246,.3);
}
label { color: #334155 !important; font-weight: 500; }
</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# SESSION
# =========================================================

for key, default in (("token", None), ("user_id", None), ("username", "")):
    st.session_state.setdefault(key, default)


def is_logged_in():
    return bool(st.session_state.token)


def start_session(result):
    st.session_state.token = result["token"]
    st.session_state.user_id = result.get("user_id")
    st.session_state.username = result.get("username", "")
    st.session_state.pop("tx", None)


def logout(notice=None):
    for key in ("token", "user_id", "tx", "page"):
        st.session_state.pop(key, None)
    st.session_state.username = ""
    if notice:
        st.session_state["notice"] = notice


def notify(message):
    """Lưu thông báo để hiển thị sau khi st.rerun()."""
    st.session_state["notice"] = message


# =========================================================
# API
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
        return response.text or "Có lỗi xảy ra"


def api_call(method, path, timeout=60, timeout_msg="Backend phản hồi quá lâu.", **kwargs):
    """Gọi backend. Trả về (thành_công, dữ_liệu_hoặc_thông_báo_lỗi)."""
    headers = kwargs.pop("headers", {})
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = http().request(method, BACKEND_URL + path, headers=headers, timeout=timeout, **kwargs)
    except requests.exceptions.Timeout:
        return False, timeout_msg
    except requests.exceptions.ConnectionError:
        return False, "Không kết nối được tới Backend. " + COLD_START_HINT
    except requests.exceptions.RequestException as e:
        return False, str(e)

    if response.status_code == 401 and token:  # token hết hạn / không hợp lệ
        logout("⏰ Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại.")
        st.rerun()

    if not response.ok:
        return False, get_error(response)
    try:
        return True, response.json()
    except ValueError:
        return False, "Backend trả về dữ liệu không hợp lệ."


@st.cache_data(ttl=30, show_spinner=False)
def check_backend():
    try:
        return requests.get(BACKEND_URL + "/", timeout=5).status_code == 200
    except requests.exceptions.RequestException:
        return False


def load_transactions(force=False):
    """Giữ danh sách giao dịch trong session; chỉ gọi API khi cần (lần đầu / sau khi thay đổi / bấm tải lại)."""
    if force or "tx" not in st.session_state:
        ok, data = api_call("GET", "/transactions", params={"limit": 1000})
        if not ok:
            return False, data
        if not isinstance(data, list):
            return False, "Backend trả về dữ liệu giao dịch không hợp lệ."
        st.session_state.tx = data
    return True, st.session_state.tx


def invalidate_transactions():
    st.session_state.pop("tx", None)


# =========================================================
# FORMAT HELPERS
# =========================================================

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt_money(value):
    return f"{safe_float(value):,.0f}".replace(",", ".") + " đ"


def show_dataframe(df, **kwargs):
    """Tương thích cả Streamlit cũ (use_container_width) lẫn mới (width='stretch')."""
    try:
        st.dataframe(df, width="stretch", **kwargs)
    except Exception:
        st.dataframe(df, use_container_width=True, **kwargs)


def show_result(result, amount_label="💰 Số tiền"):
    c1, c2, c3 = st.columns(3)
    c1.metric(amount_label, fmt_money(result.get("amount")))
    c2.metric("📈 Loại" if result.get("transaction_type") == "Thu" else "📉 Loại", result.get("transaction_type", "Chi"))
    c3.metric("📁 Danh mục", result.get("category", "Khác"))
    st.write("**Mô tả:**", result.get("description", ""))


# =========================================================
# AUTH PAGE
# =========================================================

def auth_page():
    _, center, _ = st.columns([0.5, 3, 0.5])
    with center:
        st.markdown(
            """
            <div style="text-align:center; margin: 15px 0;">
                <h1 style="font-size:2.2rem; margin-bottom:0; color:#1e293b;">💰 Thu Chi AI Pro</h1>
                <p style="color:#64748b; font-size:0.95rem;">Quản lý tài chính cá nhân thông minh bằng trí tuệ nhân tạo</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if notice := st.session_state.pop("notice", None):
            st.warning(notice)

        login_tab, register_tab, readme_tab = st.tabs(["🔐 Đăng nhập", "📝 Đăng ký", "📖 Giới thiệu"])

        with login_tab:
            with st.form("login_form"):
                username = st.text_input("Tên đăng nhập", placeholder="Nhập tên đăng nhập")
                password = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu")
                submitted = st.form_submit_button("🔐 Đăng nhập")

            if submitted:
                if not username.strip() or not password:
                    st.warning("Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.")
                else:
                    with st.spinner("Đang xác thực... " + COLD_START_HINT):
                        ok, result = api_call(
                            "POST", "/login", timeout=90,
                            json={"username": username.strip(), "password": password},
                        )
                    if ok and result.get("token"):
                        start_session(result)
                        st.rerun()
                    else:
                        st.error("❌ " + (str(result) if not ok else "Backend không trả về token."))

        with register_tab:
            with st.form("register_form"):
                new_username = st.text_input("Tên đăng nhập", placeholder="Ít nhất 3 ký tự")
                new_password = st.text_input("Mật khẩu", type="password", placeholder="Ít nhất 6 ký tự")
                confirm = st.text_input("Nhập lại mật khẩu", type="password", placeholder="Xác nhận mật khẩu")
                submitted = st.form_submit_button("📝 Đăng ký tài khoản")

            if submitted:
                name = new_username.strip()
                if len(name) < 3:
                    st.warning("Tên đăng nhập phải có ít nhất 3 ký tự.")
                elif len(new_password) < 6:
                    st.warning("Mật khẩu phải có ít nhất 6 ký tự.")
                elif new_password != confirm:
                    st.error("❌ Hai mật khẩu không giống nhau.")
                else:
                    with st.spinner("Đang tạo tài khoản... " + COLD_START_HINT):
                        ok, result = api_call(
                            "POST", "/register", timeout=90,
                            json={"username": name, "password": new_password},
                        )
                    if ok and result.get("token"):
                        start_session(result)  # đăng ký xong vào luôn
                        notify("🎉 Đăng ký thành công! Chào mừng bạn.")
                        st.rerun()
                    else:
                        st.error("❌ " + (str(result) if not ok else "Backend không trả về token."))

        with readme_tab:
            st.markdown("### 📚 Tài liệu giới thiệu sản phẩm")
            try:
                with open("README.md", "r", encoding="utf-8") as f:
                    st.markdown(f.read())
            except FileNotFoundError:
                st.info("Chưa tìm thấy file `README.md` trong thư mục dự án.")
            except OSError as e:
                st.error(f"Không thể đọc README.md: {e}")


# =========================================================
# PAGE: AI + MANUAL INPUT
# =========================================================

def page_ai():
    st.subheader("🤖 Nhập giao dịch bằng AI")
    st.info("Ví dụ: ăn cơm 40k, nhận lương 20 triệu, đổ xăng 2tr5")

    with st.form("ai_form", clear_on_submit=True):
        text = st.text_input("Nội dung giao dịch", placeholder="Ví dụ: mua cơm 40k", max_chars=500)
        submitted = st.form_submit_button("✨ Phân tích và lưu")

    if submitted:
        if not text.strip():
            st.warning("Vui lòng nhập nội dung giao dịch.")
        else:
            with st.spinner("🤖 AI đang phân tích..."):
                ok, result = api_call(
                    "POST", "/add-transaction-ai", timeout=120,
                    timeout_msg="AI xử lý quá lâu. Vui lòng thử lại.",
                    json={"text": text.strip()},
                )
            if ok:
                invalidate_transactions()
                st.success("✅ Đã thêm giao dịch thành công!")
                show_result(result)
            else:
                st.error("❌ " + str(result))

    with st.expander("✍️ Nhập thủ công (không dùng AI)"):
        with st.form("manual_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            m_type = c1.selectbox("Loại", ["Chi", "Thu"])
            m_amount = c2.number_input("Số tiền (VND)", min_value=0.0, value=0.0, step=1000.0)
            c3, c4 = st.columns(2)
            m_cat = c3.selectbox("Danh mục", CATEGORIES, index=CATEGORIES.index("Khác"))
            m_desc = c4.text_input("Mô tả", max_chars=500)
            manual_submitted = st.form_submit_button("💾 Lưu giao dịch")

        if manual_submitted:
            if m_amount <= 0:
                st.warning("Số tiền phải lớn hơn 0.")
            else:
                ok, result = api_call(
                    "POST", "/transactions",
                    json={"amount": m_amount, "transaction_type": m_type,
                          "category": m_cat, "description": m_desc.strip()},
                )
                if ok:
                    invalidate_transactions()
                    st.success("✅ Đã lưu giao dịch!")
                    show_result(result)
                else:
                    st.error("❌ " + str(result))


# =========================================================
# PAGE: SCAN BILL
# =========================================================

def page_bill():
    st.subheader("📷 Quét hóa đơn bằng AI")
    uploaded = st.file_uploader("Chọn ảnh hóa đơn", type=["jpg", "jpeg", "png", "webp"])
    if not uploaded:
        return

    st.image(uploaded, caption="Hóa đơn", width=400)
    if st.button("🔍 Quét và lưu hóa đơn"):
        data = uploaded.getvalue()
        if not data:
            st.error("❌ File ảnh rỗng.")
            return
        with st.spinner("🤖 AI đang đọc hóa đơn..."):
            ok, result = api_call(
                "POST", "/scan-bill", timeout=120,
                timeout_msg="Quét hóa đơn quá lâu.",
                files={"file": (uploaded.name, data, uploaded.type or "image/jpeg")},
            )
        if ok:
            invalidate_transactions()
            st.success("✅ Đã quét và lưu hóa đơn!")
            show_result(result, "💰 Tổng tiền")
        else:
            st.error("❌ " + str(result))


# =========================================================
# PAGE: HISTORY & STATS
# =========================================================

def build_dataframe(rows):
    df = pd.DataFrame(rows)
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True).dt.tz_convert(TIMEZONE)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["category"] = df["category"].fillna("Khác")
    df["description"] = df["description"].fillna("")
    df["month"] = df["created_at"].dt.strftime("%Y-%m")
    return df


def edit_section(fdf):
    with st.expander("✏️ Sửa / Xóa giao dịch"):
        labels = {
            r.id: f"{r.created_at:%d/%m/%Y %H:%M} · {r.description or '(không mô tả)'} · {fmt_money(r.amount)}"
            for r in fdf.itertuples()
        }
        selected = st.selectbox("Chọn giao dịch", list(labels), format_func=labels.get)
        item = fdf[fdf["id"] == selected].iloc[0]
        tid = int(selected)

        current_cat = str(item["category"])
        cat_options = list(dict.fromkeys(CATEGORIES + [current_cat]))

        with st.form(f"edit_form_{tid}"):
            desc = st.text_input("Mô tả", value=str(item["description"]), key=f"desc_{tid}")
            amount = st.number_input("Số tiền (VND)", min_value=1.0, value=max(float(item["amount"]), 1.0),
                                     step=1000.0, key=f"amount_{tid}")
            c1, c2 = st.columns(2)
            ttype = c1.selectbox("Loại", ["Chi", "Thu"], index=0 if item["transaction_type"] == "Chi" else 1,
                                 key=f"type_{tid}")
            cat = c2.selectbox("Danh mục", cat_options, index=cat_options.index(current_cat), key=f"cat_{tid}")
            confirm_delete = st.checkbox("Tôi chắc chắn muốn xóa giao dịch này", key=f"confirm_{tid}")
            c_save, c_del = st.columns(2)
            save = c_save.form_submit_button("💾 Lưu thay đổi")
            delete = c_del.form_submit_button("🗑️ Xóa giao dịch")

        if save:
            ok, res = api_call("PUT", f"/transactions/{tid}", json={
                "amount": amount, "transaction_type": ttype, "category": cat, "description": desc.strip(),
            })
            if ok:
                invalidate_transactions()
                notify("✅ Cập nhật giao dịch thành công!")
                st.rerun()
            else:
                st.error("❌ " + str(res))

        if delete:
            if not confirm_delete:
                st.warning("Hãy tick ô xác nhận trước khi xóa.")
            else:
                ok, res = api_call("DELETE", f"/transactions/{tid}")
                if ok:
                    invalidate_transactions()
                    notify("🗑️ Đã xóa giao dịch!")
                    st.rerun()
                else:
                    st.error("❌ " + str(res))


def page_history():
    st.subheader("📊 Lịch sử giao dịch & Thống kê")

    ok, transactions = load_transactions(force=st.button("🔄 Tải lại dữ liệu"))
    if not ok:
        st.error("❌ " + str(transactions))
        return

    rows = [t for t in transactions if isinstance(t, dict)]
    if not rows:
        st.info("Chưa có giao dịch nào.")
        return

    df = build_dataframe(rows)

    # ---- Bộ lọc ----
    f1, f2, f3, f4 = st.columns([1, 1, 1.5, 1.5])
    months = sorted(df["month"].unique(), reverse=True)
    month = f1.selectbox("📅 Tháng", ["Tất cả"] + months,
                         format_func=lambda m: m if m == "Tất cả" else f"{m[5:]}/{m[:4]}")
    ttype = f2.selectbox("Loại", ["Tất cả", "Thu", "Chi"])
    cats = f3.multiselect("Danh mục", sorted(df["category"].unique()))
    keyword = f4.text_input("🔎 Tìm theo mô tả")

    fdf = df
    if month != "Tất cả":
        fdf = fdf[fdf["month"] == month]
    if ttype != "Tất cả":
        fdf = fdf[fdf["transaction_type"] == ttype]
    if cats:
        fdf = fdf[fdf["category"].isin(cats)]
    if keyword.strip():
        fdf = fdf[fdf["description"].str.contains(keyword.strip(), case=False, na=False, regex=False)]

    if fdf.empty:
        st.info("Không có giao dịch nào khớp bộ lọc.")
        return

    # ---- Tổng quan ----
    income = fdf.loc[fdf["transaction_type"] == "Thu", "amount"].sum()
    expense = fdf.loc[fdf["transaction_type"] == "Chi", "amount"].sum()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💵 Tổng thu", fmt_money(income))
    m2.metric("💸 Tổng chi", fmt_money(expense))
    m3.metric("💰 Số dư", fmt_money(income - expense))
    m4.metric("🧾 Số giao dịch", f"{len(fdf)}")

    st.divider()

    # ---- Biểu đồ ----
    left, right = st.columns(2)
    with left:
        st.markdown("##### 📊 Chi tiêu theo danh mục")
        exp = fdf[fdf["transaction_type"] == "Chi"]
        if exp.empty:
            st.info("Không có khoản chi trong bộ lọc này.")
        else:
            st.bar_chart(exp.groupby("category")["amount"].sum().sort_values(ascending=False))
    with right:
        if month == "Tất cả":
            st.markdown("##### 📈 Thu / Chi theo tháng")
            index_col = "month"
        else:
            st.markdown("##### 📈 Thu / Chi theo ngày")
            index_col = "day"
            fdf = fdf.assign(day=fdf["created_at"].dt.strftime("%d"))
        trend = fdf.pivot_table(index=index_col, columns="transaction_type", values="amount",
                                aggfunc="sum", fill_value=0)
        st.bar_chart(trend)

    st.divider()

    # ---- Bảng chi tiết ----
    st.markdown("##### 📝 Chi tiết giao dịch")
    view = fdf[["created_at", "transaction_type", "category", "description", "amount"]].rename(columns={
        "created_at": "Thời gian", "transaction_type": "Loại", "category": "Danh mục",
        "description": "Mô tả", "amount": "Số tiền",
    })
    show_dataframe(
        view, hide_index=True,
        column_config={
            "Thời gian": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
            "Số tiền": st.column_config.NumberColumn(format="%.0f đ"),
        },
    )
    st.download_button(
        "⬇️ Tải CSV",
        data=view.assign(**{"Thời gian": view["Thời gian"].dt.strftime("%Y-%m-%d %H:%M")})
                 .to_csv(index=False).encode("utf-8-sig"),
        file_name="giao_dich.csv",
        mime="text/csv",
    )

    edit_section(fdf)


# =========================================================
# MAIN
# =========================================================

def main_app():
    with st.sidebar:
        st.title("💰 Thu Chi AI Pro")
        st.write(f"👤 **{st.session_state.username}**")
        st.divider()
        if check_backend():
            st.success("🟢 Backend Online")
        else:
            st.error("🔴 Backend Offline")
        st.divider()
        if st.button("🚪 Đăng xuất"):
            logout()
            st.rerun()

    st.title("💰 Thu Chi AI Pro")
    st.write(f"Xin chào **{st.session_state.username}** 👋")

    if notice := st.session_state.pop("notice", None):
        st.success(notice)

    pages = {
        "🤖 Nhập giao dịch": page_ai,
        "📷 Quét hóa đơn": page_bill,
        "📊 Lịch sử & Thống kê": page_history,
    }
    # Dùng radio thay cho st.tabs: chỉ chạy code của trang đang chọn (tabs chạy cả 3 trang mỗi lần rerun).
    choice = st.radio("Điều hướng", list(pages), horizontal=True,
                      label_visibility="collapsed", key="page")
    st.divider()
    pages[choice]()


if is_logged_in():
    main_app()
else:
    auth_page()
