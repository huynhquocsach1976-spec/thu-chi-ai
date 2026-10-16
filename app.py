```python
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
# ERROR
# =========================================================

def get_error(response):

    try:

        data = response.json()

        detail = data.get(
            "detail",
            "Có lỗi xảy ra"
        )

        if isinstance(detail, list):

            messages = []

            for item in detail:

                if isinstance(item, dict):

                    messages.append(
                        item.get(
                            "msg",
                            str(item)
                        )
                    )

                else:

                    messages.append(
                        str(item)
                    )

            return "; ".join(messages)

        return str(detail)

    except Exception:

        if response.text:
            return response.text

        return "Có lỗi xảy ra"


# =========================================================
# BACKEND CHECK
# =========================================================

def check_backend():

    try:

        response = requests.get(
            BACKEND_URL + "/",
            timeout=30
        )

        return response.status_code == 200

    except Exception:

        return False


# =========================================================
# REGISTER
# =========================================================

def register_user(
    username,
    password
):

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

            return False, get_error(
                response
            )

        return True, response.json()

    except requests.exceptions.Timeout:

        return False, (
            "Backend phản hồi quá lâu."
        )

    except requests.exceptions.ConnectionError:

        return False, (
            "Không kết nối được Backend."
        )

    except Exception as e:

        return False, str(e)


# =========================================================
# LOGIN
# =========================================================

def login_user(
    username,
    password
):

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

            return False, get_error(
                response
            )

        data = response.json()

        return True, data

    except requests.exceptions.Timeout:

        return False, (
            "Backend phản hồi quá lâu."
        )

    except requests.exceptions.ConnectionError:

        return False, (
            "Không kết nối được Backend."
        )

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

            return False, get_error(
                response
            )

        return True, response.json()

    except requests.exceptions.Timeout:

        return False, (
            "AI xử lý quá lâu. Vui lòng thử lại."
        )

    except requests.exceptions.ConnectionError:

        return False, (
            "Không kết nối được Backend."
        )

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

            return False, get_error(
                response
            )

        data = response.json()

        if not isinstance(data, list):

            return False, (
                "Backend trả về dữ liệu "
                "giao dịch không hợp lệ."
            )

        return True, data

    except requests.exceptions.Timeout:

        return False, (
            "Backend phản hồi quá lâu."
        )

    except requests.exceptions.ConnectionError:

        return False, (
            "Không kết nối được Backend."
        )

    except Exception as e:

        return False, str(e)


# =========================================================
# SCAN BILL
# =========================================================

def scan_bill(uploaded_file):

    try:

        file_bytes = uploaded_file.getvalue()

        if not file_bytes:

            return False, (
                "File ảnh rỗng."
            )

        files = {
            "file": (
                uploaded_file.name,
                file_bytes,
                uploaded_file.type
                or "image/jpeg"
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

            return False, get_error(
                response
            )

        return True, response.json()

    except requests.exceptions.Timeout:

        return False, (
            "Quét hóa đơn quá lâu."
        )

    except requests.exceptions.ConnectionError:

        return False, (
            "Không kết nối được Backend."
        )

    except Exception as e:

        return False, str(e)


# =========================================================
# LOGIN / REGISTER PAGE
# =========================================================

if not st.session_state.logged_in:

    st.title("💰 Thu Chi AI Pro")

    st.write(
        "Quản lý thu chi thông minh bằng AI"
    )

    st.divider()

    login_tab, register_tab = st.tabs(
        [
            "🔐 Đăng nhập",
            "📝 Đăng ký"
        ]
    )

    # =====================================================
    # LOGIN
    # =====================================================

    with login_tab:

        st.subheader(
            "🔐 Đăng nhập"
        )

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

            if not username.strip():

                st.warning(
                    "Vui lòng nhập tên đăng nhập."
                )

            elif not password:

                st.warning(
                    "Vui lòng nhập mật khẩu."
                )

            else:

                with st.spinner(
                    "Đang đăng nhập..."
                ):

                    success, result = login_user(
                        username.strip(),
                        password
                    )

                if success:

                    # Backend mới trả:
                    # user_id
                    # username

                    user_id = result.get(
                        "user_id"
                    )

                    logged_username = result.get(
                        "username",
                        username.strip()
                    )

                    if not user_id:

                        st.error(
                            "Backend không trả về user_id."
                        )

                    else:

                        st.session_state.logged_in = True

                        st.session_state.user_id = (
                            user_id
                        )

                        st.session_state.username = (
                            logged_username
                        )

                        st.success(
                            "✅ Đăng nhập thành công!"
                        )

                        st.rerun()

                else:

                    st.error(
                        "❌ " + str(result)
                    )

    # =====================================================
    # REGISTER
    # =====================================================

    with register_tab:

        st.subheader(
            "📝 Đăng ký tài khoản"
        )

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
            key="register_confirm_password"
        )

        if st.button(
            "📝 Đăng ký",
            use_container_width=True
        ):

            username_clean = (
                new_username.strip()
            )

            if not username_clean:

                st.warning(
                    "Vui lòng nhập tên đăng nhập."
                )

            elif len(username_clean) < 3:

                st.warning(
                    "Tên đăng nhập phải có ít nhất 3 ký tự."
                )

            elif not new_password:

                st.warning(
                    "Vui lòng nhập mật khẩu."
                )

            elif len(new_password) < 4:

                st.warning(
                    "Mật khẩu phải có ít nhất 4 ký tự."
                )

            elif new_password != confirm_password:

                st.error(
                    "❌ Hai mật khẩu không giống nhau."
                )

            else:

                with st.spinner(
                    "Đang tạo tài khoản..."
                ):

                    success, result = register_user(
                        username_clean,
                        new_password
                    )

                if success:

                    st.success(
                        "✅ Đăng ký thành công!"
                    )

                    st.info(
                        "Anh chuyển sang tab Đăng nhập "
                        "và đăng nhập bằng tài khoản vừa tạo."
                    )

                else:

                    st.error(
                        "❌ " + str(result)
                    )

    st.stop()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title(
        "💰 Thu Chi AI Pro"
    )

    st.write(
        f"👤 **{st.session_state.username}**"
    )

    st.divider()

    if check_backend():

        st.success(
            "🟢 Backend Online"
        )

    else:

        st.error(
            "🔴 Backend Offline"
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

st.title(
    "💰 Thu Chi AI Pro"
)

st.write(
    f"Xin chào **{st.session_state.username}** 👋"
)

st.caption(
    "Quản lý thu chi bằng trí tuệ nhân tạo"
)


# =========================================================
# TABS
# =========================================================

tab_ai, tab_bill, tab_history = st.tabs(
    [
        "🤖 Nhập giao dịch AI",
        "📷 Quét hóa đơn",
        "📊 Lịch sử giao dịch"
    ]
)


# =========================================================
# AI TRANSACTION
# =========================================================

with tab_ai:

    st.subheader(
        "🤖 Nhập giao dịch bằng AI"
    )

    st.info(
        "Ví dụ: ăn cơm 40k"
    )

    transaction_text = st.text_input(
        "Nội dung giao dịch",
        placeholder="Ví dụ: mua cơm 40k"
    )

    if st.button(
        "✨ Phân tích và lưu",
        use_container_width=True
    ):

        if not transaction_text.strip():

            st.warning(
                "Vui lòng nhập nội dung giao dịch."
            )

        else:

            with st.spinner(
                "🤖 AI đang phân tích..."
            ):

                success, result = (
                    add_transaction_ai(
                        transaction_text.strip()
                    )
                )

            if success:

                st.success(
                    "✅ Đã thêm giao dịch thành công!"
                )

                amount = float(
                    result.get(
                        "amount",
                        0
                    )
                )

                transaction_type = result.get(
                    "transaction_type",
                    "Chi"
                )

                category = result.get(
                    "category",
                    "Khác"
                )

                description = result.get(
                    "description",
                    transaction_text
                )

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.metric(
                        "💰 Số tiền",
                        f"{amount:,.0f} đ"
                    )

                with col2:

                    if transaction_type == "Thu":

                        st.metric(
                            "📈 Loại",
                            "Thu"
                        )

                    else:

                        st.metric(
                            "📉 Loại",
                            "Chi"
                        )

                with col3:

                    st.metric(
                        "📁 Danh mục",
                        category
                    )

                st.write(
                    "**Mô tả:**",
                    description
                )

            else:

                st.error(
                    "❌ " + str(result)
                )


# =========================================================
# BILL
# =========================================================

with tab_bill:

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
            caption="Hóa đơn",
            use_container_width=True
        )

        if st.button(
            "🔍 Quét và lưu hóa đơn",
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

                amount = float(
                    result.get(
                        "amount",
                        0
                    )
                )

                st.metric(
                    "💰 Tổng tiền",
                    f"{amount:,.0f} đ"
                )

                st.write(
                    "**Loại:**",
                    result.get(
                        "transaction_type",
                        "Chi"
                    )
                )

                st.write(
                    "**Danh mục:**",
                    result.get(
                        "category",
                        "Khác"
                    )
                )

                st.write(
                    "**Mô tả:**",
                    result.get(
                        "description",
                        ""
                    )
                )

            else:

                st.error(
                    "❌ " + str(result)
                )


# =========================================================
# HISTORY
# =========================================================

with tab_history:

    st.subheader(
        "📊 Lịch sử giao dịch"
    )

    if st.button(
        "🔄 Tải lại dữ liệu",
        use_container_width=True
    ):

        st.rerun()

    success, transactions = (
        get_transactions()
    )

    if not success:

        st.error(
            "❌ " + str(transactions)
        )

    elif not isinstance(
        transactions,
        list
    ):

        st.error(
            "❌ Dữ liệu giao dịch không hợp lệ."
        )

    elif len(transactions) == 0:

        st.info(
            "Chưa có giao dịch nào."
        )

    else:

        total_income = 0
        total_expense = 0

        valid_transactions = []

        for item in transactions:

            if not isinstance(
                item,
                dict
            ):
                continue

            valid_transactions.append(
                item
            )

            amount = float(
                item.get(
                    "amount",
                    0
                )
            )

            transaction_type = item.get(
                "transaction_type",
                "Chi"
            )

            if transaction_type == "Thu":

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

        for item in valid_transactions:

            amount = float(
                item.get(
                    "amount",
                    0
                )
            )

            transaction_type = item.get(
                "transaction_type",
                "Chi"
            )

            description = item.get(
                "description",
                "Không có mô tả"
            )

            category = item.get(
                "category",
                "Khác"
            )

            created_at = item.get(
                "created_at",
                ""
            )

            if transaction_type == "Thu":

                icon = "🟢"
                type_text = "THU"
                sign = "+"

            else:

                icon = "🔴"
                type_text = "CHI"
                sign = "-"

            with st.container():

                col1, col2 = st.columns(
                    [3, 1]
                )

                with col1:

                    st.markdown(
                        f"### {icon} {description}"
                    )

                    st.write(
                        f"**Danh mục:** {category}"
                    )

                    st.caption(
                        f"{type_text} • {created_at}"
                    )

                with col2:

                    st.markdown(
                        f"### {sign}{amount:,.0f} đ"
                    )

                st.divider()
```
