import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# ==========================================
# 1. PAGE SETUP & PREMIUM SYSTEM THEME
# ==========================================
st.set_page_config(
    page_title="Retail Intelligence Suite", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Professional CSS
st.markdown("""
    <style>
        .main { background-color: #f8f9fa; font-family: 'Inter', sans-serif; }
        [data-testid="stSidebar"] { background-color: #0f172a !important; color: #ffffff; }
        [data-testid="stSidebar"] .stMarkdown h2, [data-testid="stSidebar"] p { color: #f1f5f9 !important; }
        
        .metric-container {
            background-color: #ffffff; padding: 20px; border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            border-left: 5px solid #2563eb; margin-bottom: 15px;
        }
        .metric-label { font-size: 0.85rem; color: #64748b; text-transform: uppercase; font-weight: 600; }
        .metric-value { font-size: 1.8rem; color: #0f172a; font-weight: 700; margin-top: 5px; }
        h1 { color: #0f172a !important; font-weight: 800 !important; }
        h3 { color: #1e293b !important; font-weight: 600 !important; margin-top: 20px !important; }
        .custom-hr { border: 0; height: 1px; background: #e2e8f0; margin: 25px 0; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE PIPELINE
# ==========================================
DB_NAME = "retail_data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            product_category TEXT,
            product_name TEXT,
            quantity INTEGER,
            unit_price REAL,
            total_revenue REAL,
            store_location TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_to_db(df):
    conn = sqlite3.connect(DB_NAME)
    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date']).dt.strftime('%Y-%m-%d')
    df_copy['total_revenue'] = df_copy['quantity'] * df_copy['unit_price']
    df_copy.to_sql('sales', conn, if_exists='append', index=False)
    conn.close()
    return df_copy

def fetch_analytics_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM sales", conn)
    conn.close()
    return df

# Initialize DB structure
init_db()

# ==========================================
# 3. SIDEBAR NAVIGATION & UPLOAD
# ==========================================
with st.sidebar:
    try:
        st.image("logo.png", width=80)
    except Exception:
        st.image("https://img.icons8.com/external-flatart-icons-flat-flatarticons/128/external-analytics-marketing-flatart-icons-flat-flatarticons.png", width=70)
        
    st.markdown("## **Retail Intelligence**")
    st.caption("v2.3.0 • Enterprise Edition")
    st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)
    
    st.markdown("### 📥 Data Ingestion")
    uploaded_file = st.file_uploader("Upload Daily Sales (CSV)", type=["csv"])

# Active memory allocation
active_data = pd.DataFrame()

# ==========================================
# 4. INGESTION HANDLING CONTROL
# ==========================================
if uploaded_file is not None:
    try:
        raw_df = pd.read_csv(uploaded_file)
        required_cols = {'date', 'product_category', 'product_name', 'quantity', 'unit_price', 'store_location'}
        
        if required_cols.issubset(raw_df.columns):
            active_data = save_to_db(raw_df)
            st.sidebar.success("⚡ Database synchronized.")
        else:
            st.sidebar.error("Schema Mismatch. Please check file columns.")
    except Exception as e:
        st.sidebar.error(f"Error processing file: {e}")
else:
    # Check if database has persistent analytical data rows
    historical_data = fetch_analytics_data()
    if not historical_data.empty:
        active_data = historical_data

# ==========================================
# 5. STRICT CONDITIONAL APPLICATION RENDER
# ==========================================
if active_data.empty:
    # If no file is uploaded and database is empty, execution completely stops here.
    # The main page layout remains totally blank.
    st.stop()

# ALL CODE BELOW RUNS ONLY AND EXCLUSIVELY WHEN VALID RETAIL DATA EXISTS
st.title("📊 Executive Performance Dashboard")
st.markdown("Real-time transactional insights, revenue trends, and localized store performance.")
st.markdown("<div class='custom-hr'></div>", unsafe_allow_html=True)

# FILTERS ROW
f1, f2 = st.columns(2)
with f1:
    locations = ["All Locations"] + list(active_data['store_location'].unique())
    selected_location = st.selectbox("📍 Store Location", locations)
with f2:
    categories = ["All Categories"] + list(active_data['product_category'].unique())
    selected_category = st.selectbox("🏷️ Product Verticals", categories)

# Filter Application
filtered_data = active_data.copy()
if selected_location != "All Locations":
    filtered_data = filtered_data[filtered_data['store_location'] == selected_location]
if selected_category != "All Categories":
    filtered_data = filtered_data[filtered_data['product_category'] == selected_category]

# KPI ENGINE
total_sales = filtered_data['total_revenue'].sum()
total_items = filtered_data['quantity'].sum()
avg_order_val = filtered_data['total_revenue'].mean() if len(filtered_data) > 0 else 0
top_performer = filtered_data.groupby('product_name')['total_revenue'].sum().idxmax() if len(filtered_data) > 0 else "N/A"

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.markdown(f"<div class='metric-container'><div class='metric-label'>Gross Revenue</div><div class='metric-value'>${total_sales:,.2f}</div></div>", unsafe_allow_html=True)
with kpi2:
    st.markdown(f"<div class='metric-container'><div class='metric-label'>Volume Sold</div><div class='metric-value'>{total_items:,} units</div></div>", unsafe_allow_html=True)
with kpi3:
    st.markdown(f"<div class='metric-container'><div class='metric-label'>Avg ticket value</div><div class='metric-value'>${avg_order_val:,.2f}</div></div>", unsafe_allow_html=True)
with kpi4:
    st.markdown(f"<div class='metric-container'><div class='metric-label'>MVP Product</div><div class='metric-value' style='font-size:1.3rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>{top_performer}</div></div>", unsafe_allow_html=True)

# VISUALIZATIONS
st.markdown("<div class='custom-hr'></div>", unsafe_allow_html=True)
graph_col1, graph_col2 = st.columns(2)
corporate_colors = ['#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe']

with graph_col1:
    st.markdown("### 📅 Net Revenue Run Rate")
    trend_df = filtered_data.groupby('date')['total_revenue'].sum().reset_index().sort_values('date')
    fig_trend = px.line(
        trend_df, x='date', y='total_revenue', markers=True,
        labels={'total_revenue': 'Revenue ($)', 'date': 'Timeline'},
        template="plotly_white"
    )
    fig_trend.update_traces(line_color='#2563eb', line_width=3, marker=dict(size=8, color='#0f172a'))
    fig_trend.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=350)
    st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})

with graph_col2:
    st.markdown("### 📊 Distribution by Product Vertical")
    cat_df = filtered_data.groupby('product_category')['total_revenue'].sum().reset_index()
    fig_bar = px.bar(
        cat_df, x='product_category', y='total_revenue',
        labels={'total_revenue': 'Revenue ($)', 'product_category': 'Category'},
        template="plotly_white",
        color_discrete_sequence=corporate_colors
    )
    fig_bar.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=350)
    st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

# SECURE TRANSACTION LEDGER
st.markdown("<div class='custom-hr'></div>", unsafe_allow_html=True)
with st.expander("📋 Secure SQL Database Record Ledger"):
    st.dataframe(
        filtered_data, 
        use_container_width=True,
        column_config={
            "total_revenue": st.column_config.NumberColumn("Total Revenue", format="$%.2f"),
            "unit_price": st.column_config.NumberColumn("Unit Price", format="$%.2f"),
            "quantity": st.column_config.NumberColumn("Units")
        }
    )
