from flask import Flask, render_template, request, redirect, url_for, session
import os
import time

app = Flask(__name__)
app.secret_key = 'chrily_secret_123'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route("/save-phone", methods=["POST"])
def save_phone():
    phone = request.form.get("phone")
    if phone:
        session["user_phone"] = phone
        return "تم الحفظ"
    return "فشل"

@app.route("/my-orders")
def my_orders():
    phone = session.get("user_phone")
    if not phone:
        return redirect(url_for("login"))

    upload_dir = os.path.join('static', 'uploads')
    orders = []
    if os.path.exists(upload_dir):
        for file in os.listdir(upload_dir):
            if phone in file:
                parts = file.split("__")
                method = parts[0] if len(parts) > 1 else "غير معروف"
                timestamp = os.path.getmtime(os.path.join(upload_dir, file))
                date_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(timestamp))
                orders.append({'filename': file, 'method': method, 'date': date_str})
    return render_template("my-orders.html", phone=phone, orders=orders)