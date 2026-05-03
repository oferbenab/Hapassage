import streamlit as st
import sqlite3
import pandas as pd
import datetime

st.set_page_config(page_title="🍔 מסעדת המבורגר", layout="centered")

st.title("🍔 ניהול קבוצות סועדים")

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

# ====================== SESSION STATE ======================
if 'current_order' not in st.session_state:
    st.session_state.current_order = []

def reset_new_order():
    for key in list(st.session_state.keys()):
        if key not in ['current_order']:
            del st.session_state[key]
    st.session_state.current_order = []

# ====================== SIDEBAR ======================
page = st.sidebar.selectbox("בחר עמוד", ["הזמנה חדשה", "ניהול תפריט", "היסטוריית הזמנות"])

# ====================== PAGES ======================
if page == "ניהול תפריט":
    st.subheader("ניהול התפריט")
    col1, col2 = st.columns([3,1])
    with col1:
        st.markdown("**שם המוצר**")
        new_name = st.text_input("", placeholder="שם המוצר", label_visibility="collapsed")
    with col2:
        st.markdown("**מחיר ₪**")
        new_price = st.number_input("", min_value=0, value=0, step=1, label_visibility="collapsed")
    
    if st.button("➕ הוסף מוצר"):
        if new_name:
            try:
                c.execute("INSERT INTO menu (name, price) VALUES (?, ?)", (new_name.strip(), new_price))
                conn.commit()
                st.success("✅ נוסף!")
                st.rerun()
            except:
                st.error("מוצר כבר קיים")

    st.subheader("תפריט נוכחי")
    df_menu = pd.read_sql("SELECT name as 'מוצר', price as 'מחיר ₪' FROM menu ORDER BY name", conn)
    st.dataframe(df_menu, use_container_width=True, hide_index=True)

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
        st.number_input("", min_value=1, value=10, step=1, key="people", label_visibility="collapsed")
        st.markdown("**תקציב (₪)**")
        st.number_input("", min_value=0, value=1500, step=1, key="budget", label_visibility="collapsed")

    st.subheader("תאריך ושעה")
    col3, col4 = st.columns(2)
    with col3:
        st.date_input("תאריך", datetime.date.today(), key="date")
    with col4:
        st.time_input("שעה", datetime.datetime.now().time(), key="time")

    # הוספת מוצרים
    st.subheader("הוסף מוצרים")
    menu_df = pd.read_sql("SELECT name, price FROM menu", conn)
    if not menu_df.empty:
        st.markdown("**בחר מוצר**")
        product = st.selectbox("", menu_df['name'], key="product_select", label_visibility="collapsed")
        st.markdown("**כמות**")
        qty = st.number_input("", min_value=1, value=1, step=1, key="qty_input", label_visibility="collapsed")
        
        if st.button("➕ הוסף להזמנה"):
            price = menu_df[menu_df['name'] == product]['price'].values[0]
            st.session_state.current_order.append({
                "מוצר": product, "כמות": qty, "מחיר": price, "סה\"כ": price * qty
            })
            st.success(f"נוסף: {qty} × {product}")
            st.rerun()  # מאפס את שדה הכמות

    # הזמנה נוכחית
    if st.session_state.current_order:
        df_order = pd.DataFrame(st.session_state.current_order)
        st.dataframe(df_order, use_container_width=True, hide_index=True)
        
        total = df_order["סה\"