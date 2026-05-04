import streamlit as st
import sqlite3
import pandas as pd
import datetime
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="🍔 מערכת ניהול מסעדה", layout="wide")

# ======================
# DB INIT
# ======================
conn = sqlite3.connect('hamburger.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS menu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    price REAL
)''')

c.execute('''CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT,
    phone TEXT,
    email TEXT,
    total REAL,
    created_at TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    product_name TEXT,
    quantity INTEGER,
    total REAL
)''')

conn.commit()

# ======================
# SESSION
# ======================
if "order" not in st.session_state:
    st.session_state.order = []

if "group" not in st.session_state:
    st.session_state.group = ""
    st.session_state.phone = ""
    st.session_state.email = ""

# ======================
# SIDEBAR
# ======================
page = st.sidebar.radio("ניווט", ["🆕 הזמנה", "📋 תפריט", "📊 היסטוריה", "📄 PDF"])

if st.sidebar.button("⬅ חזור להזמנה"):
    page = "🆕 הזמנה"

# ======================
# 📋 MENU
# ======================
if page == "📋 תפריט":

    st.title("📋 ניהול תפריט")

    df = pd.read_sql("SELECT * FROM menu", conn)

    edited = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True
    )

    if st.button("💾 שמור שינויים"):
        for _, row in edited.iterrows():
            if pd.isna(row["id"]):
                c.execute("INSERT INTO menu (name, price) VALUES (?,?)",
                          (row["name"], row["price"]))
            else:
                c.execute("UPDATE menu SET name=?, price=? WHERE id=?",
                          (row["name"], row["price"], row["id"]))
        conn.commit()
        st.success("התפריט עודכן")

# ======================
# 🆕 ORDER
# ======================
elif page == "🆕 הזמנה":

    st.title("🧾 הזמנה")

    st.session_state.group = st.text_input("שם קבוצה", st.session_state.group)
    st.session_state.phone = st.text_input("טלפון", st.session_state.phone)
    st.session_state.email = st.text_input("מייל", st.session_state.email)

    menu_df = pd.read_sql("SELECT name, price FROM menu", conn)

    if not menu_df.empty:
        col1, col2, col3 = st.columns([4,1,1])
        product = col1.selectbox("מוצר", menu_df["name"])
        qty = col2.number_input("כמות", min_value=1, value=1)

        if col3.button("➕"):
            price = menu_df[menu_df["name"] == product]["price"].values[0]
            st.session_state.order.append({
                "name": product,
                "qty": qty,
                "price": price,
                "total": price * qty
            })

    # ===== TABLE
    if st.session_state.order:
        df = pd.DataFrame(st.session_state.order)

        edited = st.data_editor(
            df[["name", "qty", "total"]],
            use_container_width=True
        )

        new_order = []
        for i, row in edited.iterrows():
            price = df.iloc[i]["price"]
            new_order.append({
                "name": row["name"],
                "qty": int(row["qty"]),
                "price": price,
                "total": int(row["qty"]) * price
            })

        st.session_state.order = new_order

        total = sum(x["total"] for x in new_order)
        st.markdown(f"## 💰 סה\"כ: ₪ {total}")

        if st.button("💾 שמור הזמנה"):
            c.execute("""INSERT INTO orders
            (group_name, phone, email, total, created_at)
            VALUES (?, ?, ?, ?, ?)""",
            (
                st.session_state.group,
                st.session_state.phone,
                st.session_state.email,
                total,
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            ))

            oid = c.lastrowid

            for item in new_order:
                c.execute("""INSERT INTO order_items
                (order_id, product_name, quantity, total)
                VALUES (?, ?, ?, ?)""",
                (oid, item["name"], item["qty"], item["total"]))

            conn.commit()
            st.success("ההזמנה נשמרה")

# ======================
# 📊 HISTORY
# ======================
elif page == "📊 היסטוריה":

    st.title("📊 היסטוריה")

    orders = pd.read_sql("SELECT * FROM orders ORDER BY id DESC", conn)
    st.dataframe(orders, use_container_width=True)

    selected = st.selectbox("בחר הזמנה", orders["id"])

    if selected:

        items = pd.read_sql(
            "SELECT product_name, quantity, total FROM order_items WHERE order_id=?",
            conn,
            params=(selected,)
        )

        st.dataframe(items, use_container_width=True)

        if st.button("🔄 טען להזמנה"):
            st.session_state.order = [
                {
                    "name": r["product_name"],
                    "qty": r["quantity"],
                    "price": r["total"] / r["quantity"],
                    "total": r["total"]
                }
                for _, r in items.iterrows()
            ]

            order_info = orders[orders["id"] == selected].iloc[0]
            st.session_state.group = order_info["group_name"]
            st.session_state.phone = order_info["phone"]
            st.session_state.email = order_info["email"]

            st.success("ההזמנה נטענה לעריכה")

# ======================
# 📄 PDF
# ======================
elif page == "📄 PDF":

    st.title("📄 הפקת חשבונית")

    if not st.session_state.order:
        st.warning("אין הזמנה")
    else:

        file = "invoice.pdf"
        doc = SimpleDocTemplate(file, pagesize=A4)
        styles = getSampleStyleSheet()

        elements = []

        elements.append(Paragraph("Invoice", styles["Title"]))
        elements.append(Spacer(1, 10))

        elements.append(Paragraph(f"Customer: {st.session_state.group}", styles["Normal"]))
        elements.append(Paragraph(f"Phone: {st.session_state.phone}", styles["Normal"]))
        elements.append(Paragraph(f"Email: {st.session_state.email}", styles["Normal"]))
        elements.append(Paragraph(f"Date: {datetime.datetime.now()}", styles["Normal"]))

        elements.append(Spacer(1, 20))

        data = [["Product", "Qty", "Total"]]

        for item in st.session_state.order:
            data.append([item["name"], item["qty"], item["total"]])

        total = sum(x["total"] for x in st.session_state.order)
        data.append(["", "סה\"כ", total])

        table = Table(data)
        table.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 1, colors.black),
            ("BACKGROUND", (0,0), (-1,0), colors.grey)
        ]))

        elements.append(table)

        doc.build(elements)

        with open(file, "rb") as f:
            st.download_button("📥 הורד PDF", f, file_name="invoice.pdf")