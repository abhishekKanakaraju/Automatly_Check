from flask import Flask
from auto_register import main as auto_register
from site_routes import site_bp
from webhook import webhook_bp

# Auto-detect and register any new pages before starting
auto_register()

app = Flask(__name__)

app.register_blueprint(site_bp)
app.register_blueprint(webhook_bp)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)