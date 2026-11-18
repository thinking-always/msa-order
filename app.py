import os

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

PRODUCT_URL = os.getenv("PRODUCT_URL", "<http://product>")
PAYMENT_URL = os.getenv("PAYMENT_URL", "<http://payment>")

ORDERS = []


@app.route("/api/orders", methods=["GET"])
def list_orders():
    return jsonify(ORDERS)


@app.route("/api/orders", methods=["POST"])
def create_order():
    data = request.get_json(silent=True) or {}
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    if product_id is None:
        return jsonify(error="product_id is required"), 400

    # 1. 재고 확인 (product)
    try:
        res = requests.get(f"{PRODUCT_URL}/api/products/{product_id}", timeout=2)
    except requests.RequestException:
        return jsonify(error="product service unavailable"), 502

    if res.status_code == 404:
        return jsonify(error="product not found"), 404
    if res.status_code != 200:
        return jsonify(error="product service error"), 502

    product = res.json()
    if product["stock"] < quantity:
        return jsonify(error="out of stock"), 409

    # 2. 결제 (payment)
    amount = product["price"] * quantity
    try:
        pay = requests.post(f"{PAYMENT_URL}/pay", json={"amount": amount}, timeout=2)
    except requests.RequestException:
        return jsonify(error="payment service unavailable"), 502

    if pay.status_code != 200:
        return jsonify(error="payment failed"), 502

    # 3. 주문 저장
    order = {
        "id": len(ORDERS) + 1,
        "product_id": product_id,
        "quantity": quantity,
        "amount": amount,
        "status": "paid",
        "test": "ok",
    }
    ORDERS.append(order)
    return jsonify(order), 201


@app.route("/healthz")
def healthz():
    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)