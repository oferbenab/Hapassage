import streamlit as st
import sqlite3
import pandas as pd
import datetime

st.set_page_config(page_title="🍔 מסעדת המבורגר", layout="centered")

st.title("🍔 ניהול קבוצות סועדים")

# Database
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

# Session
if 'current_order' not in st.session_state:
    st.session_state.current_order = []

def reset_order():
    st.session_state.current_order = []
    for key in ['group', 'phone', 'email', 'people', 'budget']:
        if key in st.session_state:
            del st.session_state[key]

page = st.sidebar.selectbox("בחר עמוד", ["הזמנה חדשה", "ניהול תפריט", "היסטוריה"])

if page == "ניהול תפריט":
    st.subheader("ניהול תפריט")
    col1, col2 = st.columns([3,1])
    with col1:
        st.write("**שם המוצר**")
        name = st.text_input(" ", placeholder="שם המוצר", label_visibility="collapsed")
    with col2:
        st.write("**מחיר ₪**")
        price = st.number_input(" ", min_value=0, value=0, step=1, label_visibility="collapsed")
    
    if st.button("➕ הוסף מוצר"):
        if name:
            c.execute("INSERT OR IGNORE INTO menu (name, price) VALUES (?, ?)", (name, price))
            conn.commit()
            st.success("נוסף!")
            st.rerun()

    st.subheader("תפריט נוכחי")
    df = pd.read_sql("SELECT name as 'מוצר', price as 'מחיר ₪' FROM menu", conn)
    st.dataframe(df, use_container_width=True, hide_index=True)

elif page == "הזמנה חדשה":
    st.subheader("פרטי הקבוצה")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**שם הקבוצה**")
        st.text_input(" ", key="group", placeholder="שם הקבוצה", label_visibility="collapsed")
        st.write("**טלפון**")
        st.text_input(" ", key="phone", placeholder="טלפון", label_visibility="collapsed")
        st.write("**מייל**")
        st.text_input(" ", key="email", placeholder="מייל", label_visibility="collapsed")
    with col2:
        st.write("**מספר סועדים**")
        st.number_input(" ", min_value=1, value=None, step=1, key="people", label_visibility="collapsed")
        st.write("**תקציב (₪)**")
        st.number_input(" ", min_value=0, value=None, step=1, key="budget", label_visibility="collapsed")

    st.subheader("תאריך ושעה")
    col3, col4 = st.columns(2)
    with col3:
        st.date_input("תאריך", datetime.date.today(), key="date")
    with col4:
        st