import os
import json
from flask import Flask, request, render_template_string, redirect, url_for
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import datetime

# Load token from environment variable
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Flask app
app = Flask(__name__)

# Telegram app
application = Application.builder().token(TOKEN).build()

# JSON storage
SALES_FILE = "sales.json"
if not os.path.exists(SALES_FILE):
    with open(SALES_FILE, "w") as f:
        json.dump([], f)


# ---------------- Telegram Commands ----------------
async def start(update: Update, context):
    await update.message.reply_text("🤖 Hello! Send me sales like: Apple 5000")


async def add_sale(update: Update, context):
    text = update.message.text.strip()
    parts = text.rsplit(" ", 1)
    if len(parts) == 2 and parts[1].isdigit():
        item, price = parts
        price = int(parts[1])

        sale = {
            "item": item,
            "price": price,
            "currency": "៛",
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        with open(SALES_FILE, "r+") as f:
            data = json.load(f)
            data.append(sale)
            f.seek(0)
            json.dump(data, f, indent=2)

        await update.message.reply_text(f"✅ Added sale: {item} {price:,} ៛")
    else:
        await update.message.reply_text("❌ Format: ItemName 5000")


application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_sale))


# ---------------- Flask Routes ----------------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"


@app.route("/")
def dashboard():
    with open(SALES_FILE) as f:
        sales = json.load(f)

    total = sum(s["price"] for s in sales)

    html = """
    <h1>📊 Sales Dashboard</h1>
    <form method="post" action="/add">
        <input name="item" placeholder="Item" required>
        <input name="price" type="number" placeholder="Price (៛)" required>
        <button type="submit">Add Sale</button>
    </form>
    <h2>Total: {{ total:, }} ៛</h2>
    <ul>
        {% for s in sales %}
            <li>{{ s["time"] }} - {{ s["item"] }} - {{ s["price"]:, }} ៛</li>
        {% endfor %}
    </ul>
    """
    return render_template_string(html, sales=sales, total=total)


@app.route("/add", methods=["POST"])
def add_sale_form():
    item = request.form["item"]
    price = int(request.form["price"])
    sale = {
        "item": item,
        "price": price,
        "currency": "៛",
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    with open(SALES_FILE, "r+") as f:
        data = json.load(f)
        data.append(sale)
        f.seek(0)
        json.dump(data, f, indent=2)

    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
