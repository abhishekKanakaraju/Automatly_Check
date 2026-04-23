import os
import re

TEMPLATES_DIR = "templates"
ROUTES_FILE = "site_routes.py"

# Pages that should be ignored (already handled manually)
SKIP_FILES = {"index.html", "index_1.html", "index_2.html"}

def filename_to_route(filename):
    """Convert filename to Flask route. e.g. iexchange-how-it-works.html -> /how-it-works"""
    name = filename.replace(".html", "")
    name = re.sub(r'^iexchange-', '', name)
    name = name.replace("_", "-").lower()
    return f"/{name}"

def filename_to_func(filename):
    """Convert filename to valid Python function name. e.g. iexchange-how-it-works.html -> how_it_works"""
    name = filename.replace(".html", "")
    name = re.sub(r'^iexchange-', '', name)
    name = name.replace("-", "_").lower()
    # ensure it doesn't start with a number
    if name[0].isdigit():
        name = "page_" + name
    return name

def filename_to_label(filename):
    """Convert filename to human readable nav label. e.g. iexchange-how-it-works.html -> How It Works"""
    name = filename.replace(".html", "")
    name = re.sub(r'^iexchange-', '', name)
    name = name.replace("-", " ").replace("_", " ")
    return name.title()

def get_registered_routes():
    """Read site_routes.py and extract already registered filenames."""
    if not os.path.exists(ROUTES_FILE):
        print(f"ERROR: {ROUTES_FILE} not found. Make sure you run this from your project root.")
        exit(1)

    with open(ROUTES_FILE, "r") as f:
        content = f.read()

    registered = re.findall(r'render_template\(["\'](.+?)["\']\)', content)
    return set(registered)

def get_registered_funcs():
    """Read site_routes.py and extract already used function names."""
    if not os.path.exists(ROUTES_FILE):
        return set()
    with open(ROUTES_FILE, "r") as f:
        content = f.read()
    return set(re.findall(r'def (\w+)\(\)', content))

def get_template_files():
    """Get all HTML files in templates folder."""
    if not os.path.exists(TEMPLATES_DIR):
        print(f"ERROR: templates/ folder not found. Run this from your project root.")
        exit(1)
    files = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith(".html")]
    return files

def add_route(filename):
    """Add a new route to site_routes.py."""
    route = filename_to_route(filename)
    func_name = filename_to_func(filename)

    # If function name already taken, add suffix
    existing_funcs = get_registered_funcs()
    original_func = func_name
    counter = 2
    while func_name in existing_funcs:
        func_name = f"{original_func}_{counter}"
        counter += 1

    new_route = f"""
@site_bp.route("{route}")
def {func_name}():
    return render_template("{filename}")
"""

    with open(ROUTES_FILE, "a") as f:
        f.write(new_route)

    print(f"  [+] Route added: {route} -> {filename} (func: {func_name})")
    return route

def add_nav_link(filename, route):
    """Add nav link to all other HTML files in templates/."""
    label = filename_to_label(filename)
    nav_link = f'<li><a href="{route}">{label}</a></li>'

    html_files = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith(".html") and f != filename]

    for html_file in html_files:
        filepath = os.path.join(TEMPLATES_DIR, html_file)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        if '<ul class="nav-links">' in content and nav_link not in content:
            content = content.replace(
                '</ul>\n  <button class="nav-cta"',
                f'    {nav_link}\n  </ul>\n  <button class="nav-cta"'
            )
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  [+] Nav link added to: {html_file}")

def fix_html_links(filename):
    """Fix any .html links in the new file to use Flask routes."""
    filepath = os.path.join(TEMPLATES_DIR, filename)

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    replacements = {
        'href="index.html#how"':            'href="/#how"',
        'href="index.html#testimonials"':   'href="/#testimonials"',
        'href="index.html"':                'href="/"',
        'href="iexchange-jobseekers.html"': 'href="/for-job-seekers"',
        'href="iexchange-employers.html"':  'href="/for-employers"',
        'href="iexchange-how-it-works.html"': 'href="/how-it-works"',
    }

    for old, new in replacements.items():
        content = content.replace(old, new)

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  [+] Fixed .html links in: {filename}")

def main():
    print("\n=== i.Exchange Auto Page Registrar ===\n")

    template_files = get_template_files()
    registered = get_registered_routes()

    new_files = [
        f for f in template_files
        if f not in registered and f not in SKIP_FILES
    ]

    if not new_files:
        print("No new pages found. Everything is already registered.")
        print(f"\nRegistered templates: {', '.join(sorted(registered))}")
        return

    print(f"Found {len(new_files)} new page(s): {', '.join(new_files)}\n")

    for filename in new_files:
        print(f"Processing: {filename}")
        fix_html_links(filename)
        route = add_route(filename)
        add_nav_link(filename, route)
        print()

    print("=== Done! Restart Flask to see changes. ===\n")

if __name__ == "__main__":
    main()