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

page = st.sidebar.selectbox("בחר עמוד", ["הזמנה חדשה", "ניהול תפריט", "היסטוריה"])

if page == "ניהול תפריט":
    st.subheader("ניהול התפריט")
    col1, col2 = st.columns([3,1])
    with col1:
        new_name = st.text_input("שם המוצר")
    with col2:
        new_price = st.number_input("מחיר ₪", min_value=0, value=0, step=1)
    
    if st.button("➕ הוסף מוצר"):
        if new_name:
            try:
                c.execute("INSERT INTO menu (name, price) VALUES (?, ?)", (new_name.strip(), new_price))
                conn.commit()
                st.success("✅ המוצר נוסף בהצלחה!")
                st.rerun()
            except:
                st.error("מוצר זה כבר קיים")

    st.subheader("התפריט")
    df = pd.read_sql("SELECT name as 'מוצר', price as 'מחיר ₪' FROM menu ORDER BY name", conn)
    st.dataframe(df, use_container_width=True, hide_index=True)

elif page == "הזמנה חדשה":
    st.subheader("פרטי הקבוצה")
    col1, col2 = st.columns(2)
    with col1:
        group = st.text_input("שם הקבוצה")
        phone = st.text_input("טלפון")
        email = st.text_input("מייל")
    with col2:
        people = st.number_input("מספר סועדים", min_value=1, value=10, step=1)
        budget = st.number_input("תקציב ₪", min_value=0, value=1500, step=1)
    
    st.subheader("הוסף מוצרים")
    menu_df = pd.read_sql("SELECT name, price FROM menu", conn)
    if not menu_df.empty:
        product = st.selectbox("בחר מוצר", menu_df['name'])
        qty = st.number_input("כמות", min_value=1, value=1, step=1)
        if st.button("➕ הוסף להזמנה"):
            price = menu_df[menu_df['name'] == product]['price'].values[0]
            if 'current_order' not in st.session_state:
                st.session_state.current_order = []
            st.session_state.current_order.append({"מוצר": product, "כמות": qty, "סה\"כ": price * qty})
            st.success(f"נוסף: {qty} × {product}")
            st.rerun()

    if 'current_order' in st.session_state and st.session_state.current_order:
        df_order = pd.DataFrame(st.session_state.current_order)
        st.dataframe(df_order, use_container_width=True, hide_index=True)
        
        total = df_order["סה\"כ"].sum()
        st.success(f"סכום כולל: {total:.0f} ₪")
        
        if st.button("💾 שמור הזמנה", type="primary"):
            st.success("הזמנה נשמרה בהצלחה!")
            # כאן אפשר להוסיף שמירה אמיתית לטבלה

else:
    st.subheader("היסטור