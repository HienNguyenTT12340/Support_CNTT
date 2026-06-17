import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# ====================================================
# 1. CẤU HÌNH THÔNG TIN GOOGLE SHEETS CỦA BẠN
# ====================================================
# Dán link Apps Script (mã /exec) của bạn vào đây
API_URL = "https://script.google.com/macros/s/AKfycbz_wIoCEjetiJ5j0D1CszZYWfYrYaQclM2lTlFl9Sr-oKI1wbNbObHtOwmgkDIJrKae/exec"

# Dán ID file Google Sheets của bạn vào đây
SHEET_ID = "1mySA4SihCcHY1lKO53tq0EiomDx1LUKkvRZgZLmPrnc" 
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# ====================================================
# 2. ĐỊNH NGHĨA TÀI KHOẢN (Đơn giản, không cần DB)
# ====================================================
# Bạn có thể thêm bớt tài khoản admin hoặc user ở đây tùy ý
ACCOUNTS = {
    "admin": {"password": "admin123", "role": "admin"},
    "user1": {"password": "user123", "role": "user"},
    "user2": {"password": "user123", "role": "user"}
}

# Cấu hình giao diện trang
st.set_page_config(page_title="IT Support Portal", layout="wide")

# Khởi tạo trạng thái đăng nhập nếu chưa có
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

# Hàm đọc dữ liệu từ Google Sheets
def load_data():
    try:
        return pd.read_csv(f"{CSV_URL}&nocache={int(datetime.now().timestamp())}")
    except Exception:
        return pd.DataFrame(columns=["Mã Yêu Cầu", "Người Gửi", "Loại Dịch Vụ", "Nội Dung", "Trạng Thái", "Ngày Tạo"])

# ====================================================
# MÀN HÌNH 1: GIAO DIỆN ĐĂNG NHẬP (LOGIN)
# ====================================================
if not st.session_state.logged_in:
    st.title("🔐 Đăng nhập hệ thống IT Support")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Tài khoản").strip()
            password = st.text_input("Mật khẩu", type="password")
            btn_login = st.form_submit_button("Đăng nhập")
            
            if btn_login:
                if username in ACCOUNTS and ACCOUNTS[username]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = ACCOUNTS[username]["role"]
                    st.success("Đăng nhập thành công!")
                    st.rerun()
                else:
                    st.error("Sai tài khoản hoặc mật khẩu!")

# ====================================================
# MÀN HÌNH 2: GIAO DIỆN CHÍNH (Sau khi đăng nhập thành công)
# ====================================================
else:
    # Thanh điều hướng phía trên / Nút Đăng xuất
    col_title, col_logout = st.columns([5, 1])
    with col_title:
        st.title(f"💻 Hệ Thống Hỗ Trợ CNTT - Xin chào {st.session_state.username}!")
    with col_logout:
        if st.button("🚪 Đăng xuất"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.role = ""
            st.rerun()

    # Tải dữ liệu từ Sheet về
    df = load_data()

    # Phân quyền giao diện dựa trên vai trò (Role)
    
    # ------------------------------------------------
    # PHÂN QUYỀN: TÀI KHOẢN QUẢN TRỊ VIÊN (ADMIN)
    # ------------------------------------------------
    if st.session_state.role == "admin":
        st.subheader("🛠️ Khu vực dành riêng cho Quản trị viên")
        
        if df.empty or len(df) == 0:
            st.info("Chưa có dữ liệu yêu cầu nào.")
        else:
            ticket_list = df["Mã Yêu Cầu"].tolist()
            selected_id = st.selectbox("Chọn mã yêu cầu cần duyệt:", ticket_list)
            
            ticket_info = df[df["Mã Yêu Cầu"] == selected_id].iloc[0]
            st.write(f"Yêu cầu từ: **{ticket_info['Người Gửi']}** - Nội dung: {ticket_info['Nội Dung']}")
            st.write(f"Trạng thái hiện tại: `{ticket_info['Trạng Thái']}`")
            
            new_status = st.selectbox("Đổi trạng thái thành:", ["Chờ duyệt", "Đang xử lý", "Đã hoàn thành"])
            
            if st.button("Cập nhật trạng thái"):
                payload = {
                    "action": "update",
                    "ticket_id": selected_id,
                    "new_status": new_status
                }
                response = requests.post(API_URL, json=payload)
                
                if response.status_code == 200:
                    st.success(f"Đã cập nhật trạng thái {selected_id} thành {new_status}!")
                    st.rerun()
                else:
                    st.error("Cập nhật thất bại!")
            
            st.markdown("---")
            st.subheader("📋 Danh sách toàn bộ yêu cầu trong hệ thống")
            st.dataframe(df, use_container_width=True)

    # ------------------------------------------------
    # PHÂN QUYỀN: TÀI KHOẢN NGƯỜI DÙNG thường (USER)
    # ------------------------------------------------
    else:
        st.subheader("🙋 Gửi yêu cầu mới")
        with st.form("form_request", clear_on_submit=True):
            service_type = st.selectbox("Dịch vụ cần hỗ trợ", ["Cài phần mềm", "Lỗi phần cứng", "Mất mạng", "Tài khoản/Email"])
            content = st.text_area("Chi tiết lỗi *")
            submit = st.form_submit_button("Gửi hỗ trợ")
            
        if submit:
            if content:
                ticket_id = f"IT-{int(datetime.now().timestamp())}"
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Gửi dữ liệu qua Apps Script (Người Gửi lấy tự động từ tên Đăng nhập)
                payload = {
                    "action": "append",
                    "row": [ticket_id, st.session_state.username, service_type, content, "Chờ duyệt", created_at]
                }
                response = requests.post(API_URL, json=payload)
                
                if response.status_code == 200:
                    st.success(f"Đã gửi thành công! Mã số: {ticket_id}")
                    st.rerun()
                else:
                    st.error("Có lỗi xảy ra khi kết nối dữ liệu!")
            else:
                st.error("Vui lòng điền chi tiết lỗi!")

        st.markdown("---")
        st.subheader("📋 Lịch sử yêu cầu của bạn")
        # Lọc dữ liệu: User thông thường chỉ xem được đúng các ticket do chính mình gửi lên
        user_df = df[df["Người Gửi"] == st.session_state.username]
        st.dataframe(user_df, use_container_width=True)
