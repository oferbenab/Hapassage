import streamlit as st
import sqlite3
import pandas as pd
import datetime

st.set_page_config(page_title="🍔 מסעדת המבורגר", layout="centered")

st.title("🍔 ניהול קבוצות סועדים")

conn = sqlite3.connect('hamburger.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS menu (id INTEGER PRIMARY KEY, name TEXT UNIQUE, price REAL)''')
conn.commit()

# Sidebar
page = st.sidebar.selectbox("בחר עמוד", 
    ["הזמנה חדשה", "ניהול תפריט", "היסטוריה", "ייצוא PDF"])

# Session State
if 'current_order' not in st.session_state:
    st.session_state.current_order = []

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
            c.execute("INSERT OR IGNORE INTO menu (name, price) VALUES (?, ?)", (new_name, new_price))
            conn.commit()
            st.success("✅ נוסף!")
            st.rerun()

    st.subheader("תפריט נוכחי")
    df = pd.read_sql("SELECT name as 'מוצר', price as 'מחיר ₪' FROM menu", conn)
    st.dataframe(df, use_container_width=True)

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

    # הוספת מוצרים
    st.subheader("הוסף מוצרים")
    menu_df = pd.read_sql("SELECT name, price FROM menu", conn)
    if not menu_df.empty:
        st.markdown("**בחר מוצר**")
        product = st.selectbox("", menu_df['name'], key="product")
        st.markdown("**כמות**")
        qty = st.number_input("", min_value=1, value=1, step=1, key="qty")
        
        if st.button("➕ הוסף להזמנה"):
            price = menu_df[menu_df['name'] == product]['price'].values[0]
            st.session_state.current_order.append({
                "מוצר": product,
                "כמות": qty,
                "סכום": price * qty
            })
            st.success(f"נוסף: {qty} × {product}")
            st.rerun()

    # הצגת ההזמנה
    if st.session_state.current_order:
        st.subheader("ההזמנה הנוכחית")
        df_order = pd.DataFrame(st.session_state.current_order)
        st.dataframe(df_order, use_container_width=True, hide_index=True)

    if st.button("💾 שמור הזמנה"):
        st.success("✅ ההזמנה נשמרה!")

elif page == "ייצוא PDF":
    st.subheader("ייצוא PDF")
    st.info("בחר סוג PDF:\n• PDF מנהל\n• PDF מטבח\n• PDF ללקוח")

else:
    st.subheader("היסטוריה")
    st.info("היסטוריה תופיע כאן")

st.divider()
st.caption("🍔 מסעדת המבורגר")