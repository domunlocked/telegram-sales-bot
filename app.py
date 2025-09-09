import os
import json
from flask import Flask, request, render_template_string
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ======================
# Configuration
# ======================
TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")  # set in Render
bot = Bot(token=TOKEN)

app = Flask(__name__)

# JSON file to store sales
SALES_FILE = "sales.json"
if not os.path.exists(SALES_FILE):
    with open(SALES_FILE, "w") as f:
        json.dump([], f)


# ======================
# Telegram Handlers
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Send me your sales data in format: item, amount")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        item, amount = text.split(",")
        sale = {"item": item.strip(), "amount": float(amount.strip()), "time": update.message.date.isoformat()}

        # Save to file
        with open(SALES_FILE, "r") as f:
            sales = json.load(f)
        sales.append(sale)
        with open(SALES_FILE, "w") as f:
            json.dump(sales, f)

        await update.message.reply_text(f"✅ Recorded sale: {sale['item']} - {sale['amount']}")
    except Exception:
        await update.message.reply_text("❌ Invalid format. Use: item, amount")


# ======================
# Flask Dashboard
# ======================
@app.route("/")
def dashboard():
    with open(SALES_FILE, "r") as f:
        sales = json.load(f)

    total = sum(s["amount"] for s in sales)

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sales Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            table { border-collapse: collapse; width: 100%; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f4f4f4; }
        </style>
    </head>
    <body>
        <h1>Sales Dashboard</h1>
        <h2>Total Sales: {{ total }}</h2>
        <table>
            <tr><th>Item</th><th>Amount</th><th>Time</th></tr>
            {% for sale in sales %}
            <tr>
                <td>{{ sale["item"] }}</td>
                <td>{{ sale["amount"] }}</td>
                <td>{{ sale["time"] }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(html, sales=sales, total=total)


# ======================
# Telegram Webhook
# ======================
@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    app_telegram.update_queue.put_nowait(update)
    return "OK", 200


# ======================
# Run Telegram + Flask
# ======================
def main():
    global app_telegram
    app_telegram = Application.builder().token(TOKEN).build()

    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start polling in background
    app_telegram.run_polling(stop_signals=None)


if __name__ == "__main__":
    main()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
