import streamlit as st
import sqlite3
import pandas as pd
import datetime

st.set_page_config(page_title="🍔 מסעדת המבורגר", layout="centered", initial_sidebar_state="expanded")

st.title("🍔 ניהול קבוצות סועדים - מסעדת המבורגר")

# ====================== DATABASE ======================
conn = sqlite3.connect('hamburger.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS menu (id INTEGER PRIMARY KEY, name TEXT UNIQUE, price REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY, group_name TEXT, phone TEXT, email TEXT, num_people INTEGER,
    budget REAL, order_date TEXT, order_time TEXT, total REAL, tip_percent INTEGER,
    tip_amount REAL, final_total REAL, created_at TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY, order_id INTEGER, product_name TEXT, quantity INTEGER, line_total REAL)''')
conn.commit()

# ====================== SESSION ======================
if 'current_order' not in st.session_state:
    st.session_state.current_order = []

def reset_order():
    st.session_state.current_order = []
    for key in ['group', 'phone', 'email', 'people', 'budget']:
        if key in st.session_state:
            del st.session_state[key]

# ====================== SIDEBAR ======================
page = st.sidebar.selectbox("בחר עמוד", 
    ["הזמנה חדשה", "ניהול תפריט", "היסטוריה", "ייצוא PDF"])

# ====================== MENU ======================
if page == "ניהול תפריט":
    st.subheader("ניהול התפריט")
    col1, col2 = st.columns([3,1])
    with col1:
        st.markdown("**שם המוצר**")
        name = st.text_input("", placeholder="שם המוצר", label_visibility="collapsed")
    with col2:
        st.markdown("**מחיר ₪**")
        price = st.number_input("", min_value=0, value=0, step=1, label_visibility="collapsed")
    
    if st.button("➕ הוסף מוצר"):
        if name:
            try:
                c.execute("INSERT INTO menu (name, price) VALUES (?, ?)", (name.strip(), price))
                conn.commit()
                st.success("✅ נוסף!")
                st.rerun()
            except:
                st.error("מוצר כבר קיים")

    st.subheader("תפריט נוכחי")
    df_menu = pd.read_sql("SELECT name as 'מוצר', price as 'מחיר ₪' FROM menu ORDER BY name", conn)
    st.dataframe(df_menu, use_container_width=True, hide_index=True)

# ====================== NEW ORDER ======================
elif page == "הזמנה חדשה":
    st.subheader("פרטי הקבוצה")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**שם הקבוצה**")
        st.text_input("", key="group", placeholder="שם הקבוצה", label_visibility="collapsed")
        st.markdown("**טלפון**")
        st.text_input("", key="phone", placeholder="טלפון", label_visibility="collapsed")
        st.markdown("**מייל**")
        st.text_input("", key="email", placeholder="מייל", label_visibility="collapsed")
    with col2:
        st.markdown("**מספר סועדים**")
        st.number_input("", min_value=1, value=None, step=1, key="people", label_visibility="collapsed")
        st.markdown("**תקציב (₪)**")
        st.number_input("", min_value=0, value=None, step=1, key="budget", label_visibility="collapsed")

    st.subheader("תאריך ושעה")
    col3, col4 = st.columns(2)
    with col3:
        st.date_input("תאריך", datetime.date.today(), key="date")
    with col4:
        st.time_input("שעה", datetime.datetime.now().time(), key="time")

    # Add items
    st.subheader("הוסף מוצרים")
    menu_df = pd.read_sql("SELECT name, price FROM menu", conn)
    if not menu_df.empty:
        st.markdown("**בחר מוצר**")
        product = st.selectbox("", menu_df['name'], key="product")
        st.markdown("**כמות**")
        qty = st.number_input("", min_value=1, value=1, step=1, key="qty")
        
        if st.button("➕ הוסף להזמנה"):