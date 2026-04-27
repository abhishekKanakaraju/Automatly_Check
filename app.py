from flask import Flask
from register_pages import main as register_pages
from register_blogs import main as register_blogs
from site_routes import site_bp
from webhook import webhook_bp
import os
import re

TEMPLATES_DIR = "templates"
BLOGS_DIR = "blogs"

ACTIVE = {
    "index.html": "/",
    "iexchange-jobseekers.html": "/for-job-seekers",
    "iexchange-employers.html": "/for-employers",
    "iexchange-how-it-works.html": "/how-it-works",
    "iexchange-pricing.html": "/pricing",
    "iexchange-blog.html": "/blog",
    "iexchange-about.html": "/about",
    "iexchange-government.html": "/government",
}

def make_nav(active_route):
    """Build clean nav with correct active link."""
    links = [
        ("/for-job-seekers", "For Job Seekers"),
        ("/for-employers", "For Employers"),
        ("/how-it-works", "How It Works"),
        ("/pricing", "Pricing"),
        ("/blog", "Blog"),
        ("/about", "About"),
    ]
    # Add any extra pages that exist in templates but not in default list
    if os.path.exists(TEMPLATES_DIR):
        for filename in os.listdir(TEMPLATES_DIR):
            if not filename.endswith(".html"):
                continue
            if filename in ACTIVE or filename in {"index.html", "index_1.html", "index_2.html"}:
                continue
            name = re.sub(r'^iexchange-', '', filename.replace(".html", ""))
            route = f"/{name.replace('_', '-').lower()}"
            label = name.replace("-", " ").replace("_", " ").title()
            if route not in [r for r, _ in links]:
                links.append((route, label))

    items = ""
    for route, label in links:
        cls = ' class="active"' if route == active_route else ''
        items += f'    <li><a href="{route}"{cls}>{label}</a></li>\n'
    return f'  <ul class="nav-links">\n{items}  </ul>'

def sync_nav():
    """Fix nav in all HTML files automatically."""
    pattern = re.compile(r'<ul class="nav-links">.*?</ul>', re.DOTALL)

    # Fix templates
    if os.path.exists(TEMPLATES_DIR):
        for filename in os.listdir(TEMPLATES_DIR):
            if not filename.endswith(".html"):
                continue
            filepath = os.path.join(TEMPLATES_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            active_route = ACTIVE.get(filename, "")
            new_content = pattern.sub(make_nav(active_route), content)
            if new_content != content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)

    # Fix blogs — Blog always active
    if os.path.exists(BLOGS_DIR):
        for filename in os.listdir(BLOGS_DIR):
            if not filename.endswith(".html"):
                continue
            filepath = os.path.join(BLOGS_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            new_content = pattern.sub(make_nav("/blog"), content)
            if new_content != content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)

    print("[Nav] Synced nav in all pages and blogs.")

# Run all auto-registration before Flask starts
register_pages()
register_blogs()
sync_nav()

app = Flask(__name__, template_folder="templates")

# Also allow Flask to find templates in the blogs/ folder
app.jinja_loader.searchpath.append(os.path.join(app.root_path, "blogs"))

app.register_blueprint(site_bp)
app.register_blueprint(webhook_bp)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)