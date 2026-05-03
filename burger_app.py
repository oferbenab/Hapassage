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
conn.commit()

# Sidebar
page = st.sidebar.selectbox("בחר עמוד", 
    ["הזמנה חדשה", "ניהול תפריט", "היסטוריה"])

if page == "ניהול תפריט":
    st.subheader("הוסף מוצר")
    name = st.text_input("שם המוצר")
    price = st.number_input("מחיר ₪", min_value=0.0, step=1.0)
    if st.button("הוסף"):
        try:
            c.execute("INSERT INTO menu (name, price) VALUES (?, ?)", (name, price))
            conn.commit()
            st.success("נוסף בהצלחה!")
        except:
            st.error("מוצר כבר קיים")

    st.subheader("התפריט")
    df = pd.read_sql("SELECT name as 'מוצר', price as 'מחיר ₪' FROM menu", conn)
    st.dataframe(df, use_container_width=True)

elif page == "הזמנה חדשה":
    st.subheader("פרטי הקבוצה")
    col1, col2 = st.columns(2)
    with col1:
        group = st.text_input("שם הקבוצה")
        phone = st.text_input("טלפון")
        people = st.number_input("מספר סועדים", 1, 100, 10)
    with col2:
        budget = st.number_input("תקציב ₪", 0, 10000, 1500)
        order_date = st.date_input("תאריך", datetime.date.today())
        order_time = st.time_input("שעה", datetime.datetime.now().time())

    # Order
    st.subheader("הוסף מוצרים")
    menu_df = pd.read_sql("SELECT name, price FROM menu", conn)
    if not menu_df.empty:
        product = st.selectbox("בחר מוצר", menu_df['name'])
        qty = st.number_input("כמות", 1, 50, 1)
        if st.button("הוסף להזמנה"):
            st.success(f"נוסף: {qty} × {product}")

    if st.button("💾 שמור הזמנה"):
        st.success("הזמנה נשמרה! (גרסה בסיסית)")

else:
    st.subheader("היסטוריה")
    st.info("היסטוריה תופיע כאן (בגרסה מלאה)")

st.caption("אפליקציית מסעדת המבורגר")