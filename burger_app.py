import streamlit as st
import sqlite3
import pandas as pd
import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

st.set_page_config(page_title="🍔 מסעדת המבורגר", layout="centered")

st.title("🍔 ניהול קבוצות סועדים")
st.markdown("### מערכת ניהול הזמנות למסעדה")

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

# ====================== SIDEBAR ======================
page = st.sidebar.selectbox("בחר עמוד", 
    ["הזמנה חדשה", "ניהול תפריט", "היסטוריית הזמנות"])

# ====================== MENU MANAGEMENT ======================
if page == "ניהול תפריט":
    st.subheader("ניהול התפריט")
    
    col1, col2 = st.columns([3,1])
    with col1:
        new_name = st.text_input("שם המוצר")
    with col2:
        new_price = st.number_input("מחיר ₪", min_value=0.0, step=1.0)
    
    if st.button("➕ הוסף מוצר"):
        if new_name:
            try:
                c.execute("INSERT INTO menu (name, price) VALUES (?, ?)", (new_name.strip(), new_price))
                conn.commit()
                st.success("✅ המוצר נוסף!")
            except:
                st.error("מוצר עם שם זה כבר קיים")
    
    st.subheader("תפריט נוכחי")
    df_menu = pd.read_sql("SELECT name as 'מוצר', price as 'מחיר ₪' FROM menu ORDER BY name", conn)
    st.dataframe(df_menu, use_container_width=True, hide_index=True)

# ====================== NEW ORDER ======================
elif page == "הזמנה חדשה":
    st.subheader("פרטי הקבוצה")
    col1, col2 = st.columns(2)
    with col1:
        group_name = st.text_input("שם הקבוצה *", key="group")
        phone = st.text_input("טלפון *", key="phone")
        email = st.text_input("מייל", key="email")
        num_people = st.number_input("מספר סועדים", min_value=1, value=10, key="people")
    with col2:
        budget = st.number_input("תקציב (₪)", min_value=0, value=1500, key="budget")
        order_date = st.date_input("תאריך", datetime.date.today(), key="date")
        order_time = st.time_input("שעה", datetime.datetime.now().time(), key="time")

    # Order items
    st.subheader("הוסף מוצרים להזמנה")
    menu_df = pd.read_sql("SELECT name, price FROM menu", conn)
    
    if not menu_df.empty:
        product = st.selectbox("בחר מוצר", menu_df['name'], key="product")
        qty = st.number_input("כמות", min_value=1, value=1, key="qty")
        
        if st.button("➕ הוסף להזמנה"):
            if 'current_order' not in st.session_state:
                st.session_state.current_order = []
            price = menu_df[menu_df['name'] == product]['price'].values[0]
            st.session_state.current_order.append({
                "מוצר": product,
                "כמות": qty,
                "מחיר": price,
                "סה\"כ": price * qty
            })
            st.rerun()

    # Show current order
    if 'current_order' in st.session_state and st.session_state.current_order:
        df_order = pd.DataFrame(st.session_state.current_order)
        st.dataframe(df_order, use_container_width=True, hide_index=True)
        
        total = df_order["סה\"כ"].sum()
        st.success(f"**סכום כולל: {total:.2f} ₪**")
        
        tip_percent = st.radio("טיפ", [10, 15, 20], horizontal=True, key="tip")
        tip_amount = total * (tip_percent / 100)
        final_total = total - tip_amount
        
        st.info(f"**סכום סופי: {final_total:.2f} ₪** (כולל טיפ {tip_percent}%)")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 שמור הזמנה", type="primary"):
                try:
                    c.execute("""INSERT INTO orders 
                        (group_name, phone, email, num_people, budget, order_date, order_time, 
                         total, tip_percent, tip_amount, final_total, created_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (group_name, phone, email, num_people, budget, str(order_date), str(order_time),
                         total, tip_percent, tip_amount, final_total, datetime.datetime.now().isoformat()))
                    
                    order_id = c.lastrowid
                    for item in st.session_state.current_order:
                        c.execute("INSERT INTO order_items (order_id, product_name, quantity, line_total) VALUES (?,?,?,?)",
                                 (order_id, item["מוצר"], item["כמות"], item["סה\"כ"]))
                    conn.commit()
                    st.success(f"✅ ההזמנה נשמרה! מספר: {order_id}")
                    del st.session_state.current_order
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        
        with col2:
            if st.button("נקה הזמנה"):
                if st.session_state.current_order:
                    del st.session_state.current_order
                    st.rerun()

# ====================== HISTORY ======================
else:
    st.subheader("היסטוריית הזמנות")
    df = pd.read_sql("""
        SELECT id, group_name as 'קבוצה', order_date as 'תאריך', 
               num_people as 'סועדים', final_total as 'סכום סופי' 
        FROM orders ORDER BY created_at DESC
    """, conn)
    st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()
st.caption("🍔 מערכת ניהול הזמנות - מסעדת המבורגר")