from flask import Flask
from site_routes import site_bp
from webhook import webhook_bp

app = Flask(__name__)

app.register_blueprint(site_bp)
app.register_blueprint(webhook_bp)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)