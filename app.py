```python
import streamlit as st
import requests
import pandas as pd
import base64
import os
from datetime import datetime

# ============================================================
# CẤU HÌNH
# ============================================================

st.set_page_config(
    page_title="Thu Chi AI Pro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend online
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
        font-size: 36px;
        font-weight: bold;
        color: #1565C0;
    }

    .subtitle {
        color: #666;
        font-size: 16px;
    }

    .success-box {
        padding: 15px;
        border-radius: 10px;
        background-color: #E8F5E9;
        border: 1px solid #4CAF50;
        color: #1B5E20;
    }

    .error-box {
        padding: 15px;
        border-radius: 10px;
        background-color: #FFEBEE;
        border: 1px solid #F44336;
        color: #B71C1C;
    }

    .info-box {
        padding: 15px;
        border-radius: 10px;
        background-color: #E3F2FD;
        border: 1px solid #2196F3;
        color: #0D47A1;
    }

    div[data-testid="stMetric"] {
        border: 1px solid #ddd;
        padding: 15px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
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
# HÀM GỌI BACKEND
# ============================================================

def api_post(endpoint, data, timeout=30):
    """Gửi POST request tới Backend."""
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
            detail = result.get("detail", "Backend trả về lỗi.")
            return None, f"{detail}"

        return result, None

    except requests.exceptions.Timeout:
        return None, "Backend phản hồi quá lâu. Có thể Render đang khởi động lại."

    except requests.exceptions.ConnectionError:
        return None, (
            "Không thể kết nối Backend. "
            f"URL hiện tại: {BACKEND_URL}"
        )

    except Exception as e:
        return None, str(e)


def api_get(endpoint, timeout=30):
    """Gửi GET request tới Backend."""
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
            detail = result.get("detail", "Backend trả về lỗi.")
            return None, detail

        return result, None

    except requests.exceptions.Timeout:
        return None, "Backend phản hồi quá lâu."

    except requests.exceptions.ConnectionError:
        return None, (
            "Không thể kết nối Backend. "
            f"URL: {BACKEND_URL}"
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
                data = response.json()
                return True, data
            except Exception:
                return True, response.text

        return False, f"HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        return False, "Backend timeout."

    except requests.exceptions.ConnectionError:
        return False, "Không kết nối được Backend."

    except Exception as e:
        return False, str(e)


# ============================================================
# TRANG ĐĂNG NHẬP / ĐĂNG KÝ
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

    # Kiểm tra Backend
    backend_ok, backend_data = check_backend()

    if backend_ok:
        st.success(
            "🟢 Backend đang hoạt động: "
            "https://thu-chi-ai.onrender.com"
        )
    else:
        st.error("🔴 Không kết nối được Backend")
        st.warning(
            f"URL Backend: {BACKEND_URL}\n\n"
            f"Chi tiết: {backend_data}"
        )

        st.info(
            "Nếu Backend vừa mới khởi động trên Render, "
            "hãy chờ khoảng 30–60 giây rồi tải lại trang."
        )

    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        tab_login, tab_register = st.tabs(
            ["🔐 Đăng nhập", "📝 Đăng ký"]
        )

        # ====================================================
        # LOGIN
        # ====================================================

        with tab_login:

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
                        "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu."
                    )
                else:

                    with st.spinner("Đang đăng nhập..."):

                        result, error = api_post(
                            "/login",
                            {
                                "username": username,
                                "password": password
                            }
                        )

                    if error:
                        st.error(f"❌ {error}")

                    elif result:

                        if result.get("status") == "success":

                            st.session_state.logged_in = True
                            st.session_state.user_id = result.get(
                                "user_id"
                            )
                            st.session_state.username = result.get(
                                "username",
                                username
                            )
                            st.session_state.page = "Dashboard"

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

        # ====================================================
        # REGISTER
        # ====================================================

        with tab_register:

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
                        "❌ Mật khẩu nhập lại không giống nhau."
                    )

                elif len(new_password) < 4:
                    st.warning(
                        "Mật khẩu nên có ít nhất 4 ký tự."
                    )

                else:

                    with st.spinner("Đang tạo tài khoản..."):

                        result, error = api_post(
                            "/register",
                            {
                                "username": new_username,
                                "password": new_password
                            }
                        )

                    if error:
                        st.error(f"❌ {error}")

                    elif result and result.get("status") == "success":

                        st.success(
                            "✅ Tạo tài khoản thành công! "
                            "Bây giờ anh có thể đăng nhập."
                        )

                    else:
                        st.error(
                            result.get(
                                "message",
                                "Không thể tạo tài khoản."
                            )
                        )


# ============================================================
# SIDEBAR
# ============================================================

def sidebar():

    with st.sidebar:

        st.markdown(
            "## 💰 Thu Chi AI Pro"
        )

        st.caption(
            f"Xin chào, **{st.session_state.username}**"
        )

        st.divider()

        pages = {
            "🏠 Dashboard": "Dashboard",
            "➕ Thêm giao dịch": "Add",
            "📷 Quét hóa đơn": "Scan",
            "📋 Lịch sử": "History",
            "📊 Thống kê": "Statistics"
        }

        for label, page in pages.items():

            if st.button(
                label,
                use_container_width=True,
                key=f"menu_{page}"
            ):
                st.session_state.page = page
                st.rerun()

        st.divider()

        st.caption(
            "🔗 Backend"
        )

        st.code(
            BACKEND_URL,
            language="text"
        )

        backend_ok, _ = check_backend()

        if backend_ok:
            st.success("🟢 Backend Online")
        else:
            st.error("🔴 Backend Offline")

        st.divider()

        if st.button(
            "🚪 Đăng xuất",
            use_container_width=True
        ):

            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = ""
            st.session_state.page = "Dashboard"

            st.rerun()


# ============================================================
# LẤY LỊCH SỬ GIAO DỊCH
# ============================================================

def get_transactions():

    user_id = st.session_state.user_id

    if not user_id:
        return []

    result, error = api_get(
        f"/transactions/{user_id}"
    )

    if error:
        st.error(f"❌ {error}")
        return []

    if result:
        return result.get("data", [])

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
            "Chưa có giao dịch nào. "
            "Hãy thêm giao dịch đầu tiên."
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("💰 Tổng thu", "0 ₫")

        with col2:
            st.metric("💸 Tổng chi", "0 ₫")

        with col3:
            st.metric("📊 Số giao dịch", "0")

        return

    df = pd.DataFrame(transactions)

    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        ).fillna(0)

    total_income = 0
    total_expense = 0

    if "type" in df.columns:

        total_income = df.loc[
            df["type"] == "thu",
            "amount"
        ].sum()

        total_expense = df.loc[
            df["type"] == "chi",
            "amount"
        ].sum()

    balance = total_income - total_expense

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

    st.subheader("📋 Giao dịch gần đây")

    display_columns = [
        "type",
        "amount",
        "category",
        "note",
        "date"
    ]

    existing_columns = [
        col for col in display_columns
        if col in df.columns
    ]

    if existing_columns:

        display_df = df[existing_columns].copy()

        if "type" in display_df.columns:
            display_df["type"] = display_df["type"].map(
                {
                    "thu": "🟢 Thu",
                    "chi": "🔴 Chi"
                }
            ).fillna(display_df["type"])

        if "amount" in display_df.columns:
            display_df["amount"] = display_df[
                "amount"
            ].apply(
                lambda x: f"{x:,.0f} ₫"
            )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# THÊM GIAO DỊCH
# ============================================================

def add_transaction():

    st.title("➕ Thêm giao dịch")

    st.write(
        "Nhập giao dịch bằng câu tự nhiên. "
        "AI sẽ tự nhận diện số tiền, loại và danh mục."
    )

    st.info(
        "Ví dụ: **Ăn cơm 50k**  |  "
        "**Đổ xăng 100k**  |  "
        "**Nhận lương 10 triệu**"
    )

    text = st.text_input(
        "💬 Nhập giao dịch",
        placeholder="Ví dụ: Ăn cơm 50k"
    )

    if st.button(
        "🤖 AI ghi nhận giao dịch",
        type="primary",
        use_container_width=True
    ):

        if not text.strip():
            st.warning(
                "Vui lòng nhập nội dung giao dịch."
            )
            return

        with st.spinner("🤖 AI đang phân tích..."):

            result, error = api_post(
                "/add-transaction-ai",
                {
                    "user_id": st.session_state.user_id,
                    "text": text
                }
            )

        if error:
            st.error(f"❌ {error}")
            return

        if result and result.get("status") == "success":

            data = result.get("data", {})

            st.success(
                "✅ Đã ghi nhận giao dịch!"
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Số tiền",
                    f"{float(data.get('amount', 0)):,.0f} ₫"
                )

            with col2:
                st.metric(
                    "Loại",
                    data.get("type", "")
                )

            with col3:
                st.metric(
                    "Danh mục",
                    data.get("category", "")
                )

            st.info(
                f"📝 {data.get('note', text)}"
            )


# ============================================================
# QUÉT HÓA ĐƠN
# ============================================================

def scan_bill():

    st.title("📷 Quét hóa đơn bằng AI")

    st.write(
        "Tải ảnh hóa đơn lên. AI sẽ đọc số tiền "
        "và tự động lưu giao dịch."
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
            caption="Hóa đơn đã chọn",
            use_container_width=True
        )

        if st.button(
            "🤖 Phân tích hóa đơn",
            type="primary",
            use_container_width=True
        ):

            try:

                image_bytes = uploaded_file.read()

                image_base64 = base64.b64encode(
                    image_bytes
                ).decode("utf-8")

                with st.spinner(
                    "🤖 AI đang đọc hóa đơn..."
                ):

                    result, error = api_post(
                        "/scan-bill",
                        {
                            "user_id": st.session_state.user_id,
                            "image_base64": image_base64
                        },
                        timeout=60
                    )

                if error:
                    st.error(f"❌ {error}")
                    return

                if result and result.get("status") == "success":

                    data = result.get(
                        "data",
                        {}
                    )

                    st.success(
                        "✅ Đã quét và lưu hóa đơn!"
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
                    f"❌ Lỗi đọc ảnh: {str(e)}"
                )


# ============================================================
# LỊCH SỬ
# ============================================================

def history():

    st.title("📋 Lịch sử giao dịch")

    transactions = get_transactions()

    if not transactions:

        st.info(
            "Chưa có giao dịch."
        )
        return

    df = pd.DataFrame(
        transactions
    )

    if "amount" in df.columns:

        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        ).fillna(0)

    # Bộ lọc
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

        categories = ["Tất cả"]

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

    filtered_df = df.copy()

    if filter_type == "Thu":
        filtered_df = filtered_df[
            filtered_df["type"] == "thu"
        ]

    elif filter_type == "Chi":
        filtered_df = filtered_df[
            filtered_df["type"] == "chi"
        ]

    if filter_category != "Tất cả":

        filtered_df = filtered_df[
            filtered_df["category"]
            == filter_category
        ]

    # Hiển thị
    if "type" in filtered_df.columns:

        filtered_df["type"] = filtered_df[
            "type"
        ].map(
            {
                "thu": "🟢 Thu",
                "chi": "🔴 Chi"
            }
        ).fillna(
            filtered_df["type"]
        )

    if "amount" in filtered_df.columns:

        filtered_df["amount"] = filtered_df[
            "amount"
        ].apply(
            lambda x: f"{x:,.0f} ₫"
        )

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# THỐNG KÊ
# ============================================================

def statistics():

    st.title("📊 Thống kê")

    transactions = get_transactions()

    if not transactions:

        st.info(
            "Chưa có dữ liệu để thống kê."
        )
        return

    df = pd.DataFrame(
        transactions
    )

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
    ).fillna(0)

    # ================================
    # TỔNG QUAN
    # ================================

    total_income = df.loc[
        df["type"] == "thu",
        "amount"
    ].sum()

    total_expense = df.loc[
        df["type"] == "chi",
        "amount"
    ].sum()

    balance = total_income - total_expense

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

    # ================================
    # CHI THEO DANH MỤC
    # ================================

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

        st.dataframe(
            category_summary
            .reset_index()
            .rename(
                columns={
                    "category": "Danh mục",
                    "amount": "Số tiền"
                }
            ),
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# TRANG CHÍNH
# ============================================================

def main():

    if not st.session_state.logged_in:

        login_page()

        return

    sidebar()

    page = st.session_state.page

    if page == "Dashboard":

        dashboard()

    elif page == "Add":

        add_transaction()

    elif page == "Scan":

        scan_bill()

    elif page == "History":

        history()

    elif page == "Statistics":

        statistics()

    else:

        dashboard()


# ============================================================
# CHẠY APP
# ============================================================

if __name__ == "__main__":
    main()
```

### Quan trọng nhất sau khi dán code

Trong **Streamlit Cloud → Settings → Secrets**, anh đặt:

```toml
BACKEND_URL = "https://thu-chi-ai.onrender.com"
```

Sau đó **Save → Reboot app**.

### Kiểm tra

Khi mở lại Streamlit, ngay màn hình đăng nhập phải hiện:

**🟢 Backend đang hoạt động: https://thu-chi-ai.onrender.com**

Nếu hiện 🟢 thì chúng ta đã xử lý xong lỗi kết nối Backend.

Nếu vẫn hiện 🔴, **đừng sửa thêm code**. Gửi tôi ảnh màn hình phần 🔴 đó, đặc biệt là dòng **“Chi tiết:”**, tôi sẽ xử lý đúng lỗi tiếp theo cho anh.
