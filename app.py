import os
from datetime import datetime
import pandas as pd
import requests
import streamlit as st


# =========================================================
# CONFIG & CLEAN BACKEND URL
# =========================================================

raw_backend_url = os.getenv("BACKEND_URL", "https://thu-chi-ai.onrender.com")

# Ép buộc tự động bổ sung https:// nếu chưa có và làm sạch URL
raw_backend_url = raw_backend_url.strip().strip('"').strip("'")
if not raw_backend_url.startswith("http://") and not raw_backend_url.startswith("https://"):
    raw_backend_url = "https://" + raw_backend_url

BACKEND_URL = raw_backend_url.rstrip("/")

st.set_page_config(
    page_title="Thu Chi AI Pro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CUSTOM CSS (GIAO DIỆN SÁNG SỦA, HIỆN ĐẠI, THU GỌN)
# =========================================================

CUSTOM_CSS = """
<style>
/* Background toàn trang phong cách Sáng sủa, Tươi mới */
.stApp {
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #f1f5f9 100%);
    color: #1e293b;
}

/* Card Đăng nhập / Đăng ký căn giữa, màu sáng, hiệu ứng kính mờ tinh tế */
[data-testid="stForm"] {
    background: rgba(255, 255, 255, 0.85) !important;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(226, 232, 240, 0.8) !important;
    border-radius: 16px !important;
    padding: 24px 28px !important;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05) !important;
}

/* Căn chỉnh lại Tab Đăng nhập / Đăng ký / Giới thiệu */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: rgba(226, 232, 240, 0.6);
    padding: 6px;
    border-radius: 12px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 16px;
    color: #64748b;
    font-weight: 500;
}

.stTabs [aria-selected="true"] {
    background-color: #3b82f6 !important;
    color: #ffffff !important;
}

/* Nút bấm sáng sủa, nổi bật */
.stButton > button {
    border-radius: 10px !important;
    background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    border: none !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.3);
}

/* Tinh chỉnh nhãn chữ trong form cho dễ nhìn trên nền sáng */
label {
    color: #334155 !important;
    font-weight: 500;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =========================================================
# SESSION
# =========================================================

st.session_state.setdefault("logged_in", False)
st.session_state.setdefault("user_id", None)
st.session_state.setdefault("username", "")


# =========================================================
# HELPERS
# =========================================================

def get_error(response):
    try:
        data = response.json()
        detail = data.get("detail", "Có lỗi xảy ra")
        if isinstance(detail, list):
            return "; ".join(
                item.get("msg", str(item)) if isinstance(item, dict) else str(item)
                for item in detail
            )
        return str(detail)
    except Exception:
        return response.text or "Có lỗi xảy ra"


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def format_date(value):
    if not value:
        return ""
    try:
        return datetime.fromisoformat(str(value)).strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return str(value)


def api_call(method, path, timeout=60, timeout_msg="Backend phản hồi quá lâu.", **kwargs):
    """Gọi backend, trả về (thành_công, dữ_liệu_hoặc_lỗi)."""
    full_url = BACKEND_URL + path
    try:
        response = requests.request(
            method,
            full_url,
            timeout=timeout,
            **kwargs
        )

        if response.status_code != 200:
            return False, get_error(response)

        return True, response.json()

    except requests.exceptions.Timeout:
        return False, timeout_msg

    except requests.exceptions.ConnectionError:
        return False, f"Không kết nối được tới Backend ({full_url})."

    except Exception as e:
        return False, str(e)


@st.cache_data(ttl=30, show_spinner=False)
def check_backend():
    try:
        return requests.get(BACKEND_URL + "/", timeout=5).status_code == 200
    except Exception:
        return False


def register_user(username, password):
    return api_call(
        "POST", "/register",
        json={"username": username, "password": password}
    )


def login_user(username, password):
    return api_call(
        "POST", "/login",
        timeout=90,
        json={"username": username, "password": password}
    )


def add_transaction_ai(text):
    return api_call(
        "POST", "/add-transaction-ai",
        timeout=180,
        timeout_msg="AI xử lý quá lâu. Vui lòng thử lại.",
        json={"user_id": st.session_state.user_id, "text": text}
    )


def get_transactions():
    ok, data = api_call("GET", f"/transactions/{st.session_state.user_id}")
    if ok and not isinstance(data, list):
        return False, "Backend trả về dữ liệu giao dịch không hợp lệ."
    return ok, data


def scan_bill(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    if not file_bytes:
        return False, "File ảnh rỗng."

    return api_call(
        "POST", "/scan-bill",
        timeout=180,
        timeout_msg="Quét hóa đơn quá lâu.",
        params={"user_id": st.session_state.user_id},
        files={
            "file": (
                uploaded_file.name,
                file_bytes,
                uploaded_file.type or "image/jpeg"
            )
        }
    )


def show_result(result, title_amount="💰 Số tiền"):
    amount = safe_float(result.get("amount"))
    col1, col2, col3 = st.columns(3)
    col1.metric(title_amount, f"{amount:,.0f} đ")
    col2.metric(
        "📈 Loại" if result.get("transaction_type") == "Thu" else "📉 Loại",
        result.get("transaction_type", "Chi")
    )
    col3.metric("📁 Danh mục", result.get("category", "Khác"))
    st.write("**Mô tả:**", result.get("description", ""))


# =========================================================
# LOGIN / REGISTER / README PAGE (CĂN GIỮA - SÁNG SỦA)
# =========================================================

if not st.session_state.logged_in:

    # Mở rộng bố cục một chút ở màn hình chào mừng để hiển thị README thoải mái hơn
    col_left, col_center, col_right = st.columns([0.5, 3, 0.5])

    with col_center:
        st.markdown(
            """
            <div style="text-align: center; margin-top: 15px; margin-bottom: 15px;">
                <h1 style="font-size: 2.2rem; margin-bottom: 0px; color: #1e293b;">💰 Thu Chi AI Pro</h1>
                <p style="color: #64748b; font-size: 0.95rem;">Quản lý tài chính cá nhân thông minh bằng trí tuệ nhân tạo</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        login_tab, register_tab, readme_tab = st.tabs(["🔐 Đăng nhập", "📝 Đăng ký", "📖 Giới thiệu (README)"])

        # ---------------- LOGIN ----------------
        with login_tab:
            with st.form("login_form"):
                username = st.text_input("Tên đăng nhập", placeholder="Nhập tên đăng nhập")
                password = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu")
                submitted = st.form_submit_button("🔐 Đăng nhập", use_container_width=True)

            if submitted:
                if not username.strip():
                    st.warning("Vui lòng nhập tên đăng nhập.")
                elif not password:
                    st.warning("Vui lòng nhập mật khẩu.")
                else:
                    with st.spinner("Đang xác thực..."):
                        success, result = login_user(username.strip(), password)

                    if success:
                        user_id = result.get("user_id")
                        if not user_id:
                            st.error("Backend không trả về user_id.")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.user_id = user_id
                            st.session_state.username = result.get("username", username.strip())
                            st.rerun()
                    else:
                        st.error("❌ " + str(result))

        # ---------------- REGISTER ----------------
        with register_tab:
            with st.form("register_form"):
                new_username = st.text_input("Tên đăng nhập", placeholder="Ít nhất 3 ký tự")
                new_password = st.text_input("Mật khẩu", type="password", placeholder="Ít nhất 4 ký tự")
                confirm_password = st.text_input("Nhập lại mật khẩu", type="password", placeholder="Xác nhận mật khẩu")
                submitted = st.form_submit_button("📝 Đăng ký tài khoản", use_container_width=True)

            if submitted:
                username_clean = new_username.strip()
                if not username_clean:
                    st.warning("Vui lòng nhập tên đăng nhập.")
                elif len(username_clean) < 3:
                    st.warning("Tên đăng nhập phải có ít nhất 3 ký tự.")
                elif not new_password.strip():
                    st.warning("Vui lòng nhập mật khẩu.")
                elif len(new_password.strip()) < 4:
                    st.warning("Mật khẩu phải có ít nhất 4 ký tự.")
                elif new_password != confirm_password:
                    st.error("❌ Hai mật khẩu không giống nhau.")
                else:
                    with st.spinner("Đang tạo tài khoản..."):
                        success, result = register_user(username_clean, new_password)

                    if success:
                        st.success("✅ Đăng ký thành công! Bạn hãy chuyển sang tab Đăng nhập.")
                    else:
                        st.error("❌ " + str(result))

        # ---------------- README / GIỚI THIỆU ----------------
        with readme_tab:
            st.markdown("### 📚 Tài liệu giới thiệu sản phẩm")
            if os.path.exists("README.md"):
                try:
                    with open("README.md", "r", encoding="utf-8") as f:
                        readme_content = f.read()
                    # Hiển thị nội dung README dưới dạng Markdown trực quan
                    st.markdown(readme_content)
                except Exception as e:
                    st.error(f"Không thể đọc file README.md: {e}")
            else:
                st.info("Hiện tại chưa tìm thấy file `README.md` trong thư mục dự án. Hãy đảm bảo bạn đã tạo file này.")

    st.stop()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.title("💰 Thu Chi AI Pro")
    st.write(f"👤 **{st.session_state.username}**")
    st.divider()

    if check_backend():
        st.success("🟢 Backend Online")
    else:
        st.error("🔴 Backend Offline")

    st.divider()

    if st.button("🚪 Đăng xuất", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = ""
        st.rerun()


# =========================================================
# MAIN APP
# =========================================================

st.title("💰 Thu Chi AI Pro")
st.write(f"Xin chào **{st.session_state.username}** 👋")

tab_ai, tab_bill, tab_history = st.tabs([
    "🤖 Nhập giao dịch AI",
    "📷 Quét hóa đơn",
    "📊 Lịch sử & Thống kê"
])


# =========================================================
# TAB: AI TRANSACTION
# =========================================================

with tab_ai:
    st.subheader("🤖 Nhập giao dịch bằng AI")
    st.info("Ví dụ: ăn cơm 40k, nhận lương 20 triệu, đổ xăng 2tr5")

    with st.form("ai_form", clear_on_submit=True):
        transaction_text = st.text_input("Nội dung giao dịch", placeholder="Ví dụ: mua cơm 40k")
        submitted = st.form_submit_button("✨ Phân tích và lưu", use_container_width=True)

    if submitted:
        if not transaction_text.strip():
            st.warning("Vui lòng nhập nội dung giao dịch.")
        else:
            with st.spinner("🤖 AI đang phân tích..."):
                success, result = add_transaction_ai(transaction_text.strip())

            if success:
                st.success("✅ Đã thêm giao dịch thành công!")
                show_result(result)
            else:
                st.error("❌ " + str(result))


# =========================================================
# TAB: SCAN BILL
# =========================================================

with tab_bill:
    st.subheader("📷 Quét hóa đơn bằng AI")

    uploaded_file = st.file_uploader("Chọn ảnh hóa đơn", type=["jpg", "jpeg", "png", "webp"])

    if uploaded_file:
        st.image(uploaded_file, caption="Hóa đơn", width=400)

        if st.button("🔍 Quét và lưu hóa đơn", use_container_width=True):
            with st.spinner("🤖 AI đang đọc hóa đơn..."):
                success, result = scan_bill(uploaded_file)

            if success:
                st.success("✅ Đã quét và lưu hóa đơn!")
                show_result(result, "💰 Tổng tiền")
            else:
                st.error("❌ " + str(result))


# =========================================================
# TAB: HISTORY, FILTER, STATS & EDIT/DELETE
# =========================================================

with tab_history:
    st.subheader("📊 Lịch sử giao dịch & Thống kê")

    if st.button("🔄 Tải lại dữ liệu", use_container_width=True):
        st.rerun()

    success, transactions = get_transactions()

    if not success:
        st.error("❌ " + str(transactions))

    else:
        valid_transactions = [t for t in transactions if isinstance(t, dict)]

        if not valid_transactions:
            st.info("Chưa có giao dịch nào.")

        else:
            df = pd.DataFrame(valid_transactions)
            df["created_at_dt"] = pd.to_datetime(df["created_at"])
            df["amount"] = df["amount"].astype(float)

            # Lọc theo tháng/năm
            df["month_year"] = df["created_at_dt"].dt.strftime("%m/%Y")
            all_months = sorted(df["month_year"].unique(), reverse=True)

            selected_month = st.selectbox("📅 Lọc theo tháng", ["Tất cả"] + all_months)

            if selected_month != "Tất cả":
                df_filtered = df[df["month_year"] == selected_month]
            else:
                df_filtered = df

            # Tính tổng số dư / thu / chi
            total_income = df_filtered[df_filtered["transaction_type"] == "Thu"]["amount"].sum()
            total_expense = df_filtered[df_filtered["transaction_type"] != "Thu"]["amount"].sum()

            col1, col2, col3 = st.columns(3)
            col1.metric("💵 Tổng thu", f"{total_income:,.0f} đ")
            col2.metric("💸 Tổng chi", f"{total_expense:,.0f} đ")
            col3.metric("💰 Số dư", f"{total_income - total_expense:,.0f} đ")

            st.divider()

            # Biểu đồ cột (Bar Chart) chi tiêu theo danh mục
            st.markdown("### 📊 Biểu đồ cột chi tiêu theo danh mục")
            df_expense = df_filtered[df_filtered["transaction_type"] == "Chi"]
            if not df_expense.empty:
                cat_grouped = df_expense.groupby("category")["amount"].sum()
                st.bar_chart(cat_grouped)
            else:
                st.info("Không có dữ liệu chi tiêu trong kỳ này để hiển thị biểu đồ.")

            st.divider()

            # Danh sách giao dịch cho phép Sửa & Xóa
            st.markdown("### 📝 Chi tiết giao dịch (Bấm vào để Sửa / Xóa)")

            for _, item in df_filtered.iterrows():
                t_id = int(item["id"])
                is_income = item["transaction_type"] == "Thu"
                icon = "🟢" if is_income else "🔴"
                sign = "+" if is_income else "-"

                header_text = (
                    f"{icon} {item['description']} | {sign}{item['amount']:,.0f} đ "
                    f"({format_date(item['created_at'])})"
                )

                with st.expander(header_text):
                    with st.form(f"edit_form_{t_id}"):
                        edit_desc = st.text_input("Mô tả", value=str(item.get("description") or ""))
                        edit_amount = st.number_input("Số tiền (VND)", value=float(item.get("amount") or 0.0), step=1000.0)
                        edit_type = st.selectbox(
                            "Loại giao dịch",
                            ["Chi", "Thu"],
                            index=0 if item.get("transaction_type") == "Chi" else 1
                        )
                        edit_cat = st.text_input("Danh mục", value=str(item.get("category") or "Khác"))

                        col_save, col_del = st.columns(2)
                        save_btn = col_save.form_submit_button("💾 Lưu thay đổi", use_container_width=True)
                        del_btn = col_del.form_submit_button("🗑️ Xóa giao dịch", use_container_width=True)

                        if save_btn:
                            ok, res = api_call(
                                "PUT", f"/transactions/{t_id}",
                                json={
                                    "user_id": st.session_state.user_id,
                                    "amount": edit_amount,
                                    "transaction_type": edit_type,
                                    "category": edit_cat,
                                    "description": edit_desc
                                }
                            )
                            if ok:
                                st.success("Cập nhật giao dịch thành công!")
                                st.rerun()
                            else:
                                st.error("❌ " + str(res))

                        if del_btn:
                            ok, res = api_call(
                                "DELETE", f"/transactions/{t_id}",
                                params={"user_id": st.session_state.user_id}
                            )
                            if ok:
                                st.success("Đã xóa giao dịch!")
                                st.rerun()
                            else:
                                st.error("❌ " + str(res))
