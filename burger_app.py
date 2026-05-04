import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, time
import json

# --- הגדרות דף ---
st.set_page_config(page_title="Passaz Pro POS", layout="wide", initial_sidebar_state="collapsed")

# --- CSS מתקדם למערכת מסעדות ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;700&display=swap');
    * { font-family: 'Assistant', sans-serif; direction: rtl; }
    .stApp { background-color: #f8f9fa; }
    
    /* כפתור איפוס עליון מעוצב כ-Action Bar */
    .main-action-btn { 
        background: linear-gradient(90deg, #ff4b4b, #ff7676);
        color: white; border-radius: 8px; padding: 10px;
        text-align: center; margin-bottom: 20px; cursor: pointer;
    }
    
    /* עיצוב טבלת היסטוריה חסינת מובייל */
    .history-row {
        background: white; border-radius: 10px; padding: 12px;
        margin-bottom: 10px; border-right: 5px solid #0083B8;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* ביטול גלילה מיותרת */
    .stTabs [data-baseweb="tab-list"] { background-color: white; border-radius: 10px; padding: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- תשתית נתונים (SQL) ---
def init_db():
    conn = sqlite3.connect('restaurant_pro.db', check_same_thread=False)
    c = conn.cursor()
    # תפריט
    c.execute('CREATE TABLE IF NOT EXISTS menu (id INTEGER PRIMARY KEY, item TEXT, price INTEGER, category TEXT)')
    # הזמנות משוכללות
    c.execute('''CREATE TABLE IF NOT EXISTS orders 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  cust_name TEXT, event_date TEXT, total INTEGER, 
                  status TEXT, raw_cart TEXT, cust_data TEXT, notes TEXT)''')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- פונקציות מערכת ---
def reset_system():
    for key in ['cart', 'nm', 'ph', 'em', 'gs', 'ppg', 'bd', 'notes']:
        if key == 'cart': st.session_state[key] = []
        elif key in ['gs', 'ppg', 'bd']: st.session_state[key] = None
        else: st.session_state[key] = ""
    st.session_state.q_idx += 100

def load_to_system(order_id):
    c.execute("SELECT raw_cart, cust_data FROM orders WHERE id=?", (order_id,))
    res = c.fetchone()
    if res:
        st.session_state.cart = json.loads(res[0])
        data = json.loads(res[1])
        for k, v in data.items(): st.session_state[k] = v
        st.toast("הזמנה שוחזרה בהצלחה")

# --- ניהול Session ---
if 'cart' not in st.session_state: st.session_state.cart = []
if 'q_idx' not in st.session_state: st.session_state.q_idx = 0
for k in ['nm', 'ph', 'em', 'gs', 'ppg', 'bd', 'notes']:
    if k not in st.session_state: st.session_state[k] = None if k in ['gs', 'ppg', 'bd'] else ""

# --- ממשק משתמש (UI) ---

# כפתור עליון - תמיד נגיש
if st.button("🆕 פתח הזמנה / לקוח חדש", use_container_width=True, type="primary"):
    reset_system()
    st.rerun()

tab_order, tab_history, tab_admin = st.tabs(["🍽️ ניהול הזמנה", "📊 יומן אירועים", "⚙️ הגדרות מערכת"])

# --- טאב 1: הזמנה ---
with tab_order:
    col_info, col_cart = st.columns([1, 1])
    
    with col_info:
        with st.container(border=True):
            st.subheader("👤 פרטי הלקוח")
            st.session_state.nm = st.text_input("שם מלא", value=st.session_state.nm, placeholder="למי ההזמנה?")
            c_p1, c_p2 = st.columns(2)
            st.session_state.ph = c_p1.text_input("טלפון", value=st.session_state.ph)
            st.session_state.em = c_p2.text_input("אימייל", value=st.session_state.em)
            
            st.subheader("🗓️ פרטי האירוע")
            c_d1, c_d2 = st.columns(2)
            ev_date = c_d1.date_input("תאריך", datetime.now())
            ev_time = c_d2.time_input("שעת התחלה", time(20, 0))
            
            c_n1, c_n2, c_n3 = st.columns(3)
            st.session_state.gs = c_n1.number_input("אורחים", min_value=1, step=1, value=st.session_state.gs)
            st.session_state.ppg = c_n2.number_input("מחיר לסועד", min_value=0, step=1, value=st.session_state.ppg)
            st.session_state.bd = c_n3.number_input("תקציב יעד", min_value=0, step=1, value=st.session_state.bd)
            
            st.session_state.notes = st.text_area("הערות מטבח / לוגיסטיקה", value=st.session_state.notes)

    with col_cart:
        with st.container(border=True):
            st.subheader("🛒 סל מוצרים")
            m_items = pd.read_sql_query("SELECT item, price FROM menu", conn)
            if not m_items.empty:
                c_sel, c_q, c_btn = st.columns([3, 1, 1])
                choice = c_sel.selectbox("בחר פריט", m_items['item'].tolist(), label_visibility="collapsed")
                qty = c_q.number_input("כמות", min_value=1, step=1, value=None, key=f"q_{st.session_state.q_idx}")
                if c_btn.button("הוסף", use_container_width=True):
                    if qty:
                        p = int(m_items[m_items['item'] == choice]['price'].values[0])
                        st.session_state.cart.append({"פריט": choice, "כמות": qty, "מחיר": p, "סה''כ": qty*p})
                        st.rerun()

            if st.session_state.cart:
                df_cart = pd.DataFrame(st.session_state.cart)
                st.dataframe(df_cart, use_container_width=True, hide_index=True)
                
                # סיכום כספי
                gs = st.session_state.gs or 0
                ppg = st.session_state.ppg or 0
                subtotal = df_cart["סה''כ"].sum() + (gs * ppg)
                
                st.divider()
                tip_p = st.select_slider("שירות / טיפ", options=[0, 10, 12, 15, 18], value=12)
                tip_shk = int(subtotal * (tip_p/100))
                grand_total = subtotal + tip_shk
                
                m1, m2 = st.columns(2)
                m1.metric("סה''כ לתשלום", f"{grand_total:,} ₪")
                if st.session_state.bd:
                    m2.metric("תקציב לקוח", f"{st.session_state.bd:,} ₪", delta=int(st.session_state.bd - grand_total))
                
                if st.button("✅ אישור ושמירת הזמנה", type="primary", use_container_width=True):
                    raw_c = json.dumps(st.session_state.cart)
                    raw_cust = json.dumps({k: st.session_state[k] for k in ['nm', 'ph', 'em', 'gs', 'ppg', 'bd', 'notes']})
                    f_dt = f"{ev_date.strftime('%d/%m/%Y')} {ev_time.strftime('%H:%M')}"
                    c.execute("INSERT INTO orders (cust_name, event_date, total, status, raw_cart, cust_data, notes) VALUES (?,?,?,?,?,?,?)",
                             (st.session_state.nm, f_dt, grand_total, "פעיל", raw_c, raw_cust, st.session_state.notes))
                    conn.commit()
                    st.success("הזמנה ננעלה במערכת")

# --- טאב 2: היסטוריה וחיפוש ---
with tab_history:
    search_q = st.text_input("🔎 חיפוש מהיר (שם לקוח או תאריך)", placeholder="הקלד לחיפוש...")
    all_orders = pd.read_sql_query("SELECT id, cust_name, event_date, total, status FROM orders ORDER BY id DESC", conn)
    
    if not all_orders.empty:
        if search_q:
            all_orders = all_orders[all_orders['cust_name'].str.contains(search_q, na=False, case=False)]
        
        for _, row in all_orders.iterrows():
            with st.container():
                # בניית שורה אופקית קשיחה בעזרת HTML
                st.markdown(f"""
                <div class="history-row">
                    <table style="width:100%; border-collapse: collapse;">
                        <tr>
                            <td style="width:30%;"><b>{row['cust_name']}</b></td>
                            <td style="width:30%; font-size: 0.8em;">{row['event_date']}</td>
                            <td style="width:20%; color: green; font-weight: bold;">{row['total']:,} ₪</td>
                        </tr>
                    </table>
                </div>
                """, unsafe_allow_html=True)
                
                btn_col1, btn_col2, _ = st.columns([1, 1, 4])
                if btn_col1.button("🔄 טען", key=f"l_{row['id']}"):
                    load_to_system(row['id'])
                    st.rerun()
                if btn_col2.button("🗑️", key=f"d_{row['id']}"):
                    c.execute("DELETE FROM orders WHERE id=?", (row['id'],))
                    conn.commit()
                    st.rerun()
                st.write("") # מרווח
    else:
        st.info("אין הזמנות רשומות במערכת")

# --- טאב 3: הגדרות תפריט ---
with tab_admin:
    st.subheader("🍴 ניהול תפריט ומחירים")
    menu_data = pd.read_sql_query("SELECT * FROM menu", conn)
    edited_menu = st.data_editor(menu_data, column_config={"id": None}, num_rows="dynamic", use_container_width=True, hide_index=True)
    
    if st.button("💾 שמור עדכוני תפריט"):
        c.execute("DELETE FROM menu")
        for _, r in edited_menu.iterrows():
            if r['item']:
                c.execute("INSERT INTO menu (item, price) VALUES (?,?)", (r['item'], int(r['price'])))
        conn.commit()
        st.success("התפריט עודכן בהצלחה")
