import streamlit as st
import sqlite3
import pandas as pd
import datetime

st.set_page_config(page_title="🍔 מערכת ניהול מסעדה", layout="wide")

# ======================
# DB
# ======================
conn = sqlite3.connect('hamburger.db', check_same_thread=False)
c = conn.cursor()

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

# ======================
# SESSION
# ======================
if "order" not in st.session_state:
    st.session_state.order = []

# ======================
# SIDEBAR
# ======================
page = st.sidebar.radio("ניווט", [
    "🆕 הזמנה חדשה",
    "📋 תפריט",
    "📊 היסטוריה",
    "📄 PDF"
])

if st.sidebar.button("⬅ חזור להזמנה"):
    st.session_state.page_override = "🆕 הזמנה חדשה"

if "page_override" in st.session_state:
    page = st.session_state.page_override
    del st.session_state.page_override

# ======================
# 📋 MENU
# ======================
if page == "📋 תפריט":

    st.title("📋 ניהול תפריט")

    col1, col2 = st.columns([3,1])
    name = col1.text_input("שם מוצר חדש")
    price = col2.number_input("מחיר ₪", min_value=0)

    if st.button("➕ הוסף מוצר"):
        if name:
            c.execute("INSERT OR IGNORE INTO menu (name, price) VALUES (?,?)", (name, price))
            conn.commit()
            st.rerun()

    st.divider()

    df = pd.read_sql("SELECT * FROM menu", conn)

    for i, row in df.iterrows():
        col1, col2, col3, col4 = st.columns([4,2,1,1])

        new_name = col1.text_input("", value=row["name"], key=f"name{i}")
        new_price = col2.number_input("", value=row["price"], key=f"price{i}")

        if col3.button("💾", key=f"save{i}"):
            c.execute("UPDATE menu SET name=?, price=? WHERE id=?",
                      (new_name, new_price, row["id"]))
            conn.commit()
            st.rerun()

        if col4.button("❌", key=f"del{i}"):
            c.execute("DELETE FROM menu WHERE id=?", (row["id"],))
            conn.commit()
            st.rerun()

# ======================
# 🆕 NEW ORDER
# ======================
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

        if col3.button("➕ הוסף"):
            price = menu_df[menu_df["name"] == product]["price"].values[0]

            st.session_state.order.append({
                "name": product,
                "qty": qty,
                "price": price,
                "total": price * qty
            })

            st.rerun()

    st.divider()

    # ===== ORDER TABLE (שורה אחת לכל פריט)
    if st.session_state.order:

        st.subheader("🧾 ההזמנה")

        for i, item in enumerate(st.session_state.order):

            col1, col2, col3, col4 = st.columns([4,2,2,1])

            col1.write(item["name"])

            new_qty = col2.number_input(
                "כמות",
                min_value=1,
                value=item["qty"],
                key=f"qty_{i}"
            )

            if new_qty != item["qty"]:
                st.session_state.order[i]["qty"] = new_qty
                st.session_state.order[i]["total"] = new_qty * item["price"]
                st.rerun()

            col3.markdown(f"💰 ₪ {item['total']}")

            if col4.button("❌", key=f"del_item_{i}"):
                st.session_state.order.pop(i)
                st.rerun()

        total = sum(x["total"] for x in st.session_state.order)

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

# ======================
# 📊 HISTORY
# ======================
elif page == "📊 היסטוריה":

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

# ======================
# 📄 PDF (בסיסי)
# ======================
elif page == "📄 PDF":

    st.title("📄 ייצוא PDF")

    if not st.session_state.order:
        st.warning("אין הזמנה להדפסה")
    else:
        text = "הזמנה:\n\n"

        for item in st.session_state.order:
            text += f"{item['name']} x{item['qty']} - ₪ {item['total']}\n"

        total = sum(x["total"] for x in st.session_state.order)
        text += f"\nסה\"כ: ₪ {total}"

        st.download_button(
            "📥 הורד קובץ",
            text,
            file_name="order.txt"
        )