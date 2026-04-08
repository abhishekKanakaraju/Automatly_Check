from flask import Blueprint, request
import hmac
import hashlib
import subprocess

webhook_bp = Blueprint("webhook", __name__)

WEBHOOK_SECRET = "MDQ6VXNlcjc0MTM4NTAy"

@webhook_bp.route("/deploy", methods=["POST"])
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
        stdout=open("/var/www/automatly/webhook.log", "ab"),
        stderr=open("/var/www/automatly/webhook.log", "ab"),
        start_new_session=True
    )

    return "deploy started", 200