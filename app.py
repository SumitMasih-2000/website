import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# ==========================================
# 1. DATABASE & BACKEND LOGIC
# ==========================================
DB_NAME = "retail_data.db"

def init_db():
    """Initializes the SQL database with a sales table."""
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
    """Cleans and appends uploaded data into the SQL database."""
    conn = sqlite3.connect(DB_NAME)
    # Business Logic: Ensure correct data types and calculate Total Revenue if missing
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    df['total_revenue'] = df['quantity'] * df['unit_price']
    
    # Append data to SQL
    df.to_sql('sales', conn, if_exists='append', index=False)
    conn.close()

def fetch_analytics_data():
    """Retrieves all data from SQL for analysis."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM sales", conn)
    conn.close()
    return df

# ==========================================
# 2. STREAMLIT USER INTERFACE (UI)
# ==========================================
st.set_page_config(page_title="Automated Retail Analytics", layout="wide")
init_db()

st.title("📊 Automated Retail Analytics Dashboard")
st.subheader("Upload raw sales data to instantly generate business insights and SQL records.")

# Sidebar - Data Upload
st.sidebar.header("📥 Upload Center")
uploaded_file = st.sidebar.file_uploader("Upload Retail CSV", type=["csv"])

if uploaded_file is not None:
    try:
        raw_df = pd.read_csv(uploaded_file)
        
        # Validate expected columns
        required_cols = {'date', 'product_category', 'product_name', 'quantity', 'unit_price', 'store_location'}
        if required_cols.issubset(raw_df.columns):
            save_to_db(raw_df)
            st.sidebar.success("🎉 Data successfully processed and saved to SQL!")
        else:
            st.sidebar.error(f"Missing columns! Required: {required_cols}")
    except Exception as e:
        st.sidebar.error(f"Error parsing file: {e}")

# Fetch latest data from SQL
data = fetch_analytics_data()

if data.empty:
    st.info("👋 Welcome! Please upload a retail CSV file in the sidebar to populate the dashboard.")
    
    # Provide a sample data template for the user
    st.markdown("### 📝 Expected CSV Format Template:")
    sample_template = pd.DataFrame([{
        "date": "2026-01-01", "product_category": "Electronics", "product_name": "Laptop",
        "quantity": 5, "unit_price": 800.00, "store_location": "New York"
    }])
    st.dataframe(sample_template)

else:
    # ==========================================
    # 3. FILTERS & INTERACTIVE FEATURES
    # ==========================================
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        locations = ["All"] + list(data['store_location'].unique())
        selected_location = st.selectbox("📍 Filter by Store Location", locations)
    with col2:
        categories = ["All"] + list(data['product_category'].unique())
        selected_category = st.selectbox("🏷️ Filter by Product Category", categories)

    # Apply Filters to Dataframe
    filtered_data = data.copy()
    if selected_location != "All":
        filtered_data = filtered_data[filtered_data['store_location'] == selected_location]
    if selected_category != "All":
        filtered_data = filtered_data[filtered_data['product_category'] == selected_category]

    # ==========================================
    # 4. AUTOMATED KPIs
    # ==========================================
    total_sales = filtered_data['total_revenue'].sum()
    total_items = filtered_data['quantity'].sum()
    avg_order_val = filtered_data['total_revenue'].mean() if len(filtered_data) > 0 else 0
    top_performer = filtered_data.groupby('product_name')['total_revenue'].sum().idxmax() if len(filtered_data) > 0 else "N/A"

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("💰 Total Revenue", f"${total_sales:,.2f}")
    kpi2.metric("📦 Units Sold", f"{total_items:,}")
    kpi3.metric("📈 Avg Transaction Value", f"${avg_order_val:,.2f}")
    kpi4.metric("🏆 Top Product", top_performer)

    # ==========================================
    # 5. DYNAMIC GRAPHS & TRENDS
    # ==========================================
    st.markdown("---")
    graph_col1, graph_col2 = st.columns(2)

    with graph_col1:
        st.subheader("📅 Revenue Trend Over Time")
        # Aggregate revenue by date
        trend_df = filtered_data.groupby('date')['total_revenue'].sum().reset_index().sort_values('date')
        fig_trend = px.line(trend_df, x='date', y='total_revenue', markers=True,
                            labels={'total_revenue': 'Revenue ($)', 'date': 'Date'},
                            template="plotly_white")
        st.plotly_chart(fig_trend, use_container_width=True)

    with graph_col2:
        st.subheader("📊 Revenue by Product Category")
        cat_df = filtered_data.groupby('product_category')['total_revenue'].sum().reset_index()
        fig_bar = px.bar(cat_df, x='product_category', y='total_revenue', color='product_category',
                         labels={'total_revenue': 'Revenue ($)', 'product_category': 'Category'},
                         template="plotly_white")
        st.plotly_chart(fig_bar, use_container_width=True)

    # View Raw SQL Records
    with st.expander("🔍 View Raw SQL Database Records"):
        st.dataframe(filtered_data, use_container_width=True)
