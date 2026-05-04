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

    col1, col2, col3 = st.columns([4,2,1])

    new_name = col1.text_input("מוצר חדש")
    new_price = col2.number_input("מחיר", min_value=0)

    if col3.button("➕"):
        if new_name:
            c.execute("INSERT OR IGNORE INTO menu (name, price) VALUES (?,?)", (new_name, new_price))
            conn.commit()
            st