```python
import os
import base64
import requests
import pandas as pd
import streamlit as st

# ============================================================
# CẤU HÌNH
# ============================================================

st.set_page_config(
    page_title="Thu Chi AI Pro",
    page_icon="💰",
    layout="wide"
)

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "https://thu-chi-ai.onrender.com"
).rstrip("/")


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>
.main {
    padding-top: 1rem;
}

.title {
    font-size: 38px;
    font-weight: bold;
    color: #1565C0;
}

.subtitle {
    color: #666;
    font-size: 17px;
}

.success-box {
    padding: 15px;
    border-radius: 10px;
    background-color: #E8F5E9;
    border: 1px solid #4CAF50;
}

.error-box {
    padding: 15px;
    border-radius: 10px;
    background-color: #FFEBEE;
    border: 1px solid #F44336;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "username" not in st.session_state:
    st.session_state.username = ""

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"


# ============================================================
# API POST
# ============================================================

def api_post(endpoint, data, timeout=30):

    url = f"{BACKEND_URL}{endpoint}"

    try:
        response = requests.post(
            url,
            json=data,
            timeout=timeout
        )

        try:
            result = response.json()
        except Exception:
            result = {
                "detail": response.text
            }

        if response.status_code >= 400:
            return None, result.get(
                "detail",
                f"HTTP {response.status_code}"
            )

        return result, None

    except requests.exceptions.Timeout:
        return None, "Backend phản hồi quá lâu."

    except requests.exceptions.ConnectionError:
        return None, (
            "Không thể kết nối Backend: "
            + BACKEND_URL
        )

    except Exception as e:
        return None, str(e)


# ============================================================
# API GET
# ============================================================

def api_get(endpoint, timeout=30):

    url = f"{BACKEND_URL}{endpoint}"

    try:
        response = requests.get(
            url,
            timeout=timeout
        )

        try:
            result = response.json()
        except Exception:
            result = {
                "detail": response.text
            }

        if response.status_code >= 400:
            return None, result.get(
                "detail",
                f"HTTP {response.status_code}"
            )

        return result, None

    except requests.exceptions.Timeout:
        return None, "Backend phản hồi quá lâu."

    except requests.exceptions.ConnectionError:
        return None, (
            "Không thể kết nối Backend: "
            + BACKEND_URL
        )

    except Exception as e:
        return None, str(e)


# ============================================================
# KIỂM TRA BACKEND
# ============================================================

def check_backend():

    try:

        response = requests.get(
            f"{BACKEND_URL}/",
            timeout=15
        )

        if response.status_code == 200:

            try:
                return True, response.json()
            except Exception:
                return True, response.text

        return False, f"HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        return False, "Backend Timeout"

    except requests.exceptions.ConnectionError:
        return False, "Connection Error"

    except Exception as e:
        return False, str(e)


# ============================================================
# ĐĂNG NHẬP / ĐĂNG KÝ
# ============================================================

def login_page():

    st.markdown(
        '<div class="title">💰 Thu Chi AI Pro</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Quản lý thu chi thông minh bằng AI'
        '</div>',
        unsafe_allow_html=True
    )

    st.write("")

    backend_ok, backend_info = check_backend()

    if backend_ok:

        st.success(
            "🟢 Backend đang hoạt động"
        )

    else:

        st.error(
            "🔴 Không kết nối được Backend"
        )

        st.warning(
            f"Backend: {BACKEND_URL}"
        )

        st.caption(
            f"Chi tiết: {backend_info}"
        )

    st.divider()

    col1, col2, col3 = st.columns(
        [1, 2, 1]
    )

    with col2:

        login_tab, register_tab = st.tabs(
            [
                "🔐 Đăng nhập",
                "📝 Đăng ký"
            ]
        )

        # ----------------------------------------------------
        # LOGIN
        # ----------------------------------------------------

        with login_tab:

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
                use_container_width=True,
                type="primary"
            ):

                if not username or not password:

                    st.warning(
                        "Vui lòng nhập tên đăng nhập và mật khẩu."
                    )

                else:

                    with st.spinner(
                        "Đang đăng nhập..."
                    ):

                        result, error = api_post(
                            "/login",
                            {
                                "username": username,
                                "password": password
                            }
                        )

                    if error:

                        st.error(
                            "❌ " + error
                        )

                    elif result:

                        if result.get(
                            "status"
                        ) == "success":

                            st.session_state.logged_in = True

                            st.session_state.user_id = (
                                result.get(
                                    "user_id"
                                )
                            )

                            st.session_state.username = (
                                result.get(
                                    "username",
                                    username
                                )
                            )

                            st.session_state.page = (
                                "Dashboard"
                            )

                            st.success(
                                "✅ Đăng nhập thành công!"
                            )

                            st.rerun()

                        else:

                            st.error(
                                result.get(
                                    "message",
                                    "Đăng nhập thất bại."
                                )
                            )

        # ----------------------------------------------------
        # REGISTER
        # ----------------------------------------------------

        with register_tab:

            new_username = st.text_input(
                "Tên đăng nhập mới",
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
                key="register_confirm"
            )

            if st.button(
                "📝 Tạo tài khoản",
                use_container_width=True
            ):

                if not new_username or not new_password:

                    st.warning(
                        "Vui lòng nhập đầy đủ thông tin."
                    )

                elif new_password != confirm_password:

                    st.error(
                        "❌ Hai mật khẩu không giống nhau."
                    )

                else:

                    with st.spinner(
                        "Đang tạo tài khoản..."
                    ):

                        result, error = api_post(
                            "/register",
                            {
                                "username": new_username,
                                "password": new_password
                            }
                        )

                    if error:

                        st.error(
                            "❌ " + error
                        )

                    elif result:

                        if result.get(
                            "status"
                        ) == "success":

                            st.success(
                                "✅ Đăng ký thành công! "
                                "Hãy chuyển sang Đăng nhập."
                            )

                        else:

                            st.error(
                                result.get(
                                    "message",
                                    "Đăng ký thất bại."
                                )
                            )


# ============================================================
# SIDEBAR
# ============================================================

def sidebar():

    with st.sidebar:

        st.title("💰 Thu Chi AI")

        st.write(
            f"Xin chào **{st.session_state.username}**"
        )

        st.divider()

        if st.button(
            "🏠 Dashboard",
            use_container_width=True
        ):

            st.session_state.page = "Dashboard"
            st.rerun()

        if st.button(
            "➕ Thêm giao dịch",
            use_container_width=True
        ):

            st.session_state.page = "Add"
            st.rerun()

        if st.button(
            "📷 Quét hóa đơn",
            use_container_width=True
        ):

            st.session_state.page = "Scan"
            st.rerun()

        if st.button(
            "📋 Lịch sử",
            use_container_width=True
        ):

            st.session_state.page = "History"
            st.rerun()

        if st.button(
            "📊 Thống kê",
            use_container_width=True
        ):

            st.session_state.page = "Statistics"
            st.rerun()

        st.divider()

        backend_ok, _ = check_backend()

        if backend_ok:

            st.success("🟢 Backend Online")

        else:

            st.error("🔴 Backend Offline")

        if st.button(
            "🚪 Đăng xuất",
            use_container_width=True
        ):

            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = ""

            st.rerun()


# ============================================================
# LẤY GIAO DỊCH
# ============================================================

def get_transactions():

    user_id = st.session_state.user_id

    if not user_id:
        return []

    result, error = api_get(
        f"/transactions/{user_id}"
    )

    if error:

        st.error(
            "❌ " + error
        )

        return []

    if result:

        return result.get(
            "data",
            []
        )

    return []


# ============================================================
# DASHBOARD
# ============================================================

def dashboard():

    st.title("🏠 Dashboard")

    st.write(
        f"Xin chào **{st.session_state.username}** 👋"
    )

    transactions = get_transactions()

    if not transactions:

        st.info(
            "Chưa có giao dịch nào."
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "💰 Tổng thu",
                "0 ₫"
            )

        with col2:
            st.metric(
                "💸 Tổng chi",
                "0 ₫"
            )

        with col3:
            st.metric(
                "📋 Giao dịch",
                "0"
            )

        return

    df = pd.DataFrame(
        transactions
    )

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
    ).fillna(0)

    total_income = df.loc[
        df["type"] == "thu",
        "amount"
    ].sum()

    total_expense = df.loc[
        df["type"] == "chi",
        "amount"
    ].sum()

    balance = (
        total_income -
        total_expense
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "💰 Tổng thu",
            f"{total_income:,.0f} ₫"
        )

    with col2:

        st.metric(
            "💸 Tổng chi",
            f"{total_expense:,.0f} ₫"
        )

    with col3:

        st.metric(
            "💵 Số dư",
            f"{balance:,.0f} ₫"
        )

    with col4:

        st.metric(
            "📋 Giao dịch",
            len(df)
        )

    st.divider()

    st.subheader(
        "📋 Giao dịch gần đây"
    )

    show_columns = [
        "type",
        "amount",
        "category",
        "note",
        "date"
    ]

    columns = [
        c for c in show_columns
        if c in df.columns
    ]

    show_df = df[columns].copy()

    if "type" in show_df.columns:

        show_df["type"] = (
            show_df["type"]
            .map(
                {
                    "thu": "🟢 Thu",
                    "chi": "🔴 Chi"
                }
            )
            .fillna(
                show_df["type"]
            )
        )

    if "amount" in show_df.columns:

        show_df["amount"] = (
            show_df["amount"]
            .apply(
                lambda x:
                f"{x:,.0f} ₫"
            )
        )

    st.dataframe(
        show_df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# THÊM GIAO DỊCH
# ============================================================

def add_transaction():

    st.title(
        "➕ Thêm giao dịch"
    )

    st.write(
        "Nhập câu tự nhiên để AI tự nhận diện giao dịch."
    )

    st.info(
        "Ví dụ: Ăn cơm 50k | Đổ xăng 100k | Nhận lương 10 triệu"
    )

    text = st.text_input(
        "💬 Nội dung giao dịch",
        placeholder="Ví dụ: Ăn cơm 50k"
    )

    if st.button(
        "🤖 AI ghi nhận",
        type="primary",
        use_container_width=True
    ):

        if not text.strip():

            st.warning(
                "Vui lòng nhập giao dịch."
            )

            return

        with st.spinner(
            "🤖 AI đang phân tích..."
        ):

            result, error = api_post(
                "/add-transaction-ai",
                {
                    "user_id": st.session_state.user_id,
                    "text": text
                }
            )

        if error:

            st.error(
                "❌ " + error
            )

            return

        if result:

            data = result.get(
                "data",
                {}
            )

            st.success(
                "✅ Đã ghi nhận giao dịch!"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "💰 Số tiền",
                    f"{float(data.get('amount', 0)):,.0f} ₫"
                )

            with col2:

                st.metric(
                    "📂 Danh mục",
                    data.get(
                        "category",
                        "Khác"
                    )
                )

            with col3:

                st.metric(
                    "📌 Loại",
                    data.get(
                        "type",
                        ""
                    )
                )


# ============================================================
# QUÉT HÓA ĐƠN
# ============================================================

def scan_bill():

    st.title(
        "📷 Quét hóa đơn bằng AI"
    )

    st.write(
        "Tải ảnh hóa đơn để AI phân tích."
    )

    uploaded_file = st.file_uploader(
        "📷 Chọn ảnh hóa đơn",
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
            "🤖 Phân tích hóa đơn",
            type="primary",
            use_container_width=True
        ):

            try:

                image_bytes = (
                    uploaded_file.read()
                )

                image_base64 = (
                    base64.b64encode(
                        image_bytes
                    )
                    .decode("utf-8")
                )

                with st.spinner(
                    "🤖 AI đang đọc hóa đơn..."
                ):

                    result, error = api_post(
                        "/scan-bill",
                        {
                            "user_id":
                                st.session_state.user_id,
                            "image_base64":
                                image_base64
                        },
                        timeout=60
                    )

                if error:

                    st.error(
                        "❌ " + error
                    )

                    return

                if result:

                    data = result.get(
                        "data",
                        {}
                    )

                    st.success(
                        "✅ Đã quét hóa đơn!"
                    )

                    col1, col2, col3 = st.columns(3)

                    with col1:

                        st.metric(
                            "💰 Số tiền",
                            f"{float(data.get('amount', 0)):,.0f} ₫"
                        )

                    with col2:

                        st.metric(
                            "📂 Danh mục",
                            data.get(
                                "category",
                                "Khác"
                            )
                        )

                    with col3:

                        st.metric(
                            "📝 Nội dung",
                            data.get(
                                "note",
                                ""
                            )
                        )

            except Exception as e:

                st.error(
                    f"❌ Lỗi xử lý ảnh: {str(e)}"
                )


# ============================================================
# LỊCH SỬ
# ============================================================

def history():

    st.title(
        "📋 Lịch sử giao dịch"
    )

    transactions = get_transactions()

    if not transactions:

        st.info(
            "Chưa có giao dịch."
        )

        return

    df = pd.DataFrame(
        transactions
    )

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
    ).fillna(0)

    col1, col2 = st.columns(2)

    with col1:

        filter_type = st.selectbox(
            "Loại giao dịch",
            [
                "Tất cả",
                "Thu",
                "Chi"
            ]
        )

    with col2:

        categories = [
            "Tất cả"
        ]

        if "category" in df.columns:

            categories += sorted(
                df["category"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

        filter_category = st.selectbox(
            "Danh mục",
            categories
        )

    filtered = df.copy()

    if filter_type == "Thu":

        filtered = filtered[
            filtered["type"] == "thu"
        ]

    elif filter_type == "Chi":

        filtered = filtered[
            filtered["type"] == "chi"
        ]

    if filter_category != "Tất cả":

        filtered = filtered[
            filtered["category"]
            == filter_category
        ]

    if "type" in filtered.columns:

        filtered["type"] = (
            filtered["type"]
            .map(
                {
                    "thu": "🟢 Thu",
                    "chi": "🔴 Chi"
                }
            )
            .fillna(
                filtered["type"]
            )
        )

    if "amount" in filtered.columns:

        filtered["amount"] = (
            filtered["amount"]
            .apply(
                lambda x:
                f"{x:,.0f} ₫"
            )
        )

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# THỐNG KÊ
# ============================================================

def statistics():

    st.title(
        "📊 Thống kê"
    )

    transactions = get_transactions()

    if not transactions:

        st.info(
            "Chưa có dữ liệu thống kê."
        )

        return

    df = pd.DataFrame(
        transactions
    )

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
    ).fillna(0)

    total_income = df.loc[
        df["type"] == "thu",
        "amount"
    ].sum()

    total_expense = df.loc[
        df["type"] == "chi",
        "amount"
    ].sum()

    balance = (
        total_income -
        total_expense
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "🟢 Tổng thu",
            f"{total_income:,.0f} ₫"
        )

    with col2:

        st.metric(
            "🔴 Tổng chi",
            f"{total_expense:,.0f} ₫"
        )

    with col3:

        st.metric(
            "💵 Số dư",
            f"{balance:,.0f} ₫"
        )

    st.divider()

    expense_df = df[
        df["type"] == "chi"
    ].copy()

    if not expense_df.empty:

        st.subheader(
            "💸 Chi tiêu theo danh mục"
        )

        category_summary = (
            expense_df
            .groupby("category")["amount"]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        st.bar_chart(
            category_summary
        )

        result_df = (
            category_summary
            .reset_index()
        )

        result_df.columns = [
            "Danh mục",
            "Số tiền"
        ]

        result_df["Số tiền"] = (
            result_df["Số tiền"]
            .apply(
                lambda x:
                f"{x:,.0f} ₫"
            )
        )

        st.dataframe(
            result_df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# MAIN
# ============================================================

def main():

    if not st.session_state.logged_in:

        login_page()

        return

    sidebar()

    if st.session_state.page == "Dashboard":

        dashboard()

    elif st.session_state.page == "Add":

        add_transaction()

    elif st.session_state.page == "Scan":

        scan_bill()

    elif st.session_state.page == "History":

        history()

    elif st.session_state.page == "Statistics":

        statistics()

    else:

        dashboard()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
```
