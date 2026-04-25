import os
import re

TEMPLATES_DIR = "templates"
ROUTES_FILE = "site_routes.py"

SKIP_FILES = {"index.html", "index_1.html", "index_2.html"}

PROTECTED_ROUTES = {
    "index.html": "/",
    "iexchange-jobseekers.html": "/for-job-seekers",
    "iexchange-employers.html": "/for-employers",
    "iexchange-how-it-works.html": "/how-it-works",
    "iexchange-about.html": "/about",
    "iexchange-pricing.html": "/pricing",
    "iexchange-blog.html": "/blog",
}

def filename_to_route(filename):
    name = filename.replace(".html", "")
    name = re.sub(r'^iexchange-', '', name)
    name = name.replace("_", "-").lower()
    return f"/{name}"

def filename_to_func(filename):
    name = filename.replace(".html", "")
    name = re.sub(r'^iexchange-', '', name)
    name = name.replace("-", "_").lower()
    if name[0].isdigit():
        name = "page_" + name
    return name

def fix_html_links(filename):
    filepath = os.path.join(TEMPLATES_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    original = content
    replacements = {
        'href="index.html#how"':              'href="/#how"',
        'href="index.html#testimonials"':     'href="/#testimonials"',
        'href="index.html"':                  'href="/"',
        'href="iexchange-jobseekers.html"':   'href="/for-job-seekers"',
        'href="iexchange-employers.html"':    'href="/for-employers"',
        'href="iexchange-how-it-works.html"': 'href="/how-it-works"',
        'href="iexchange-blog.html"':         'href="/blog"',
    }
    for old, new in replacements.items():
        content = content.replace(old, new)
    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  [+] Fixed .html links in: {filename}")

def get_registered_funcs(content):
    return set(re.findall(r'def (\w+)\(\)', content))

def get_template_files():
    if not os.path.exists(TEMPLATES_DIR):
        print(f"ERROR: templates/ folder not found.")
        exit(1)
    return [f for f in os.listdir(TEMPLATES_DIR) if f.endswith(".html")]

def main():
    print("\n[Pages] Syncing template pages...\n")
    template_files = set(get_template_files())

    with open(ROUTES_FILE, "r", encoding="utf-8") as f:
        routes_content = f.read()

    existing_refs = set(re.findall(r'render_template\(["\'](.+?)["\']\)', routes_content))
    existing_funcs = get_registered_funcs(routes_content)

    added = 0

    # Only add NEW pages not yet in routes and not protected
    for filename in sorted(template_files):
        if filename in SKIP_FILES:
            continue
        if filename in PROTECTED_ROUTES:
            continue
        if filename not in existing_refs:
            route = filename_to_route(filename)
            func_name = filename_to_func(filename)
            base = func_name
            counter = 2
            while func_name in existing_funcs:
                func_name = f"{base}_{counter}"
                counter += 1
            existing_funcs.add(func_name)
            new_block = f'\n@site_bp.route("{route}")\ndef {func_name}():\n    return render_template("{filename}")\n'
            routes_content += new_block
            existing_refs.add(filename)
            print(f"  [+] Route added: {route} -> {filename}")
            added += 1
            fix_html_links(filename)

    with open(ROUTES_FILE, "w", encoding="utf-8") as f:
        f.write(routes_content)

    if added == 0:
        print("  [=] No new pages found.")
    print("[Pages] Done.\n")

if __name__ == "__main__":
    main()