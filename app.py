import os
from datetime import datetime
import pandas as pd
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "[https://thu-chi-ai.onrender.com](https://thu-chi-ai.onrender.com)").rstrip("/")

st.set_page_config(page_title="Thu Chi AI Pro", page_icon="💰", layout="wide")

st.session_state.setdefault("logged_in", False)
st.session_state.setdefault("user_id", None)
st.session_state.setdefault("username", "")


def get_error(response):
    try:
        data = response.json()
        detail = data.get("detail", "Có lỗi xảy ra")
        if isinstance(detail, list):
            return "; ".join(item.get("msg", str(item)) if isinstance(item, dict) else str(item) for item in detail)
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


def api_call(method, path, timeout=60, **kwargs):
    try:
        response = requests.request(method, BACKEND_URL + path, timeout=timeout, **kwargs)
        if response.status_code != 200:
            return False, get_error(response)
        return True, response.json()
    except requests.exceptions.Timeout:
        return False, "Backend phản hồi quá lâu."
    except requests.exceptions.ConnectionError:
        return False, "Không kết nối được Backend."
    except Exception as e:
        return False, str(e)


# =========================================================
# LOGIN / REGISTER UI
# =========================================================

if not st.session_state.logged_in:
    st.title("💰 Thu Chi AI Pro")
    st.write("Quản lý thu chi thông minh bằng AI")
    st.divider()

    login_tab, register_tab = st.tabs(["🔐 Đăng nhập", "📝 Đăng ký"])

    with login_tab:
        st.subheader("🔐 Đăng nhập")
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập")
            password = st.text_input("Mật khẩu", type="password")
            submitted = st.form_submit_button("🔐 Đăng nhập", use_container_width=True)

        if submitted:
            success, result = api_call("POST", "/login", json={"username": username.strip(), "password": password})
            if success:
                st.session_state.logged_in = True
                st.session_state.user_id = result.get("user_id")
                st.session_state.username = result.get("username", username)
                st.rerun()
            else:
                st.error("❌ " + str(result))

    with register_tab:
        st.subheader("📝 Đăng ký tài khoản")
        with st.form("register_form"):
            new_username = st.text_input("Tên đăng nhập")
            new_password = st.text_input("Mật khẩu", type="password")
            confirm_password = st.text_input("Nhập lại mật khẩu", type="password")
            submitted = st.form_submit_button("📝 Đăng ký", use_container_width=True)

        if submitted:
            if new_password != confirm_password:
                st.error("❌ Mật khẩu không khớp.")
            else:
                success, result = api_call("POST", "/register", json={"username": new_username.strip(), "password": new_password})
                if success:
                    st.success("✅ Đăng ký thành công! Hãy sang tab Đăng nhập.")
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
    if st.button("🚪 Đăng xuất", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = ""
        st.rerun()


# =========================================================
# MAIN APP
# =========================================================

st.title("💰 Thu Chi AI Pro")
tab_ai, tab_bill, tab_history = st.tabs(["🤖 Nhập giao dịch AI", "📷 Quét hóa đơn", "📊 Lịch sử giao dịch"])

with tab_ai:
    st.subheader("🤖 Nhập giao dịch bằng AI")
    with st.form("ai_form", clear_on_submit=True):
        text = st.text_input("Nội dung giao dịch", placeholder="Ví dụ: ăn cơm 40k, lương 20 triệu")
        submitted = st.form_submit_button("✨ Phân tích và lưu", use_container_width=True)

    if submitted and text.strip():
        with st.spinner("🤖 AI đang xử lý..."):
            success, result = api_call("POST", "/add-transaction-ai", json={"user_id": st.session_state.user_id, "text": text})
        if success:
            st.success("✅ Đã thêm giao dịch thành công!")
            st.json(result)
        else:
            st.error("❌ " + str(result))

with tab_bill:
    st.subheader("📷 Quét hóa đơn bằng AI")
    uploaded_file = st.file_uploader("Chọn ảnh hóa đơn", type=["jpg", "jpeg", "png", "webp"])
    if uploaded_file and st.button("🔍 Quét và lưu", use_container_width=True):
        with st.spinner("🤖 Đang đọc hóa đơn..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            success, result = api_call("POST", "/scan-bill", params={"user_id": st.session_state.user_id}, files=files)
        if success:
            st.success("✅ Đã quét và lưu hóa đơn!")
            st.json(result)
        else:
            st.error("❌ " + str(result))

with tab_history:
    st.subheader("📊 Lịch sử giao dịch & Thống kê")
    
    success, transactions = api_call("GET", f"/transactions/{st.session_state.user_id}")
    if not success:
        st.error("❌ Không thể tải lịch sử: " + str(transactions))
    elif not transactions:
        st.info("Chưa có giao dịch nào.")
    else:
        df = pd.DataFrame(transactions)
        df["created_at_dt"] = pd.to_datetime(df["created_at"])
        df["amount"] = df["amount"].astype(float)

        # Bộ lọc theo tháng/năm
        df["month_year"] = df["created_at_dt"].dt.strftime("%m/%Y")
        all_months = sorted(df["month_year"].unique(), reverse=True)
        
        selected_month = st.selectbox("📅 Lọc theo tháng", ["Tất cả"] + all_months)
        if selected_month != "Tất cả":
            df_filtered = df[df["month_year"] == selected_month]
        else:
            df_filtered = df

        # Thống kê tổng quan
        total_income = df_filtered[df_filtered["transaction_type"] == "Thu"]["amount"].sum()
        total_expense = df_filtered[df_filtered["transaction_type"] == "Chi"]["amount"].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("💵 Tổng thu", f"{total_income:,.0f} đ")
        col2.metric("💸 Tổng chi", f"{total_expense:,.0f} đ")
        col3.metric("💰 Số dư", f"{total_income - total_expense:,.0f} đ")

        st.divider()

        # Biểu đồ chi tiêu theo danh mục
        st.markdown("### 📈 Biểu đồ chi tiêu theo danh mục")
        df_expense = df_filtered[df_filtered["transaction_type"] == "Chi"]
        if not df_expense.empty:
            cat_grouped = df_expense.groupby("category")["amount"].sum()
            st.bar_chart(cat_grouped)
        else:
            st.info("Chưa có khoản chi tiêu nào trong khoảng thời gian này để vẽ biểu đồ.")

        st.divider()
        st.markdown("### 📝 Danh sách giao dịch (Sửa / Xóa)")

        for _, item in df_filtered.iterrows():
            t_id = int(item["id"])
            is_income = item["transaction_type"] == "Thu"
            icon = "🟢" if is_income else "🔴"
            
            with st.expander(f"{icon} [{item['transaction_type']}] {item['description']} - {item['amount']:,.0f} đ ({format_date(item['created_at'])})"):
                with st.form(f"edit_form_{t_id}"):
                    new_desc = st.text_input("Mô tả", value=item["description"])
                    new_amount = st.number_input("Số tiền", value=float(item["amount"]), step=1000.0)
                    new_type = st.selectbox("Loại", ["Chi", "Thu"], index=0 if item["transaction_type"] == "Chi" else 1)
                    new_cat = st.text_input("Danh mục", value=item["category"])

                    col_save, col_del = st.columns(2)
                    save_btn = col_save.form_submit_button("💾 Lưu thay đổi", use_container_width=True)
                    del_btn = col_del.form_submit_button("🗑️ Xóa giao dịch", use_container_width=True)

                    if save_btn:
                        ok, res = api_call(
                            "PUT", f"/transactions/{t_id}",
                            json={
                                "user_id": st.session_state.user_id,
                                "amount": new_amount,
                                "transaction_type": new_type,
                                "category": new_cat,
                                "description": new_desc
                            }
                        )
                        if ok:
                            st.success("Cập nhật thành công!")
                            st.rerun()
                        else:
                            st.error(res)

                    if del_btn:
                        ok, res = api_call("DELETE", f"/transactions/{t_id}", params={"user_id": st.session_state.user_id})
                        if ok:
                            st.success("Đã xóa giao dịch!")
                            st.rerun()
                        else:
                            st.error(res)
