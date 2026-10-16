import os
from datetime import datetime

import requests
import streamlit as st


# =========================================================
# CONFIG
# =========================================================

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "https://thu-chi-ai.onrender.com"
).rstrip("/")

st.set_page_config(
    page_title="Thu Chi AI Pro",
    page_icon="💰",
    layout="wide"
)


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
    try:
        response = requests.request(
            method,
            BACKEND_URL + path,
            timeout=timeout,
            **kwargs
        )

        if response.status_code != 200:
            return False, get_error(response)

        return True, response.json()

    except requests.exceptions.Timeout:
        return False, timeout_msg

    except requests.exceptions.ConnectionError:
        return False, "Không kết nối được Backend."

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
    # Render free có thể "ngủ" nên cho timeout dài hơn
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
    ok, data = api_call(
        "GET", f"/transactions/{st.session_state.user_id}"
    )

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
# LOGIN / REGISTER PAGE
# =========================================================

if not st.session_state.logged_in:

    st.title("💰 Thu Chi AI Pro")
    st.write("Quản lý thu chi thông minh bằng AI")
    st.divider()

    login_tab, register_tab = st.tabs(["🔐 Đăng nhập", "📝 Đăng ký"])

    # ---------------- LOGIN ----------------
    with login_tab:

        st.subheader("🔐 Đăng nhập")

        with st.form("login_form"):

            username = st.text_input("Tên đăng nhập")
            password = st.text_input("Mật khẩu", type="password")

            submitted = st.form_submit_button(
                "🔐 Đăng nhập",
                use_container_width=True
            )

        if submitted:

            if not username.strip():
                st.warning("Vui lòng nhập tên đăng nhập.")

            elif not password:
                st.warning("Vui lòng nhập mật khẩu.")

            else:
                with st.spinner("Đang đăng nhập (lần đầu có thể mất ~30 giây)..."):
                    success, result = login_user(username.strip(), password)

                if success:
                    user_id = result.get("user_id")

                    if not user_id:
                        st.error("Backend không trả về user_id.")
                    else:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user_id
                        st.session_state.username = result.get(
                            "username", username.strip()
                        )
                        st.rerun()
                else:
                    st.error("❌ " + str(result))

    # ---------------- REGISTER ----------------
    with register_tab:

        st.subheader("📝 Đăng ký tài khoản")

        with st.form("register_form"):

            new_username = st.text_input("Tên đăng nhập")
            new_password = st.text_input("Mật khẩu", type="password")
            confirm_password = st.text_input("Nhập lại mật khẩu", type="password")

            submitted = st.form_submit_button(
                "📝 Đăng ký",
                use_container_width=True
            )

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
                    st.success("✅ Đăng ký thành công!")
                    st.info(
                        "Bạn hãy chuyển sang tab Đăng nhập "
                        "và đăng nhập bằng tài khoản vừa tạo."
                    )
                else:
                    st.error("❌ " + str(result))

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
# MAIN
# =========================================================

st.title("💰 Thu Chi AI Pro")
st.write(f"Xin chào **{st.session_state.username}** 👋")
st.caption("Quản lý thu chi bằng trí tuệ nhân tạo")

tab_ai, tab_bill, tab_history = st.tabs(
    [
        "🤖 Nhập giao dịch AI",
        "📷 Quét hóa đơn",
        "📊 Lịch sử giao dịch"
    ]
)


# =========================================================
# TAB: AI TRANSACTION
# =========================================================

with tab_ai:

    st.subheader("🤖 Nhập giao dịch bằng AI")
    st.info("Ví dụ: ăn cơm 40k, nhận lương 20 triệu, đổ xăng 2tr5")

    with st.form("ai_form", clear_on_submit=True):

        transaction_text = st.text_input(
            "Nội dung giao dịch",
            placeholder="Ví dụ: mua cơm 40k"
        )

        submitted = st.form_submit_button(
            "✨ Phân tích và lưu",
            use_container_width=True
        )

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
# TAB: BILL
# =========================================================

with tab_bill:

    st.subheader("📷 Quét hóa đơn bằng AI")

    uploaded_file = st.file_uploader(
        "Chọn ảnh hóa đơn",
        type=["jpg", "jpeg", "png", "webp"]
    )

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
# TAB: HISTORY
# =========================================================

with tab_history:

    st.subheader("📊 Lịch sử giao dịch")

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
            total_income = sum(
                safe_float(t.get("amount"))
                for t in valid_transactions
                if t.get("transaction_type") == "Thu"
            )
            total_expense = sum(
                safe_float(t.get("amount"))
                for t in valid_transactions
                if t.get("transaction_type") != "Thu"
            )

            col1, col2, col3 = st.columns(3)
            col1.metric("💵 Tổng thu", f"{total_income:,.0f} đ")
            col2.metric("💸 Tổng chi", f"{total_expense:,.0f} đ")
            col3.metric("💰 Số dư", f"{total_income - total_expense:,.0f} đ")

            st.divider()

            for item in valid_transactions:

                amount = safe_float(item.get("amount"))
                is_income = item.get("transaction_type") == "Thu"

                icon = "🟢" if is_income else "🔴"
                type_text = "THU" if is_income else "CHI"
                sign = "+" if is_income else "-"

                with st.container():

                    left, right = st.columns([3, 1])

                    with left:
                        st.markdown(
                            f"### {icon} {item.get('description') or 'Không có mô tả'}"
                        )
                        st.write(f"**Danh mục:** {item.get('category') or 'Khác'}")
                        st.caption(
                            f"{type_text} • {format_date(item.get('created_at'))}"
                        )

                    with right:
                        st.markdown(f"### {sign}{amount:,.0f} đ")

                    st.divider()
