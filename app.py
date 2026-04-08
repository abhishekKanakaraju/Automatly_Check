from flask import Flask, render_template, request
import os
import hmac
import hashlib
import subprocess

app = Flask(__name__)

WEBHOOK_SECRET = "MDQ6VXNlcjc0MTM4NTAy"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/deploy", methods=["POST"])
def deploy():
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        return "Missing signature", 403

    payload = request.get_data()
    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        return "Invalid signature", 403

    try:
        subprocess.run(
            "cd /var/www/automatly && git pull origin main && systemctl restart automatly",
            shell=True,
            check=True
        )
        return "Deployed", 200
    except subprocess.CalledProcessError:
        return "Deploy failed", 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)