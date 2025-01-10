import streamlit as st
import pandas as pd
import pymysql
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from transformers import pipeline
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="Hotel Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Thông tin email
SENDER_EMAIL = 'huuphucnguyen73@gmail.com'
SENDER_PASSWORD = 'uayhjbbkczvgxyue'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

# Cấu hình kết nối MySQL
host = "127.0.0.1"
user = "root"
password = "hoilamj12"
database = "hotel_booking_db"

# Power BI URL
POWERBI_URL = "https://app.powerbi.com/reportEmbed?reportId=619dd003-a214-4810-85a3-c507d75ff8f0&autoAuth=true&ctid=55b99119-ae4f-4bf9-b354-7e6ba2eb1bf2"

# Kết nối cơ sở dữ liệu MySQL
def connect_to_db():
    return pymysql.connect(host=host, user=user, password=password, database=database)

# Thực thi câu truy vấn SQL
def run_query(query):
    conn = connect_to_db()
    try:
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return None
    finally:
        conn.close()

# Tích hợp vào giao diện Streamlit
with st.sidebar:  
    # Thêm tab hình ảnh của Dashboard trong Sidebar
    with st.sidebar:
     st.markdown("### 📸 Hình ảnh Dashboard")
    image_file = st.file_uploader("Tải lên hình ảnh của Dashboard Power BI:", type=["jpg", "png", "jpeg"], key="image_upload")
# Tạo báo cáo PDF
def create_pdf(report_text, insights, output_filename="report.pdf"):
    pdfmetrics.registerFont(TTFont('Roboto', 'Roboto-Black.ttf'))

    c = canvas.Canvas(output_filename, pagesize=letter)
    width, height = letter
    c.setFont("Roboto", 16)
    c.drawString(100, height - 40, "Báo Cáo Phân Tích Đặt Phòng Khách Sạn")

    c.setFont("Roboto", 12)

    # Thêm nội dung báo cáo
    text_object = c.beginText(100, height - 80)
    text_object.textLines(report_text)
    c.drawText(text_object)

    # Thêm insight vào báo cáo PDF
    if insights:
        c.setFont("Roboto", 12)
        c.drawString(100, height - 150, "Các Insight từ Dashboard Power BI:")
        text_object = c.beginText(100, height - 170)
        text_object.textLines(insights)
        c.drawText(text_object)

    # Thêm liên kết Power BI vào báo cáo
    c.drawString(100, height - 300, "Truy cập Dashboard Power BI tại: " + POWERBI_URL)

    c.showPage()
    c.save()
    
# Gửi email với file đính kèm PDF
def send_email(to_email, subject, body, attachment_filename, insights, image_filename=None):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject

    # Nối phần insight vào nội dung email
    full_body = body + "\n\n" + "Các insight từ Dashboard Power BI:\n" + insights
    msg.attach(MIMEText(full_body, 'plain'))

    # Đính kèm báo cáo PDF
    with open(attachment_filename, "rb") as attachment:
        part = MIMEApplication(attachment.read(), Name=attachment_filename)
        part['Content-Disposition'] = f'attachment; filename="{attachment_filename}"'
        msg.attach(part)

    # Đính kèm hình ảnh nếu có
    if image_filename:
        with open(image_filename, "rb") as img_attachment:
            img_part = MIMEApplication(img_attachment.read(), Name=image_filename)
            img_part['Content-Disposition'] = f'attachment; filename="{image_filename}"'
            msg.attach(img_part)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
            st.success("Email đã được gửi thành công!")
    except Exception as e:
        st.error(f"Lỗi khi gửi email: {e}")
        


# Giao diện Streamlit
st.markdown("<h2>📤 Gửi Báo Cáo qua Email</h2>", unsafe_allow_html=True)

# CSS
st.markdown("""
<style>
    :root {
        --primary: #005B96;
        --secondary: #0288D1;
        --accent: #81D4FA;
        --bg: #F9FAFB;
        --text: #2C3E50;
        --sidebar-bg: #E3F2FD;
        --sidebar-text: #004466;
    }

    .stApp {
        background-color: var(--bg);
        color: var(--text);
    }

    h1, h2, h3 {
        color: var(--primary) !important;
        font-family: 'Playfair Display', serif !important;
        padding: 1rem 0;
        border-bottom: 2px solid var(--accent);
    }

    .stButton>button {
        background-color: var(--secondary);
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        border: none;
        transition: all 0.3s;
    }

    .stButton>button:hover {
        background-color: var(--primary);
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    [data-testid=stSidebar] {
        background-color: var(--sidebar-bg);
        color: var(--sidebar-text);
        padding: 1rem;
    }

    .sidebar-content {
        color: var(--sidebar-text);
    }

    .dataframe {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .stPlot {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 style='text-align:center'>🏨 Hotel Analytics Dashboard</h1>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🔍 Phân Tích")
    query = st.text_area("📝 SQL Query:", "SELECT * FROM hotel_booking LIMIT 10;", height=150)
    # Hiển thị câu lệnh SQL sau khi người dùng chọn câu hỏi
    if st.button("🚀 Thực thi"):
        with st.spinner("Đang xử lý..."):
            df = run_query(query)
            if df is not None:
                st.dataframe(df)
                df.to_csv("results.csv", index=False)
                st.success("✅ Đã lưu kết quả")

    analysis = st.selectbox("📊 Chọn phân tích:", [
        "Dashboard",
        "Tỷ lệ hủy đặt phòng",
        "Doanh thu theo loại phòng",
        "Thời gian lưu trú",
        "Thống kê đặt trước",
        "So sánh doanh thu"
    ])
# Main content
# Insight
direct_insights = """
1. Tổng doanh thu và số lượng hủy phòng
Tổng doanh thu: 46,34 triệu.
Số lượng hủy phòng: 43 nghìn lượt.
Đây là một con số đáng chú ý, cho thấy tỷ lệ hủy phòng có thể ảnh hưởng lớn đến doanh thu.
2. Tỷ lệ hủy phòng theo mùa
Tỷ lệ hủy phòng cao nhất vào mùa hè (Summer) với giá trị khoảng 0,377.
Tỷ lệ hủy giảm dần qua các mùa:
Mùa xuân (Spring): 0,36.
Mùa thu (Autumn): 0,34.
Mùa đông (Winter): 0,22 (thấp nhất).
Mùa hè có tỷ lệ hủy phòng cao nhất, có thể do nhu cầu du lịch tăng cao nhưng khách hàng thay đổi kế hoạch thường xuyên.
3. Tổng doanh thu theo mùa
Doanh thu cao nhất vào mùa hè (Summer) với hơn 19,5 triệu.
Các mùa khác:
Mùa xuân (Spring): khoảng 11,7 triệu.
Mùa thu (Autumn): khoảng 10,5 triệu.
Mùa đông (Winter): thấp nhất, khoảng 4,6 triệu.
Mùa hè là mùa cao điểm, mang lại doanh thu lớn nhất, trong khi mùa đông là mùa thấp điểm.
4. Doanh thu theo loại khách hàng
Phân bổ khách hàng:
Transient (khách lẻ): chiếm tỷ lệ lớn nhất, khoảng 67,5%.
Contract (hợp đồng): khoảng 12,4%.
Group (nhóm): khoảng 11,2%.
Transient-Party: khoảng 8,9%.
Khách lẻ là nguồn doanh thu chính, trong khi khách nhóm và hợp đồng chiếm tỷ lệ nhỏ hơn.
5. Số lượng đặt phòng theo tháng
Số lượng đặt phòng cao nhất vào tháng 5 và thấp nhất là vào tháng 2.
Số lượng đặt phòng tăng dần từ đầu năm, đạt đỉnh vào mùa hè (tháng 5), sau đó giảm dần vào cuối năm.
6. Bản đồ phân bố
Bản đồ hiển thị các điểm đặt phòng trên toàn cầu, tập trung chủ yếu ở các khu vực lớn như châu Âu, Bắc Mỹ, và Đông Á.
Đề xuất và chiến lược:

1 Trong khi doanh thu và tỷ lệ đặt phòng thấp vào mùa đông, bạn có thể phát triển các chiến lược marketing đặc biệt cho thời gian này. Cung cấp các gói dịch vụ đặc biệt cho khách du lịch mùa đông như các tour du lịch, dịch vụ spa, hoặc các hoạt động trong nhà
"""

# Khởi tạo trạng thái giao diện
if "insight_visible" not in st.session_state:
    st.session_state["insight_visible"] = True

# Giao diện chính
# Giao diện chính
if "Dashboard":
    # Điều chỉnh tỷ lệ cột theo trạng thái Insight
    if st.session_state["insight_visible"]:
        col1, col2 = st.columns([4, 1])
    else:
        col1, col2 = st.columns([5, 0.5])

    # Cột chính hiển thị Power BI Dashboard
    with col1:
        with st.expander("📊 Power BI Dashboard", expanded=True):
            try:
                components.iframe(POWERBI_URL, height=600)
            except Exception as e:
                st.error(f"❌ Lỗi: {str(e)}")

        with st.expander("🔍 Phân Tích Dữ Liệu Trực Tiếp", expanded=False):
            uploaded_file = st.file_uploader("📂 Tải lên tệp dữ liệu CSV:", type=["csv"], key="csv_upload")
            if uploaded_file is not None:
                data = pd.read_csv(uploaded_file)
                st.markdown("#### 📈 Dữ liệu đã tải lên:")
                st.dataframe(data.head(10))
                st.markdown("#### 🛠️ Phân tích cơ bản:")
                st.write("Số hàng và cột:", data.shape)
                st.write("Thông tin dữ liệu:", data.describe())
                st.write("Dữ liệu thiếu:", data.isnull().sum())
                if st.checkbox("📊 Hiển thị biểu đồ phân phối cột đầu tiên"):
                    fig, ax = plt.subplots(figsize=(10, 6))
                    sns.histplot(data.iloc[:, 0], kde=True, ax=ax)
                    st.pyplot(fig)

    # Cột phụ hiển thị khung nhập Insight
    with col2:
        # Nút toggle trạng thái ẩn/hiện Insight
        toggle_button = "Ẩn" if st.session_state["insight_visible"] else "Hiện"
        if st.button(f"🔄 {toggle_button} Insight"):
            st.session_state["insight_visible"] = not st.session_state["insight_visible"]

        if st.session_state["insight_visible"]:
            st.markdown("### 🔍 Nhập thông tin Insight")
            
            # **Move the direct insights to an expandable section**
            with st.expander("👉 Các Insight đã nhập:", expanded=False):
                st.write(direct_insights)

            # Hiển thị khung nhập thêm insight nếu cần
            insights = st.text_area(
                "📝 Nhập các insight bạn thu thập được từ Dashboard Power BI:",
                height=200,
            )
            # Hiển thị các insight đã nhập
            if insights.strip():
                st.markdown("#### Những Insight đã nhập:")
                st.write(insights)

            # Thêm khung nhập trực tiếp Insight vào code
            with st.expander("🔧 Tùy chỉnh hoặc xử lý Insight thêm", expanded=False):
                st.code(insights, language="python")
if analysis == "Tỷ lệ hủy đặt phòng":
    st.markdown("### 📊 Tỷ lệ Hủy Đặt Phòng")
    query = "SELECT is_canceled, COUNT(*) AS count FROM hotel_booking GROUP BY is_canceled"
    df = run_query(query)

    if df is not None:
         # Hiển thị bảng dữ liệu
        st.dataframe(df)
        df['is_canceled'] = df['is_canceled'].map({0: 'Không hủy', 1: 'Hủy'})
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.barplot(data=df, x='is_canceled', y='count', ax=ax, palette='viridis')
        ax.set_title("Tỷ lệ Hủy Đặt Phòng")
        ax.set_xlabel("Trạng Thái Hủy")
        ax.set_ylabel("Số Lượng")
        st.pyplot(fig)

if analysis == "Doanh thu theo loại phòng":
    st.markdown("### 📊 Doanh Thu Theo Loại Phòng")
    query = """
        SELECT assigned_room_type AS room_type, SUM(adr) AS revenue
        FROM hotel_booking
        WHERE is_canceled = 0
        GROUP BY assigned_room_type
        ORDER BY revenue DESC
    """
    df = run_query(query)

    if df is not None:
         # Hiển thị bảng dữ liệu
        st.dataframe(df)
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(data=df, x='room_type', y='revenue', ax=ax, palette='coolwarm')
        ax.set_title("Doanh Thu Theo Loại Phòng")
        ax.set_xlabel("Loại Phòng")
        ax.set_ylabel("Doanh Thu (ADR)")
        st.pyplot(fig)

if analysis == "Thời gian lưu trú":
    st.markdown("### 📊 Thời Gian Lưu Trú")
    query = """
        SELECT 
            (stays_in_weekend_nights + stays_in_week_nights) AS total_stay, 
            COUNT(*) AS count
        FROM hotel_booking
        GROUP BY total_stay
        ORDER BY total_stay
    """
    df = run_query(query)

    if df is not None:
         # Hiển thị bảng dữ liệu
        st.dataframe(df)
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(data=df, x='total_stay', y='count', ax=ax, palette='muted')
        ax.set_title("Phân Phối Thời Gian Lưu Trú")
        ax.set_xlabel("Thời Gian Lưu Trú (Đêm)")
        ax.set_ylabel("Số Lượng")
        st.pyplot(fig)

if analysis == "Thống kê đặt trước":
    st.markdown("### 📊 Thống Kê Đặt Trước")
    query = """
        SELECT lead_time, COUNT(*) AS count
        FROM hotel_booking
        GROUP BY lead_time
        ORDER BY lead_time
        LIMIT 50
    """
    df = run_query(query)

    if df is not None:
         # Hiển thị bảng dữ liệu
        st.dataframe(df)
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.lineplot(data=df, x='lead_time', y='count', ax=ax, color='green', marker='o')
        ax.set_title("Thống Kê Thời Gian Đặt Trước")
        ax.set_xlabel("Thời Gian Đặt Trước (Ngày)")
        ax.set_ylabel("Số Lượng")
        st.pyplot(fig)

if analysis == "So sánh doanh thu":
    st.markdown("### 📊 So Sánh Doanh Thu Theo Năm")
    query = """
        SELECT arrival_date_year AS year, SUM(adr) AS revenue
        FROM hotel_booking
        WHERE is_canceled = 0
        GROUP BY arrival_date_year
        ORDER BY year
    """
    df = run_query(query)

    if df is not None:
         # Hiển thị bảng dữ liệu
        st.dataframe(df)
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(data=df, x='year', y='revenue', ax=ax, palette='Spectral')
        ax.set_title("So Sánh Doanh Thu Theo Năm")
        ax.set_xlabel("Năm")
        ax.set_ylabel("Doanh Thu (ADR)")
        st.pyplot(fig)

# Nhập thông tin người nhận email
to_email = st.text_input("📧 Email người nhận:")
report_text = st.text_area("✍️ Nội dung báo cáo:")
attachment_filename = "hotel_report.pdf"

if st.button("📄 Tạo Báo Cáo"):
    create_pdf(report_text, insights, output_filename=attachment_filename)
    st.success(f"Báo cáo PDF đã được tạo: {attachment_filename}")

img_path = None

if image_file is not None:
    img_path = f"dashboard_image.{image_file.type.split('/')[1]}"
    with open(img_path, "wb") as f:
        f.write(image_file.getbuffer())
        
# Cập nhật phần gửi email
if st.button("📧 Gửi Email"):
    if not to_email:
        st.error("Vui lòng nhập email người nhận!")
    elif not insights:  # Kiểm tra xem người dùng có nhập insight không
        st.error("Vui lòng nhập insight từ Dashboard Power BI!")
    else:
        send_email(to_email, "Báo Cáo Phân Tích Khách Sạn", report_text, attachment_filename, insights, image_filename=img_path)
