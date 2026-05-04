import streamlit as st
import sqlite3
import pandas as pd
import datetime
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="🍔 מערכת מסעדה", layout="wide")

# ===== DB =====
conn = sqlite3.connect('hamburger.db', check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS menu (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT UNIQUE,
price REAL)""")

c.execute("""CREATE TABLE IF NOT EXISTS orders (
id INTEGER PRIMARY KEY AUTOINCREMENT,
group_name TEXT,
phone TEXT,
email TEXT,
total REAL,
created_at TEXT)""")

c.execute("""CREATE TABLE IF NOT EXISTS order_items (
id INTEGER PRIMARY KEY AUTOINCREMENT,
order_id INTEGER,
product_name TEXT,
quantity INTEGER,
price REAL)""")

conn.commit()

# ===== SESSION =====
if "order" not in st.session_state:
    st.session_state.order = []

# ===== NAV =====
page = st.sidebar.radio("ניווט", ["🆕 קופה", "📋 תפריט", "📊 היסטוריה", "📄 חשבונית"])

if st.sidebar.button("⬅ חזור לקופה"):
    page = "🆕 קופה"

# ======================
# 🆕 POS SCREEN
# ======================
if page == "🆕 קופה":

    st.title("🍔 קופה")

    col1, col2 = st.columns([2,1])

    # ===== PRODUCTS =====
    with col1:
        st.subheader("מוצרים")

        menu_df = pd.read_sql("SELECT name, price FROM menu", conn)

        if menu_df.empty:
            st.warning("אין מוצרים בתפריט")
        else:
            cols = st.columns(3)
            for i, row in menu_df.iterrows():
                if cols[i % 3].button(f"{row['name']}\n₪{row['price']}"):
                    found = False
                    for item in st.session_state.order:
                        if item["name"] == row["name"]:
                            item["qty"] += 1
                            item["total"] = item["qty"] * item["price"]
                            found = True
                    if not found:
                        st.session_state.order.append({
                            "name": row["name"],
                            "qty": 1,
                            "price": row["price"],
                            "total": row["price"]
                        })
                    st.rerun()

    # ===== ORDER =====
    with col2:
        st.subheader("הזמנה")

        if st.session_state.order:
            df = pd.DataFrame(st.session_state.order)

            edited = st.data_editor(
                df[["name", "qty", "total"]],
                use_container_width=True,
                key="order_editor"
            )

            new = []
            for i, row in edited.iterrows():
                price = df.iloc[i]["price"]
                new.append({
                    "name": row["name"],
                    "qty": int(row["qty"]),
                    "price": price,
                    "total": int(row["qty"]) * price
                })

            st.session_state.order = new

            total = sum(x["total"] for x in new)
            st.markdown(f"## 💰 ₪ {total}")

            group = st.text_input("שם לקוח")
            phone = st.text_input("טלפון")

            if st.button("💾 סגור הזמנה"):
                c.execute("""INSERT INTO orders
                (group_name, phone, email, total, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (group, phone, "", total,
                 datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))

                oid = c.lastrowid

                for item in new:
                    c.execute("""INSERT INTO order_items
                    (order_id, product_name, quantity, price)
                    VALUES (?, ?, ?, ?)""",
                    (oid, item["name"], item["qty"], item["total"]))

                conn.commit()

                st.success("נשמר!")
                st.session_state.order = []
                st.rerun()

# ======================
# 📋 MENU
# ======================
elif page == "📋 תפריט":

    st.title("ניהול תפריט")

    df = pd.read_sql("SELECT id, name, price FROM menu", conn)

    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)

    if st.button("💾 שמור"):
        c.execute("DELETE FROM menu")
        for _, row in edited.iterrows():
            if pd.notna(row["name"]):
                c.execute("INSERT INTO menu (id, name, price) VALUES (?, ?, ?)",
                          (row["id"], row["name"], row["price"]))
        conn.commit()
        st.success("נשמר!")

# ======================
# 📊 HISTORY
# ======================
elif page == "📊 היסטוריה":

    st.title("היסטוריה")

    orders = pd.read_sql("SELECT * FROM orders ORDER BY id DESC", conn)
    st.dataframe(orders)

    if not orders.empty:
        selected = st.selectbox("בחר הזמנה", orders["id"])

        items = pd.read_sql(
            "SELECT product_name, quantity, price FROM order_items WHERE order_id = ?",
            conn,
            params=(selected,)
        )

        st.dataframe(items)

        if st.button("🔄 טען להזמנה"):
            st.session_state.order = [
                {
                    "name": r["product_name"],
                    "qty": r["quantity"],
                    "price": r["price"] / r["quantity"],
                    "total": r["price"]
                }
                for _, r in items.iterrows()
            ]
            st.success("נטען!")

# ======================
# 📄 PDF
# ======================
elif page == "📄 חשבונית":

    st.title("חשבונית")

    if not st.session_state.order:
        st.warning("אין הזמנה")
    else:
        file = "invoice.pdf"
        doc = SimpleDocTemplate(file, pagesize=A4)
        styles = getSampleStyleSheet()

        elements = []

        elements.append(Paragraph("חשבונית", styles["Title"]))
        elements.append(Paragraph(str(datetime.datetime.now()), styles["Normal"]))
        elements.append(Spacer(1, 15))

        data = [["מוצר", "כמות", "סכום"]]

        for item in st.session_state.order:
            data.append([item["name"], item["qty"], item["total"]])

        total = sum(x["total"] for x in st.session_state.order)
        data.append(["", "סה\"כ", total])

        table = Table(data)
        table.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 1, colors.black)]))

        elements.append(table)
        doc.build(elements)

        with open(file, "rb") as f:
            st.download_button("📥 הורד PDF", f, file_name="invoice.pdf")