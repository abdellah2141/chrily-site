
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, url_for
from werkzeug.utils import secure_filename
import os
from bs4 import BeautifulSoup
import requests

app = Flask(__name__)
app.secret_key = 'chrily_secret_123'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

FIXED_SHIPPING = 5.0
USD_TO_MRU = 39.5
headers = {'User-Agent': 'Mozilla/5.0'}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/admin")
def admin_panel():
    upload_dir = os.path.join('static', 'uploads')
    orders = []
    if os.path.exists(upload_dir):
        for file in os.listdir(upload_dir):
            if file.lower().endswith((".png", ".jpg", ".jpeg")):
                parts = file.split("__")
                method = parts[0] if len(parts) > 1 else "غير معروف"
                import time
                timestamp = os.path.getmtime(os.path.join(upload_dir, file))
                date_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(timestamp))
                orders.append({'filename': file, 'method': method, 'date': date_str})
    return render_template("admin.html", orders=orders)

@app.route("/api/fetch", methods=["POST"])
def fetch_product():
    url = request.json.get("url")
    if not url:
        return jsonify({'error': 'رابط غير صالح'}), 400

    title, image, base_price = extract_product_data(url)
    if base_price == 0.0:
        return jsonify({'error': 'لم يتم استخراج السعر'}), 500

    total_usd = base_price * 1.10 + FIXED_SHIPPING
    total_mru = total_usd * USD_TO_MRU
    return jsonify({
        "title": title,
        "image": image,
        "price_usd": total_usd,
        "price_mru": total_mru
    })

@app.route("/api/submit-order", methods=["POST"])
def submit_order():
    method = request.form.get("method")
    screenshot = request.files.get("screenshot")
    if not method or not screenshot:
        return jsonify({'error': 'يرجى تحديد وسيلة الدفع ورفع صورة'}), 400

    filename = secure_filename(f"{method}__{screenshot.filename}")
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    screenshot.save(path)
    return jsonify({'success': True})

def extract_product_data(url):
    try:
        if "amazon." in url or "souq." in url:
            return "منتج من أمازون", "", 25
        elif "noon.com" in url:
            return "منتج من نون", "", 20
        elif "aliexpress.com" in url:
            return "منتج من علي إكسبرس", "", 18
        elif "temu.com" in url:
            return extract_from_temu(url)
        elif "shein.com" in url:
            return extract_from_shein(url)
        else:
            return "رابط غير مدعوم", "", 0.0
    except Exception as e:
        return f"خطأ: {e}", "", 0.0

def extract_from_temu(url):
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, "html.parser")
    title = soup.find("meta", property="og:title")
    image = soup.find("meta", property="og:image")
    price = soup.find("meta", property="product:price:amount")
    return (
        title["content"] if title else "منتج من Temu",
        image["content"] if image else "",
        float(price["content"]) if price else 0.0
    )

def extract_from_shein(url):
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, "html.parser")
    title = soup.find("meta", property="og:title")
    image = soup.find("meta", property="og:image")
    price = soup.find("meta", property="product:price:amount")
    return (
        title["content"] if title else "منتج من Shein",
        image["content"] if image else "",
        float(price["content"]) if price else 0.0
    )

if __name__ == "__main__":
    app.run(debug=True)


@app.route("/policies")
def policies():
    return render_template("policies.html")

@app.route("/save-phone", methods=["POST"])
def save_phone():
    phone = request.form.get("phone")
    if phone:
        session["user_phone"] = phone
        return jsonify({"success": True})
    return jsonify({"error": "رقم الهاتف غير موجود"}), 400

@app.route("/my-orders")
def my_orders():
    phone = session.get("user_phone")
    if not phone:
        return redirect(url_for("login"))

    upload_dir = os.path.join('static', 'uploads')
    orders = []
    if os.path.exists(upload_dir):
        for file in os.listdir(upload_dir):
            if phone in file:  # ربط الطلبات بالهاتف المدخل
                parts = file.split("__")
                method = parts[0] if len(parts) > 1 else "غير معروف"
                import time
                timestamp = os.path.getmtime(os.path.join(upload_dir, file))
                date_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(timestamp))
                orders.append({'filename': file, 'method': method, 'date': date_str})
    return render_template("my-orders.html", phone=phone, orders=orders)
