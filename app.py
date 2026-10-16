import os
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

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "username" not in st.session_state:
    st.session_state.username = ""


# =========================================================
# API ERROR
# =========================================================

def get_error(response):

    try:

        data = response.json()

        error = data.get(
            "detail",
            "Có lỗi xảy ra"
        )

        if isinstance(error, list):

            return "; ".join(
                str(x) for x in error
            )

        return str(error)

    except Exception:

        return response.text or "Có lỗi xảy ra"


# =========================================================
# LOGIN
# =========================================================

def login(username, password):

    try:

        response = requests.post(
            BACKEND_URL + "/login",
            json={
                "username": username,
                "password": password
            },
            timeout=60
        )

        if response.status_code != 200:

            return False, get_error(response)

        data = response.json()

        st.session_state.logged_in = True
        st.session_state.user_id = data["user_id"]
        st.session_state.username = data["username"]

        return True, "Đăng nhập thành công"

    except Exception as e:

        return False, str(e)


# =========================================================
# REGISTER
# =========================================================

def register(username, password):

    try:

        response = requests.post(
            BACKEND_URL + "/register",
            json={
                "username": username,
                "password": password
            },
            timeout=60
        )

        if response.status_code != 200:

            return False, get_error(response)

        return True, "Đăng ký thành công"

    except Exception as e:

        return False, str(e)


# =========================================================
# AI TRANSACTION
# =========================================================

def add_transaction_ai(text):

    try:

        response = requests.post(
            BACKEND_URL + "/add-transaction-ai",
            json={
                "user_id": st.session_state.user_id,
                "text": text
            },
            timeout=180
        )

        if response.status_code != 200:

            return False, get_error(response)

        return True, response.json()

    except Exception as e:

        return False, str(e)


# =========================================================
# GET TRANSACTIONS
# =========================================================

def get_transactions():

    try:

        response = requests.get(
            BACKEND_URL
            + f"/transactions/{st.session_state.user_id}",
            timeout=60
        )

        if response.status_code != 200:

            return False, get_error(response)

        return True, response.json()

    except Exception as e:

        return False, str(e)


# =========================================================
# SCAN BILL
# =========================================================

def scan_bill(uploaded_file):

    try:

        file_bytes = uploaded_file.getvalue()

        files = {
            "file": (
                uploaded_file.name,
                file_bytes,
                uploaded_file.type or "image/jpeg"
            )
        }

        response = requests.post(
            BACKEND_URL + "/scan-bill",
            params={
                "user_id": st.session_state.user_id
            },
            files=files,
            timeout=180
        )

        if response.status_code != 200:

            return False, get_error(response)

        return True, response.json()

    except Exception as e:

        return False, str(e)


# =========================================================
# LOGIN PAGE
# =========================================================

if not st.session_state.logged_in:

    st.title("💰 Thu Chi AI Pro")

    tab1, tab2 = st.tabs(
        ["🔐 Đăng nhập", "📝 Đăng ký"]
    )

    # -----------------------------------------------------
    # LOGIN
    # -----------------------------------------------------

    with tab1:

        st.subheader("Đăng nhập")

        username = st.text_input(
            "Tên đăng nhập",
            key="login_username"
        )

        password = st.text_input(
            "Mật khẩu",
            type="password",
            key="login_password"
        )

        if st.button(
            "🔐 Đăng nhập",
            use_container_width=True
        ):

            if not username or not password:

                st.warning(
                    "Vui lòng nhập đầy đủ thông tin"
                )

            else:

                success, message = login(
                    username,
                    password
                )

                if success:

                    st.success(message)
                    st.rerun()

                else:

                    st.error(
                        "❌ " + message
                    )

    # -----------------------------------------------------
    # REGISTER
    # -----------------------------------------------------

    with tab2:

        st.subheader("Đăng ký tài khoản")

        new_username = st.text_input(
            "Tên đăng nhập",
            key="register_username"
        )

        new_password = st.text_input(
            "Mật khẩu",
            type="password",
            key="register_password"
        )

        confirm_password = st.text_input(
            "Nhập lại mật khẩu",
            type="password",
            key="confirm_password"
        )

        if st.button(
            "📝 Đăng ký",
            use_container_width=True
        ):

            if not new_username or not new_password:

                st.warning(
                    "Vui lòng nhập đầy đủ thông tin"
                )

            elif new_password != confirm_password:

                st.error(
                    "❌ Mật khẩu nhập lại không đúng"
                )

            else:

                success, message = register(
                    new_username,
                    new_password
                )

                if success:

                    st.success(
                        "✅ " + message
                    )

                else:

                    st.error(
                        "❌ " + message
                    )

    st.stop()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title("💰 Thu Chi AI")

    st.write(
        f"👤 Xin chào **{st.session_state.username}**"
    )

    st.divider()

    if st.button(
        "🚪 Đăng xuất",
        use_container_width=True
    ):

        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = ""

        st.rerun()


# =========================================================
# MAIN
# =========================================================

st.title("💰 Thu Chi AI Pro")

st.caption(
    "Quản lý thu chi bằng trí tuệ nhân tạo"
)


tab1, tab2, tab3 = st.tabs(
    [
        "🤖 Nhập giao dịch AI",
        "📷 Quét hóa đơn",
        "📊 Lịch sử giao dịch"
    ]
)


# =========================================================
# TAB 1 - AI
# =========================================================

with tab1:

    st.subheader(
        "🤖 Nhập giao dịch bằng ngôn ngữ tự nhiên"
    )

    st.info(
        "Ví dụ: Ăn cơm 40k"
    )

    text = st.text_input(
        "Nhập giao dịch",
        placeholder="Ví dụ: mua cơm 40k"
    )

    if st.button(
        "✨ Phân tích & lưu giao dịch",
        use_container_width=True
    ):

        if not text.strip():

            st.warning(
                "Vui lòng nhập nội dung giao dịch"
            )

        else:

            with st.spinner(
                "🤖 AI đang phân tích..."
            ):

                success, result = add_transaction_ai(
                    text
                )

            if success:

                st.success(
                    "✅ Đã thêm giao dịch thành công!"
                )

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.metric(
                        "Số tiền",
                        f"{result['amount']:,.0f} đ"
                    )

                with col2:

                    st.write("**Loại:**")
                    st.write(
                        result["transaction_type"]
                    )

                with col3:

                    st.write("**Danh mục:**")
                    st.write(
                        result["category"]
                    )

                st.write(
                    "**Mô tả:**",
                    result["description"]
                )

            else:

                st.error(
                    "❌ Lỗi xử lý giao dịch AI: "
                    + str(result)
                )


# =========================================================
# TAB 2 - SCAN BILL
# =========================================================

with tab2:

    st.subheader(
        "📷 Quét hóa đơn bằng AI"
    )

    uploaded_file = st.file_uploader(
        "Chọn ảnh hóa đơn",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp"
        ]
    )

    if uploaded_file:

        st.image(
            uploaded_file,
            caption="Ảnh hóa đơn",
            use_container_width=True
        )

        if st.button(
            "🔍 Quét hóa đơn",
            use_container_width=True
        ):

            with st.spinner(
                "🤖 AI đang đọc hóa đơn..."
            ):

                success, result = scan_bill(
                    uploaded_file
                )

            if success:

                st.success(
                    "✅ Đã quét và lưu hóa đơn!"
                )

                st.write(
                    "**Số tiền:** "
                    + f"{result['amount']:,.0f} đ"
                )

                st.write(
                    "**Mô tả:** "
                    + result["description"]
                )

                st.write(
                    "**Danh mục:** "
                    + result["category"]
                )

            else:

                st.error(
                    "❌ Lỗi xử lý ảnh: "
                    + str(result)
                )


# =========================================================
# TAB 3 - HISTORY
# =========================================================

with tab3:

    st.subheader(
        "📊 Lịch sử giao dịch"
    )

    if st.button(
        "🔄 Tải lại",
        use_container_width=True
    ):

        st.rerun()

    success, transactions = get_transactions()

    if not success:

        st.error(
            "❌ " + str(transactions)
        )

    elif not transactions:

        st.info(
            "Chưa có giao dịch nào."
        )

    else:

        total_income = 0
        total_expense = 0

        for item in transactions:

            amount = float(
                item["amount"]
            )

            if item["transaction_type"] == "income":

                total_income += amount

            else:

                total_expense += amount

        balance = (
            total_income
            - total_expense
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "💵 Tổng thu",
                f"{total_income:,.0f} đ"
            )

        with col2:

            st.metric(
                "💸 Tổng chi",
                f"{total_expense:,.0f} đ"
            )

        with col3:

            st.metric(
                "💰 Số dư",
                f"{balance:,.0f} đ"
            )

        st.divider()

        for item in transactions:

            if item["transaction_type"] == "income":

                icon = "🟢"
                sign = "+"

            else:

                icon = "🔴"
                sign = "-"

            st.markdown(
                f"""
                ### {icon} {item['description']}

                **Số tiền:** {sign}{item['amount']:,.0f} đ

                **Danh mục:** {item['category']}

                **Thời gian:** {item['created_at']}
                """
            )

            st.divider()
