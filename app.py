from flask import Flask, render_template, request
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
    sig = request.headers.get("X-Hub-Signature-256")
    if not sig:
        return "missing signature", 403

    body = request.get_data()
    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(sig, expected):
        return "invalid signature", 403

    event = request.headers.get("X-GitHub-Event", "")

    if event == "ping":
        return "pong", 200

    if event != "push":
        return "ignored", 200

    subprocess.Popen(
        ["/bin/bash", "/var/www/automatly/deploy.sh"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )

    return "deploy started", 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)