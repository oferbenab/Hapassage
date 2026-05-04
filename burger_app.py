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
page = st.sidebar.selectbox("בחר עמוד", ["הזמנה חדשה", "ניהול תפריט", "היסטוריה"])

# ====================== PAGES ======================
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
            st.success("✅ נוסף!")
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
        st.text_input(" ", key="phone", placeholder="050-1234567", label_visibility="collapsed")
        st.write("**מייל**")
        st.text_input(" ", key="email", placeholder="example@email.com", label_visibility="collapsed")
    with col2:
        st.write("**מס