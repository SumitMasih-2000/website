import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# ==============================================================================
# 1. APPLICATION ARCHITECTURE & THEME (MINT ENTERPRISE LUX)
# ==============================================================================
st.set_page_config(
    page_title="Retail Intelligence Suite", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Unified Style Sheets + Material Icon CDN Injection
st.markdown("""
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons+Round" rel="stylesheet">
    <style>
        /* Base Page Configurations */
        .main { background-color: #f8fafc; font-family: 'Inter', sans-serif; }
        [data-testid="stSidebar"] { background-color: #064e3b !important; color: #ffffff; }
        [data-testid="stSidebar"] .stMarkdown h2, [data-testid="stSidebar"] p { color: #ecfdf5 !important; }
        
        /* Executive KPI Containers */
        .metric-card {
            background-color: #ffffff; 
            padding: 24px; 
            border-radius: 14px;
            box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.05), 0 2px 4px -2px rgba(15, 23, 42, 0.05);
            border-top: 4px solid #10b981; 
            margin-bottom: 20px;
            position: relative;
            overflow: hidden;
        }
        .metric-lbl { font-size: 0.75rem; color: #64748b; text-transform: uppercase; font-weight: 700; letter-spacing: 0.075em;}
        .metric-val { font-size: 1.8rem; color: #064e3b; font-weight: 800; margin-top: 8px; }
        
        /* Material Icon Font Inside Dashboard Cards */
        .card-icon {
            position: absolute;
            right: 15px;
            top: 20px;
            font-size: 1.8rem !important;
            color: #10b981;
            opacity: 0.3;
        }
        
        /* Component Accents */
        h1 { color: #064e3b !important; font-weight: 800 !important; letter-spacing: -0.025em; margin-bottom: 5px !important; }
        h3 { color: #0f172a !important; font-weight: 700 !important; margin-bottom: 15px !important; }
        .divider { border: 0; height: 1px; background: #e2e8f0; margin: 30px 0; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. DATA PIPELINE & GEO-COORDINATE RECOGNITION ENGINE
# ==============================================================================
DB_NAME = "retail_data.db"

COORDINATE_REGISTRY = {
    "New York": {"lat": 40.7128, "lon": -74.0060},
    "Los Angeles": {"lat": 34.0522, "lon": -118.2437},
    "Chicago": {"lat": 41.8781, "lon": -87.6298},
    "London": {"lat": 51.5074, "lon": -0.1278},
    "Tokyo": {"lat": 35.6762, "lon": 139.6503},
    "Paris": {"lat": 48.8566, "lon": 2.3522}
}

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

# ==============================================================================
# 3. SIDEBAR NAVIGATION CONTROLS (Incorporating Your Logo Asset)
# ==============================================================================
with st.sidebar:
    # Looks for 'logo.png' locally in your project root directory
    try:
        st.image("logo.png", width=90)
    except Exception:
        # Fallback if file isn't named right or missing
        st.image("https://img.icons8.com/external-flatart-icons-flat-flatarticons/128/external-analytics-marketing-flatart-icons-flat-flatarticons.png", width=70)
        
    st.markdown("## **Retail Intelligence**")
    st.caption("v2.9.0 • Custom Branding")
    st.markdown("<div style='margin: 25px 0;'></div>", unsafe_allow_html=True)
    
    st.markdown("### Ingestion Hub")
    uploaded_file = st.file_uploader("Upload Sales File", type=["csv", "xlsx"], label_visibility="collapsed")

active_data = pd.DataFrame(columns=['date', 'product_category', 'product_name', 'quantity', 'unit_price', 'total_revenue', 'store_location'])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            raw_df = pd.read_csv(uploaded_file)
        else:
            raw_df = pd.read_excel(uploaded_file)
            
        raw_df.columns = raw_df.columns.str.lower().str.strip().str.replace(' ', '_')
        required_cols = {'date', 'product_category', 'product_name', 'quantity', 'unit_price', 'store_location'}
        
        if required_cols.issubset(raw_df.columns):
            active_data = save_to_db(raw_df)
            st.sidebar.success("⚡ Ingestion Complete.")
        else:
            st.sidebar.error("Schema Mismatch.")
    except Exception as e:
        st.sidebar.error(f"Error parsing: {e}")
else:
    historical_data = fetch_analytics_data()
    if not historical_data.empty:
        active_data = historical_data

# ==============================================================================
# 4. MAIN INTERFACE LAYER
# ==============================================================================
st.title("Executive Performance Suite")
st.markdown("Real-time telemetry, transaction flows, and spatial financial distributions.")
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# FILTERS CONTAINER BLOCK
with st.container():
    f1, f2 = st.columns(2)
    with f1:
        locations = ["All Store Locations"] + list(active_data['store_location'].unique()) if not active_data.empty else ["All Store Locations"]
        selected_location = st.selectbox("Location Filter", locations)
    with f2:
        categories = ["All Categories"] + list(active_data['product_category'].unique()) if not active_data.empty else ["All Categories"]
        selected_category = st.selectbox("Department Vertical", categories)

# Apply runtime filters
filtered_data = active_data.copy()
if not filtered_data.empty:
    if selected_location != "All Store Locations":
        filtered_data = filtered_data[filtered_data['store_location'] == selected_location]
    if selected_category != "All Categories":
        filtered_data = filtered_data[filtered_data['product_category'] == selected_category]

has_data = not filtered_data.empty

# ==============================================================================
# ZONE 1: EXECUTIVE LEVEL KPIs
# ==============================================================================
total_sales = filtered_data['total_revenue'].sum() if has_data else 0.0
total_items = filtered_data['quantity'].sum() if has_data else 0
avg_order_val = filtered_data['total_revenue'].mean() if has_data else 0.0
top_performer = filtered_data.groupby('product_name')['total_revenue'].sum().idxmax() if has_data and len(filtered_data) > 0 else "None Active"

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.markdown(f"""
        <div class='metric-card'>
            <span class='material-icons-round card-icon'>payments</span>
            <div class='metric-lbl'>Gross System Revenue</div>
            <div class='metric-val'>${total_sales:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)
with kpi2:
    st.markdown(f"""
        <div class='metric-card'>
            <span class='material-icons-round card-icon'>inventory_2</span>
            <div class='metric-lbl'>Total Volume Sold</div>
            <div class='metric-val'>{total_items:,} <span style='font-size:0.9rem; font-weight:500; color:#64748b;'>pcs</span></div>
        </div>
    """, unsafe_allow_html=True)
with kpi3:
    st.markdown(f"""
        <div class='metric-card'>
            <span class='material-icons-round card-icon'>receipt_long</span>
            <div class='metric-lbl'>Avg Ticket Value</div>
            <div class='metric-val'>${avg_order_val:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)
with kpi4:
    st.markdown(f"""
        <div class='metric-card'>
            <span class='material-icons-round card-icon'>stars</span>
            <div class='metric-lbl'>MVP Capital Product</div>
            <div class='metric-val' style='font-size:1.35rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{top_performer}</div>
        </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# ZONE 2: GEO-SPATIAL MAP CARDS (FULL WIDTH LAYOUT)
# ==============================================================================
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown("### Global Revenue Footprint Vector")

with st.container():
    if has_data:
        map_df = filtered_data.groupby('store_location')['total_revenue'].sum().reset_index()
        map_df['lat'] = map_df['store_location'].map(lambda x: COORDINATE_REGISTRY.get(x, {}).get('lat', 0))
        map_df['lon'] = map_df['store_location'].map(lambda x: COORDINATE_REGISTRY.get(x, {}).get('lon', 0))
        map_df = map_df[(map_df['lat'] != 0) & (map_df['lon'] != 0)]
        
        fig_map = px.scatter_geo(
            map_df, lat='lat', lon='lon', size='total_revenue', hover_name='store_location',
            hover_data={'total_revenue': ':$,.2f', 'lat': False, 'lon': False},
            size_max=35, projection="natural earth", template="plotly_white"
        )
        fig_map.update_traces(marker=dict(color='#10b981', opacity=0.8, line=dict(width=1, color='#064e3b')))
        fig_map.update_geos(showland=True, landcolor="#f8fafc", showocean=True, oceancolor="#f0f9ff", showcountries=True, countrycolor="#cbd5e1")
    else:
        fig_map = px.scatter_geo(projection="natural earth", template="plotly_white")
        fig_map.update_geos(showland=True, landcolor="#f8fafc", showocean=True, oceancolor="#f0f9ff")
        
    fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=400)
    st.plotly_chart(fig_map, use_container_width=True, config={'displayModeBar': False})

# ==============================================================================
# ZONE 3: OPERATIONAL BREAKDOWN CHARTS (2-COLUMN BALANCED GRID)
# ==============================================================================
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
graph_col1, graph_col2 = st.columns(2)
mint_palette = ['#10b981', '#34d399', '#6ee7b7', '#a7f3d0', '#d1fae5']

with graph_col1:
    st.markdown("### Net Revenue Run Rate")
    trend_df = filtered_data.groupby('date')['total_revenue'].sum().reset_index().sort_values('date') if has_data else pd.DataFrame(columns=['date', 'total_revenue'])
    fig_trend = px.line(trend_df, x='date', y='total_revenue', markers=True, labels={'total_revenue': 'Revenue ($)', 'date': 'Timeline'}, template="plotly_white")
    fig_trend.update_traces(line_color='#10b981', line_width=3, marker=dict(size=8, color='#064e3b'))
    fig_trend.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300, xaxis_title=None, yaxis_title="Revenue ($)")
    st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})

with graph_col2:
    st.markdown("### Vertical Domain Distributions")
    cat_df = filtered_data.groupby('product_category')['total_revenue'].sum().reset_index() if has_data else pd.DataFrame(columns=['product_category', 'total_revenue'])
    fig_bar = px.bar(cat_df, x='product_category', y='total_revenue', labels={'total_revenue': 'Revenue ($)', 'product_category': 'Category'}, template="plotly_white", color_discrete_sequence=mint_palette)
    fig_bar.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300, xaxis_title=None, yaxis_title="Revenue ($)")
    st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

# Ledger Panel
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
with st.expander("Cryptographic SQL Ledger Record Audit"):
    st.dataframe(
        filtered_data, 
        use_container_width=True,
        column_config={
            "total_revenue": st.column_config.NumberColumn("Total Revenue", format="$%.2f"),
            "unit_price": st.column_config.NumberColumn("Unit Price", format="$%.2f"),
            "quantity": st.column_config.NumberColumn("Units")
        }
    )
