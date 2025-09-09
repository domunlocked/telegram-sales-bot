import os
import json
from flask import Flask, render_template_string, request, redirect, url_for
from telegram.ext import Application, CommandHandler, MessageHandler, filters

app = Flask(__name__)

DATA_FILE = "sales.json"
TOKEN = os.getenv("TELEGRAM_TOKEN")  # Load from Render environment variable

# =======================
# Helpers
# =======================
def load_sales():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_sales(sales):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(sales, f, ensure_ascii=False, indent=2)

# =======================
# Telegram Bot
# =======================
async def start(update, context):
    await update.message.reply_text("សួស្តី 🙏 បញ្ចូលការលក់ ដោយប្រើ៖\n\n`Item, Qty, Price`")

async def add_sale(update, context):
    try:
        text = update.message.text.strip()
        item, qty, price = text.split(",")
        qty, price = int(qty), int(price)
        total = qty * price

        sales = load_sales()
        sales.append({"item": item, "qty": qty, "price": price, "total": total})
        save_sales(sales)

        await update.message.reply_text(
            f"✅ បានរក្សាទុក: {item} x {qty} = {total} រៀល"
        )
    except Exception as e:
        await update.message.reply_text("❌ សូមប្រើទម្រង់: Item, Qty, Price")

def run_bot():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_sale))
    application.run_polling()

# =======================
# Flask Web Dashboard
# =======================
@app.route("/", methods=["GET", "POST"])
def dashboard():
    if request.method == "POST":
        item = request.form["item"]
        qty = int(request.form["qty"])
        price = int(request.form["price"])
        total = qty * price

        sales = load_sales()
        sales.append({"item": item, "qty": qty, "price": price, "total": total})
        save_sales(sales)

        return redirect(url_for("dashboard"))

    sales = load_sales()
    labels = [s["item"] for s in sales]
    totals = [s["total"] for s in sales]

    return render_template_string("""
    <html>
    <head>
        <title>Sales Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <h1>📊 Sales Dashboard</h1>

        <form method="POST">
            Item: <input name="item" required>
            Qty: <input name="qty" type="number" required>
            Price: <input name="price" type="number" required>
            <button type="submit">Add Sale</button>
        </form>

        <h2>Sales Records</h2>
        <table border="1" cellpadding="5">
            <tr><th>Item</th><th>Qty</th><th>Price (រៀល)</th><th>Total (រៀល)</th></tr>
            {% for s in sales %}
            <tr>
                <td>{{ s.item }}</td>
                <td>{{ s.qty }}</td>
                <td>{{ s.price }}</td>
                <td>{{ s.total }}</td>
            </tr>
            {% endfor %}
        </table>

        <h2>Sales Chart</h2>
        <canvas id="salesChart"></canvas>
        <script>
        const ctx = document.getElementById('salesChart');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: {{ labels|tojson }},
                datasets: [{
                    label: 'Total (រៀល)',
                    data: {{ totals|tojson }},
                    backgroundColor: 'rgba(75, 192, 192, 0.6)'
                }]
            }
        });
        </script>
    </body>
    </html>
    """, sales=sales, labels=labels, totals=totals)

# =======================
# Run both Flask + Bot
# =======================
if __name__ == "__main__":
    import threading

    # Run Telegram bot in background
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    # Run Flask app
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
