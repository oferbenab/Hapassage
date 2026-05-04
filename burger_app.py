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

# ======================
# 📋 MENU (טבלה מלאה)
# ======================
if page == "📋 תפריט":

    st.title("📋 ניהול תפריט")

    df = pd.read_sql("SELECT id, name, price FROM menu", conn)

    edited = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        key="menu_editor"
    )

    # שמירה
    if st.button("💾 שמור שינויים"):
        c.execute("DELETE FROM menu")
        for _, row in edited.iterrows():
            if pd.notna(row["name"]):
                c.execute(
                    "INSERT INTO menu (id, name, price) VALUES (?, ?, ?)",
                    (row["id"], row["name"], row["price"])
                )
        conn.commit()
        st.success("נשמר!")

# ======================
# 🆕 NEW ORDER
# ======================
elif page == "🆕 הזמנה חדשה":

    st.title("🆕 הזמנה חדשה")

    group = st.text_input("שם קבוצה")
    phone = st.text_input("טלפון")
    email = st.text_input("מייל")
    people = st.number_input("מספר סועדים", min_value=1)
    budget = st.number_input("תקציב ₪", min_value=0)

    st.divider()

    menu_df = pd.read_sql("SELECT name, price FROM menu", conn)

    if not menu_df.empty:
        product = st.selectbox("בחר מוצר", menu_df["name"])
        qty = st.number_input("כמות", min_value=1, value=1)

        if st.button("➕ הוסף"):
            price = menu_df[menu_df["name"] == product]["price"].values[0]

            st.session_state.order.append({
                "name": product,
                "qty": qty,
                "price": price,
                "total": price * qty
            })
            st.rerun()

    # ===== ORDER TABLE
    if st.session_state.order:

        df = pd.DataFrame(st.session_state.order)

        df_display = df[["name", "qty", "total"]].rename(columns={
            "name": "מוצר",
            "qty": "כמות",
            "total": "סכום"
        })

        edited_df = st.data_editor(
            df_display,
            use_container_width=True,
            key="order_editor"
        )

        # עדכון
        new_order = []
        for i, row in edited_df.iterrows():
            price = df.iloc[i]["price"]
            new_order.append({
                "name": row["מוצר"],
                "qty": int(row["כמות"]),
                "price": price,
                "total": int(row["כמות"]) * price
            })

        st.session_state.order = new_order

        total = sum(x["total"] for x in st.session_state.order)
        st.markdown(f"## 💰 סה\"כ: ₪ {total}")

        if budget and total > budget:
            st.error("⚠️ חרגת מהתקציב!")

        if st.button("💾 שמור הזמנה"):

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
            st.session_state.order = []
            st.success("נשמר!")

# ======================
# 📊 HISTORY (טבלאות מסודרות)
# ======================
elif page == "📊 היסטוריה":

    st.title("📊 היסטוריה")

    orders = pd.read_sql("SELECT * FROM orders ORDER BY id DESC", conn)

    st.dataframe(orders, use_container_width=True)

    order_id = st.number_input("בחר ID להזמנה", min_value=1)

    if st.button("הצג פרטים"):
        items = pd.read_sql(f"""
        SELECT product_name as מוצר,
               quantity as כמות,
               price as סכום
        FROM order_items
        WHERE order_id = {order_id}
        """, conn)

        st.data_editor(items, use_container_width=True)

# ======================
# 📄 PDF
# ======================
elif page == "📄 PDF":

    st.title("📄 ייצוא")

    if not st.session_state.order:
        st.warning("אין הזמנה")
    else:
        text = "הזמנה:\n\n"

        for item in st.session_state.order:
            text += f"{item['name']} | {item['qty']} | ₪ {item['total']}\n"

        total = sum(x["total"] for x in st.session_state.order)
        text += f"\nסה\"כ: ₪ {total}"

        st.download_button("📥 הורד", text, file_name="order.txt")