<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🍔 מסעדת המבורגר</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 15px; background: #f5f5f5; }
        h1 { text-align: center; color: #d32f2f; }
        .section { background: white; padding: 15px; margin: 12px 0; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        input, select, button { width: 100%; padding: 14px; margin: 8px 0; font-size: 17px; border-radius: 10px; border: 1px solid #ddd; }
        button { background: #d32f2f; color: white; font-weight: bold; border: none; }
        button:active { background: #b71c1c; }
        .item { background: #f9f9f9; padding: 12px; margin: 8px 0; border-radius: 10px; display: flex; justify-content: space-between; }
        .total { font-size: 20px; font-weight: bold; text-align: center; margin: 15px 0; color: #d32f2f; }
        
        /* Popup */
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 1000; }
        .modal-content { background: white; margin: 15% auto; padding: 20px; width: 80%; max-width: 350px; border-radius: 15px; text-align: center; }
        .modal button { margin: 10px 5px; width: auto; padding: 12px 20px; }
    </style>
</head>
<body>
    <h1>🍔 ניהול קבוצות סועדים</h1>

    <div class="section">
        <h2>פרטי הקבוצה</h2>
        <input type="text" id="group" placeholder="שם הקבוצה" />
        <input type="tel" id="phone" placeholder="טלפון" />
        <input type="email" id="email" placeholder="מייל" />
        <input type="number" id="people" placeholder="מספר סועדים" value="10" />
        <input type="number" id="budget" placeholder="תקציב (₪)" value="1500" />
        
        <h3>תאריך ושעה</h3>
        <input type="date" id="orderDate" />
        <input type="time" id="orderTime" />
    </div>

    <div class="section">
        <h2>תפריט</h2>
        <input type="text" id="newProduct" placeholder="שם מוצר חדש" />
        <input type="number" id="newPrice" placeholder="מחיר" step="1" />
        <button onclick="addToMenu()">➕ הוסף לתפריט</button>
        
        <select id="productSelect" style="margin-top:10px;"></select>
        <input type="number" id="qty" value="1" />
        <button onclick="addToOrder()">➕ הוסף להזמנה</button>
    </div>

    <div class="section">
        <h2>ההזמנה הנוכחית</h2>
        <div id="orderList"></div>
        <div class="total" id="totalDisplay">סכום כולל: 0 ₪</div>
        
        <label>טיפ: 
            <select id="tip" onchange="calculateTotal()">
                <option value="10">10%</option>
                <option value="15" selected>15%</option>
                <option value="20">20%</option>
            </select>
        </label>
        <div id="finalTotal" class="total"></div>
    </div>

    <div class="section">
        <button onclick="saveOrder()">💾 שמור הזמנה</button>
        <button onclick="showPDFModal()">📄 יצא PDF</button>
        <button onclick="clearOrder()">🗑️ נקה</button>
    </div>

    <div class="section">
        <h2>היסטוריה</h2>
        <div id="history"></div>
    </div>

    <!-- PDF Modal -->
    <div id="pdfModal" class="modal">
        <div class="modal-content">
            <h3>בחר סוג דף PDF</h3>
            <button onclick="exportPDF('manager')">📋 PDF מנהל (מלא)</button><br>
            <button onclick="exportPDF('kitchen')">👨‍🍳 PDF מטבח (כמויות)</button><br>
            <button onclick="exportPDF('customer')">👤 PDF ללקוח (ללא מחירים)</button><br><br>
            <button onclick="closeModal()" style="background:gray;">סגור</button>
        </div>
    </div>

    <script>
        let order = [];
        let menu = JSON.parse(localStorage.getItem('menu')) || [
            {name: "המבורגר קלאסי", price: 52},
            {name: "צ'יפס גדול", price: 32},
            {name: "קולה", price: 18},
            {name: "סלט ירוק", price: 35}
        ];

        function setDefaultDateTime() {
            const now = new Date();
            document.getElementById('orderDate').value = now.toISOString().split('T')[0];
            document.getElementById('orderTime').value = now.toTimeString().slice(0,5);
        }

        function saveMenu() { localStorage.setItem('menu', JSON.stringify(menu)); }
        
        function updateMenuSelect() {
            let select = document.getElementById('productSelect');
            select.innerHTML = '';
            menu.forEach(item => {
                let opt = document.createElement('option');
                opt.value = item.name;
                opt.textContent = `${item.name} - ${item.price} ₪`;
                select.appendChild(opt);
            });
        }

        function addToMenu() {
            let name = document.getElementById('newProduct').value.trim();
            let price = parseFloat(document.getElementById('newPrice').value);
            if (name && price) {
                menu.push({name, price});
                saveMenu();
                updateMenuSelect();
                alert('✅ נוסף לתפריט');
            }
        }

        function addToOrder() {
            let name = document.getElementById('productSelect').value;
            let qty = parseInt(document.getElementById('qty').value);
            let item = menu.find(m => m.name === name);
            if (item) {
                order.push({product: name, qty: qty, price: item.price, line: item.price * qty});
                renderOrder();
            }
        }

        function renderOrder() {
            let html = '', total = 0;
            order.forEach((item, i) => {
                html += `<div class="item">${item.qty} × ${item.product} <span>${item.line.toFixed(0)} ₪ 
                         <button onclick="removeItem(${i})" style="color:red;">🗑️</button></span></div>`;
                total += item.line;
            });
            document.getElementById('orderList').innerHTML = html;
            document.getElementById('totalDisplay').innerHTML = `סכום כולל: ${total.toFixed(0)} ₪`;
            calculateTotal();
        }

        function removeItem(i) { order.splice(i, 1); renderOrder(); }
        function calculateTotal() {
            let subtotal = order.reduce((sum, item) => sum + item.line, 0);
            let tipPercent = parseInt(document.getElementById('tip').value);
            let tip = subtotal * (tipPercent / 100);
            let final = subtotal - tip;
            document.getElementById('finalTotal').innerHTML = `טיפ (${tipPercent}%): ${tip.toFixed(0)} ₪<br><strong>סופי: ${final.toFixed(0)} ₪</strong>`;
        }

        // ====================== PDF Modal ======================
        function showPDFModal() {
            if (order.length === 0) {
                alert("אין פריטים בהזמנה");
                return;
            }
            document.getElementById('pdfModal').style.display = "block";
        }

        function closeModal() {
            document.getElementById('pdfModal').style.display = "none";
        }

        function exportPDF(type) {
            closeModal();
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF();
            let y = 20;

            doc.setFont("helvetica", "bold");
            doc.setFontSize(20);
            doc.text("מסעדת המבורגר", 105, y, { align: "center" });
            y += 15;

            doc.setFontSize(14);
            doc.text(`שם קבוצה: ${document.getElementById('group').value || 'לא צוין'}`, 20, y); y += 10;
            doc.text(`טלפון: ${document.getElementById('phone').value || 'לא צוין'}`, 20, y); y += 10;
            doc.text(`תאריך: ${document.getElementById('orderDate').value}`, 20, y); y += 10;
            doc.text(`שעה: ${document.getElementById('orderTime').value}`, 20, y); y += 15;

            let total = 0;
            order.forEach(item => {
                if (type === "kitchen") {
                    doc.text(`${item.qty} × ${item.product}`, 20, y);
                } else {
                    doc.text(`${item.qty} × ${item.product}`, 20, y);
                    doc.text(`${item.line.toFixed(0)} ₪`, 170, y, { align: "right" });
                }
                y += 10;
                total += item.line;
            });

            let tipPercent = parseInt(document.getElementById('tip').value);
            let tip = total * (tipPercent / 100);
            let final = total - tip;

            if (type !== "kitchen") {
                y += 10;
                doc.text(`סכום ביניים: ${total.toFixed(0)} ₪`, 20, y); y += 10;
                doc.text(`טיפ (${tipPercent}%): ${tip.toFixed(0)} ₪`, 20, y); y += 10;
                doc.setFont("helvetica", "bold");
                doc.text(`סכום סופי: ${final.toFixed(0)} ₪`, 20, y);
            }

            const fileName = `הזמנה_${document.getElementById('group').value || 'ללא_שם'}_${type}.pdf`;
            doc.save(fileName);
        }

        function saveOrder() {
            if (order.length === 0) return alert("ההזמנה ריקה");
            let orders = JSON.parse(localStorage.getItem('orders')) || [];
            orders.unshift({
                id: Date.now(),
                group: document.getElementById('group').value || "קבוצה",
                date: document.getElementById('orderDate').value,
                time: document.getElementById('orderTime').value,
                total: order.reduce((sum, item) => sum + item.line, 0),
                items: [...order]
            });
            localStorage.setItem('orders', JSON.stringify(orders));
            alert('✅ ההזמנה נשמרה!');
            loadHistory();
        }

        function loadHistory() {
            let orders = JSON.parse(localStorage.getItem('orders')) || [];
            let html = orders.map(o => 
                `<div class="item">${o.date} ${o.time} - ${o.group} - ${o.total} ₪</div>`
            ).join('');
            document.getElementById('history').innerHTML = html || "<p>אין הזמנות עדיין</p>";
        }

        function clearOrder() {
            if (confirm("לנקות את ההזמנה?")) {
                order = [];
                renderOrder();
            }
        }

        // Init
        updateMenuSelect();
        setDefaultDateTime();
        loadHistory();
    </script>
</body>
</html>