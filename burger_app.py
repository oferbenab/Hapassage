import streamlit as st
import sqlite3
import pandas as pd
import datetime

st.set_page_config(page_title="🍔 מערכת ניהול מסעדה", layout="wide")

# DB
conn = sqlite3.connect('hamburger.db', check_same_thread=False)
c = conn.cursor()

# Tables
c.execute('''
CREATE TABLE IF NOT EXISTS menu (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    price REAL
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT,
    phone TEXT,
    email TEXT,
    people INTEGER,
    budget REAL,
    total REAL,
    created_at TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    product_name TEXT,
    quantity INTEGER,
    price REAL
)
''')

conn.commit()

# Session
if "order" not in st.session_state:
    st.session_state.order = []

# Sidebar
page = st.sidebar.radio("ניווט", ["🆕 הזמנה חדשה", "📋 תפריט", "📊 היסטוריה"])

# ===============================
# 📋 MENU MANAGEMENT
# ===============================
if page == "📋 תפריט":

    st.title("📋 ניהול תפריט")

    col1, col2 = st.columns([3,1])

    with col1:
        name = st.text_input("שם מוצר")

    with col2:
        price = st.number_input("מחיר ₪", min_value=0)

    if st.button("➕ הוסף מוצר"):
        if name:
            c.execute("INSERT OR IGNORE INTO menu (name, price) VALUES (?,?)", (name, price))
            conn.commit()
            st.success("נוסף!")
            st.rerun()

    st.divider()

    search = st.text_input("🔍 חיפוש מוצר")

    df = pd.read_sql("SELECT * FROM menu", conn)

    if search:
        df = df[df["name"].str.contains(search, case=False)]

    for i, row in df.iterrows():
        col1, col2, col3 = st.columns([4,2,1])
        col1.write(row["name"])
        col2.write(f"₪ {row['price']}")
        if col3.button("❌", key=f"del{row['id']}"):
            c.execute("DELETE FROM menu WHERE id=?", (row["id"],))
            conn.commit()
            st.rerun()

# ===============================
# 🆕 NEW ORDER
# ===============================
elif page == "🆕 הזמנה חדשה":

    st.title("🆕 הזמנה חדשה")

    col1, col2 = st.columns(2)

    with col1:
        group = st.text_input("שם קבוצה")
        phone = st.text_input("טלפון")
        email = st.text_input("מייל")

    with col2:
        people = st.number_input("מספר סועדים", min_value=1)
        budget = st.number_input("תקציב ₪", min_value=0)

    st.divider()

    menu_df = pd.read_sql("SELECT * FROM menu", conn)

    if menu_df.empty:
        st.warning("אין מוצרים בתפריט")
    else:
        col1, col2, col3 = st.columns([3,1,1])

        product = col1.selectbox("בחר מוצר", menu_df["name"])
        qty = col2.number_input("כמות", min_value=1, value=1)

        if col3.button("➕"):
            price = menu_df[menu_df["name"] == product]["price"].values[0]

            st.session_state.order.append({
                "name": product,
                "qty": qty,
                "price": price,
                "total": price * qty
            })

            st.rerun()

    st.divider()

    # Order Table
    if st.session_state.order:

        st.subheader("🧾 ההזמנה")

        df = pd.DataFrame(st.session_state.order)

        for i, row in df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([3,1,1,1,1])

            col1.write(row["name"])
            new_qty = col2.number_input("", value=row["qty"], key=f"qty{i}")

            if new_qty != row["qty"]:
                st.session_state.order[i]["qty"] = new_qty
                st.session_state.order[i]["total"] = new_qty * row["price"]
                st.rerun()

            col3.write(f"₪ {row['price']}")
            col4.write(f"₪ {row['total']}")

            if col5.button("❌", key=f"remove{i}"):
                st.session_state.order.pop(i)
                st.rerun()

        total = sum(item["total"] for item in st.session_state.order)

        st.markdown(f"## 💰 סה\"כ: ₪ {total}")

        if budget and total > budget:
            st.error("⚠️ חרגת מהתקציב!")

        col1, col2 = st.columns(2)

        if col1.button("💾 שמור הזמנה"):

            c.execute("""
            INSERT INTO orders (group_name, phone, email, people, budget, total, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                group, phone, email, people, budget, total,
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            ))

            order_id = c.lastrowid

            for item in st.session_state.order:
                c.execute("""
                INSERT INTO order_items (order_id, product_name, quantity, price)
                VALUES (?, ?, ?, ?)
                """, (
                    order_id,
                    item["name"],
                    item["qty"],
                    item["total"]
                ))

            conn.commit()

            st.success("✅ נשמר בהצלחה!")

            st.session_state.order = []
            st.rerun()

        if col2.button("🗑️ נקה הכל"):
            st.session_state.order = []
            st.rerun()

# ===============================
# 📊 HISTORY
# ===============================
else:

    st.title("📊 היסטוריית הזמנות")

    df = pd.read_sql("SELECT * FROM orders ORDER BY id DESC", conn)

    if df.empty:
        st.info("אין הזמנות עדיין")
    else:
        st.dataframe(df, use_container_width=True)

        order_id = st.number_input("בחר הזמנה", min_value=1)

        if st.button("הצג פרטים"):
            items = pd.read_sql(f"""
            SELECT product_name as מוצר,
                   quantity as כמות,
                   price as סכום
            FROM order_items
            WHERE order_id = {order_id}
            """, conn)

            st.dataframe(items, use_container_width=True)