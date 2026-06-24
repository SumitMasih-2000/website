import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# ==========================================
# 1. PAGE SETUP & PREMIUM EMERALD THEME
# ==========================================
st.set_page_config(
    page_title="Retail Intelligence Suite", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Professional CSS (Emerald Teal & Mint Palette)
st.markdown("""
    <style>
        .main { background-color: #f4f7f6; font-family: 'Inter', sans-serif; }
        [data-testid="stSidebar"] { background-color: #064e3b !important; color: #ffffff; }
        [data-testid="stSidebar"] .stMarkdown h2, [data-testid="stSidebar"] p { color: #ecfdf5 !important; }
        
        /* Emerald Custom Metric Cards */
        .metric-container {
            background-color: #ffffff; padding: 20px; border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            border-left: 5px solid #10b981; margin-bottom: 15px;
        }
        .metric-label { font-size: 0.85rem; color: #6b7280; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em;}
        .metric-value { font-size: 1.8rem; color: #064e3b; font-weight: 700; margin-top: 5px; }
        h1 { color: #064e3b !important; font-weight: 800 !important; }
        h3 { color: #0f172a !important; font-weight: 600 !important; margin-top: 20px !important; }
        .custom-hr { border: 0; height: 1px; background: #d1d5db; margin: 25px 0; }
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
    st.caption("v2.4.0 • Mint Enterprise")
    st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)
    
    st.markdown("### 📥 Data Ingestion")
    uploaded_file = st.file_uploader("Upload Daily Sales (CSV)", type=["csv"])

# Define empty backup schema so interface has placeholder structures if empty
empty_schema = pd.DataFrame(columns=['date', 'product_category', 'product_name', 'quantity', 'unit_price', 'total_revenue', 'store_location'])
active_data = empty_schema.copy()

# Ingestion Logic
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
    historical_data = fetch_analytics_data()
    if not historical_data.empty:
        active_data = historical_data

# ==========================================
# 4. ALWAYS VISIBLE MAIN INTERFACE
# ==========================================
st.title("📊 Executive Performance Dashboard")
st.markdown("Real-time transactional insights, revenue trends, and localized store performance.")
st.markdown("<div class='custom-hr'></div>", unsafe_allow_html=True)

# FILTERS ROW (Defaults gracefully if dropdown features are missing)
f1, f2 = st.columns(2)
with f1:
    locations = ["All Locations"] + list(active_data['store_location'].unique()) if not active_data.empty else ["All Locations"]
    selected_location = st.selectbox("📍 Store Location", locations)
with f2:
    categories = ["All Categories"] + list(active_data['product_category'].unique()) if not active_data.empty else ["All Categories"]
    selected_category = st.selectbox("🏷️ Product Verticals", categories)

# Filter Application
filtered_data = active_data.copy()
if not filtered_data.empty:
    if selected_location != "All Locations":
        filtered_data = filtered_data[filtered_data['store_location'] == selected_location]
    if selected_category != "All Categories":
        filtered_data = filtered_data[filtered_data['product_category'] == selected_category]

# KPI ENGINE (Evaluates to 0 if data is not uploaded)
has_data = not filtered_data.empty
total_sales = filtered_data['total_revenue'].sum() if has_data else 0.0
total_items = filtered_data['quantity'].sum() if has_data else 0
avg_order_val = filtered_data['total_revenue'].mean() if has_data else 0.0
top_performer = filtered_data.groupby('product_name')['total_revenue'].sum().idxmax() if has_data and len(filtered_data) > 0 else "None"

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.markdown(f"<div class='metric-container'><div class='metric-label'>Gross Revenue</div><div class='metric-value'>${total_sales:,.2f}</div></div>", unsafe_allow_html=True)
with kpi2:
    st.markdown(f"<div class='metric-container'><div class='metric-label'>Volume Sold</div><div class='metric-value'>{total_items:,} units</div></div>", unsafe_allow_html=True)
with kpi3:
    st.markdown(f"<div class='metric-container'><div class='metric-label'>Avg ticket value</div><div class='metric-value'>${avg_order_val:,.2f}</div></div>", unsafe_allow_html=True)
with kpi4:
    st.markdown(f"<div class='metric-container'><div class='metric-label'>MVP Product</div><div class='metric-value' style='font-size:1.3rem;'>{top_performer}</div></div>", unsafe_allow_html=True)

# VISUALIZATIONS
st.markdown("<div class='custom-hr'></div>", unsafe_allow_html=True)
graph_col1, graph_col2 = st.columns(2)
mint_palette = ['#10b981', '#34d399', '#6ee7b7', '#a7f3d0', '#d1fae5']

with graph_col1:
    st.markdown("### 📅 Net Revenue Run Rate")
    if has_data:
        trend_df = filtered_data.groupby('date')['total_revenue'].sum().reset_index().sort_values('date')
    else:
        trend_df = pd.DataFrame(columns=['date', 'total_revenue'])
        
    fig_trend = px.line(
        trend_df, x='date', y='total_revenue', markers=True,
        labels={'total_revenue': 'Revenue ($)', 'date': 'Timeline'},
        template="plotly_white"
    )
    fig_trend.update_traces(line_color='#10b981', line_width=3, marker=dict(size=8, color='#064e3b'))
    fig_trend.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=350, xaxis_title="Timeline", yaxis_title="Revenue ($)")
    st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})

with graph_col2:
    st.markdown("### 📊 Distribution by Product Vertical")
    if has_data:
        cat_df = filtered_data.groupby('product_category')['total_revenue'].sum().reset_index()
    else:
        cat_df = pd.DataFrame(columns=['product_category', 'total_revenue'])
        
    fig_bar = px.bar(
        cat_df, x='product_category', y='total_revenue',
        labels={'total_revenue': 'Revenue ($)', 'product_category': 'Category'},
        template="plotly_white",
        color_discrete_sequence=mint_palette
    )
    fig_bar.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=350, xaxis_title="Category", yaxis_title="Revenue ($)")
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
