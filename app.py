from flask import Flask
from register_pages import main as register_pages
from register_blogs import main as register_blogs
from site_routes import site_bp
from webhook import webhook_bp
import os

# Auto-register pages and blogs before starting
register_pages()
register_blogs()

app = Flask(__name__, template_folder="templates")

# Also allow Flask to find templates in the blogs/ folder
app.jinja_loader.searchpath.append(os.path.join(app.root_path, "blogs"))

app.register_blueprint(site_bp)
app.register_blueprint(webhook_bp)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)