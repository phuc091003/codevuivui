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

# Tải mô hình NLP Hugging Face
@st.cache_resource
def load_nlp_model():
    model_name = "Salesforce/codet5-base"  # Có thể thay thế bằng mô hình khác như "t5-small"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    return tokenizer, model

# Hàm chuyển đổi câu hỏi tự nhiên thành câu lệnh SQL
def nlp_to_sql(question, table_schema="hotel_booking"):
    try:
        tokenizer, model = load_nlp_model()
        prompt = f"Translate the following question into SQL query for the table {table_schema}:\n{question}"
        inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
        outputs = model.generate(inputs.input_ids, max_length=128, num_beams=4, early_stopping=True)
        sql_query = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return sql_query
    except Exception as e:
        return f"Lỗi khi sử dụng mô hình NLP: {e}"

# Tích hợp vào giao diện Streamlit
with st.sidebar:
    st.markdown("### 🤖 NLP Chuyển Đổi")
    natural_language_question = st.text_area(
        "Nhập câu hỏi tự nhiên (ví dụ: 'Hiển thị tất cả các đặt phòng trong tháng 12')", 
        ""
    )

    if st.button("🛠️ Chuyển Đổi Thành SQL"):
        if not natural_language_question:
            st.error("Vui lòng nhập câu hỏi để chuyển đổi!")
        else:
            with st.spinner("Đang chuyển đổi..."):
                generated_sql = nlp_to_sql(natural_language_question)
                st.text_area("Câu lệnh SQL được tạo:", generated_sql)
                
    # Thêm tab hình ảnh của Dashboard trong Sidebar
    with st.sidebar:
     st.markdown("### 📸 Hình ảnh Dashboard")
    image_file = st.file_uploader("Tải lên hình ảnh của Dashboard Power BI:", type=["jpg", "png", "jpeg"])

    # Thực thi câu lệnh SQL đã chuyển đổi
    if st.button("🚀 Thực Thi SQL Từ NLP"):
        if not natural_language_question:
            st.error("Vui lòng nhập câu hỏi trước!")
        else:
            if 'generated_sql' not in locals() or not generated_sql:
                st.error("Không có câu lệnh SQL hợp lệ để thực thi!")
            else:
                with st.spinner("Đang xử lý..."):
                    df = run_query(generated_sql)
                    if df is not None:
                        st.dataframe(df)
                    else:
                        st.error("Không thể thực thi câu lệnh SQL đã tạo.")

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
if analysis == "Dashboard":
    col1, col2 = st.columns([3, 1])

    with col2:
        st.markdown("### 🔍 Nhập thông tin Insight từ Dashboard")
        
        # Ô nhập để người dùng cung cấp insight
        insights = st.text_area("📝 Nhập các insight bạn thu thập được từ Dashboard Power BI:")

        # Hiển thị các insight đã nhập
        if insights:
            st.write(f"Những insight từ Dashboard: {insights}")

    with col1:
        with st.expander("📊 Power BI Dashboard", expanded=True):
            try:
                components.iframe(POWERBI_URL, height=600)
            except Exception as e:
                st.error(f"❌ Lỗi: {str(e)}")

        with st.expander("🔍 Phân Tích Dữ Liệu Trực Tiếp", expanded=False):
            uploaded_file = st.file_uploader("📂 Tải lên tệp dữ liệu CSV:", type=["csv"])
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
