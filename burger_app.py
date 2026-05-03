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

# ====================== SIDEBAR ======================
page = st.sidebar.selectbox("בחר עמוד", 
    ["הזמנה חדשה", "ניהול תפריט", "היסטוריית הזמנות"])

# ====================== UTILS ======================
if 'current_order' not in st.session_state:
    st.session_state.current_order = []

def reset_order():
    st.session_state.current_order = []
    for key in ['group', 'phone', 'email', 'people', 'budget']:
        if key in st.session_state:
            del st.session_state[key]

# ====================== PAGES ======================
if page == "ניהול תפריט":
    st.subheader("ניהול התפריט")
    col1, col2 = st.columns([3,1])
    with col1:
        new_name = st.text_input("שם המוצר", key="new_name")
    with col2:
        new_price = st.number_input("מחיר ₪", min_value=0, value=0, step=1, key="new_price")
    
    if st.button("➕ הוסף מוצר"):
        if new_name:
            try:
                c.execute("INSERT INTO menu (name, price) VALUES (?, ?)", (new_name.strip(), new_price))
                conn.commit()
                st.success("✅ נוסף!")
                st.rerun()
            except:
                st.error("מוצר זה כבר קיים")

    st.subheader("תפריט נוכחי")
    df_menu = pd.read_sql("SELECT name as 'מוצר', price as 'מחיר ₪' FROM menu ORDER BY name", conn)
    st.dataframe(df_menu, use_container_width=True, hide_index=True)

elif page == "הזמנה חדשה":
    st.subheader("פרטי הקבוצה")
    
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("שם הקבוצה", key="group", placeholder="שם הקבוצה")
        st.text_input("טלפון", key="phone", placeholder="טלפון")
        st.text_input("מייל", key="email", placeholder="מייל")
    with col2:
        st.number_input("מספר סועדים", min_value=1, value=10, step=1, key="people")
        st.number_input("תקציב (₪)", min_value=0, value=1500, step=1, key="budget")
    
    st.subheader("תאריך ושעה")
    col3, col4 = st.columns(2)
    with col3:
        order_date = st.date_input("תאריך", datetime.date.today(), key="date")
    with col4:
        order_time = st.time_input("שעה", datetime.datetime.now().time(), key="time")

    # Add to order
    st.subheader("הוסף מוצרים")
    menu_df = pd.read_sql("SELECT name, price FROM menu", conn)
    
    if not menu_df.empty:
        product = st.selectbox("בחר מוצר", menu_df['name'], key="product_select")
        qty = st.number_input("כמות", min_value=1, value=1, step=1, key="qty_input")
        
        if st.button("➕ הוסף להזמנה"):
            price = menu_df[menu_df['name'] == product]['price'].values[0]
            st.session_state.current_order.append({
                "מוצר": product, "כמות": qty, "מחיר": price, "סה\"כ": price * qty
            })
            st.success(f"נוסף: {qty} × {product}")
            st.rerun()  # Reset quantity field

    # Current Order
    if st.session_state.current_order:
        df_order = pd.DataFrame(st.session_state.current_order)
        st.dataframe(df_order, use_container_width=True, hide_index=True)
        
        total = df_order["סה\"כ"].sum()
        tip_percent = st.radio("טיפ (%)", [10, 15, 20], horizontal=True, key="tip")
        tip_amount = total * (tip_percent / 100)
        final_total = total - tip_amount
        
        st.success(f"**סכום כולל: {total:.0f} ₪**")
        st.info(f"**טיפ: {tip_amount:.0f} ₪** | **סופי: {final_total:.0f} ₪**")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 שמור הזמנה", type="primary"):
                try:
                    c.execute("""INSERT INTO orders 
                        (group_name, phone, email, num_people, budget, order_date, order_time, 
                         total, tip_percent, tip_amount, final_total, created_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (st.session_state.get('group',''), st.session_state.get('phone',''), 
                         st.session_state.get('email',''), st.session_state.get('people',10), 
                         st.session_state.get('budget',1500), str(order_date), str(order_time),
                         total, tip_percent, tip_amount, final_total, datetime.datetime.now().isoformat()))
                    order_id = c.lastrowid
                    for item in st.session_state.current_order:
                        c.execute("INSERT INTO order_items (order_id, product_name, quantity, line_total) VALUES (?,?,?,?)",
                                 (order_id, item["מוצר"], item["כמות"], item["סה\"כ"]))
                    conn.commit()
                    st.success(f"✅ ההזמנה נשמרה! מספר: {order_id}")
                    reset_order()
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        
        with col2:
            if st.button("🗑️ נקה הזמנה"):
                reset_order()
                st.rerun()

elif page == "היסטוריית הזמנות":
    st.subheader("היסטוריית הזמנות")
    df = pd.read_sql("""
        SELECT id, group_name as 'קבוצה', order_date as 'תאריך', 
               num_people as 'סועדים', final_total as 'סכום סופי' 
        FROM orders ORDER BY created_at DESC
    """, conn)
    
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    if not df.empty:
        selected_id = st.selectbox("בחר הזמנה לפעולה", df['id'])
        col1, col2 = st.columns(2)
        with col1:
            if st.button("טען להזמנה"):
                st.info("פיצ'ר טעינה יורחב בהמשך")
        with col2:
            if st.button("🗑️ מחק הזמנה", type="secondary"):
                c.execute("DELETE FROM orders WHERE id=?", (selected_id,))
                c.execute("DELETE FROM order_items WHERE order_id=?", (selected_id,))
                conn.commit()
                st.success("