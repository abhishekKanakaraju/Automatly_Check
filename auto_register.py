import os
import re

TEMPLATES_DIR = "templates"
BLOGS_DIR = "blogs"
ROUTES_FILE = "site_routes.py"

SKIP_FILES = {"index.html", "index_1.html", "index_2.html"}

def filename_to_route(filename, is_blog=False):
    name = filename.replace(".html", "")
    name = re.sub(r'^iexchange-', '', name)
    name = re.sub(r'^blog-', '', name)
    name = name.replace("_", "-").lower()
    if is_blog:
        return f"/blog/{name}"
    return f"/{name}"

def filename_to_func(filename, is_blog=False):
    name = filename.replace(".html", "")
    name = re.sub(r'^iexchange-', '', name)
    name = re.sub(r'^blog-', '', name)
    name = name.replace("-", "_").lower()
    if name[0].isdigit():
        name = "page_" + name
    if is_blog:
        return f"blog_{name}"
    return name

def filename_to_label(filename):
    name = filename.replace(".html", "")
    name = re.sub(r'^iexchange-', '', name)
    name = re.sub(r'^blog-', '', name)
    name = name.replace("-", " ").replace("_", " ")
    return name.title()

def get_registered_routes():
    if not os.path.exists(ROUTES_FILE):
        print(f"ERROR: {ROUTES_FILE} not found.")
        exit(1)
    with open(ROUTES_FILE, "r") as f:
        content = f.read()
    registered = re.findall(r'render_template\(["\'](.+?)["\']\)', content)
    return set(registered)

def get_registered_funcs():
    if not os.path.exists(ROUTES_FILE):
        return set()
    with open(ROUTES_FILE, "r") as f:
        content = f.read()
    return set(re.findall(r'def (\w+)\(\)', content))

def get_template_files():
    if not os.path.exists(TEMPLATES_DIR):
        print(f"ERROR: templates/ folder not found.")
        exit(1)
    return [f for f in os.listdir(TEMPLATES_DIR) if f.endswith(".html")]

def get_blog_files():
    if not os.path.exists(BLOGS_DIR):
        os.makedirs(BLOGS_DIR)
        print(f"  [+] Created blogs/ folder")
    return [f for f in os.listdir(BLOGS_DIR) if f.endswith(".html")]

def add_route(filename, is_blog=False):
    route = filename_to_route(filename, is_blog)
    func_name = filename_to_func(filename, is_blog)

    existing_funcs = get_registered_funcs()
    original_func = func_name
    counter = 2
    while func_name in existing_funcs:
        func_name = f"{original_func}_{counter}"
        counter += 1

    if is_blog:
        template_path = f"../blogs/{filename}"
        new_route = f"""
@site_bp.route("{route}")
def {func_name}():
    return render_template("{template_path}")
"""
    else:
        new_route = f"""
@site_bp.route("{route}")
def {func_name}():
    return render_template("{filename}")
"""

    with open(ROUTES_FILE, "a") as f:
        f.write(new_route)

    print(f"  [+] Route added: {route} -> {filename}")
    return route

def add_nav_link(filename, route, is_blog=False):
    if is_blog:
        return  # blog articles don't need nav links in every page
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

def fix_html_links(filename, is_blog=False):
    folder = BLOGS_DIR if is_blog else TEMPLATES_DIR
    filepath = os.path.join(folder, filename)
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

def main():
    print("\n=== i.Exchange Auto Page Registrar ===\n")

    registered = get_registered_routes()
    found_new = False

    # --- TEMPLATES ---
    template_files = get_template_files()
    new_templates = [f for f in template_files if f not in registered and f not in SKIP_FILES]

    if new_templates:
        found_new = True
        print(f"[Templates] Found {len(new_templates)} new page(s): {', '.join(new_templates)}\n")
        for filename in new_templates:
            print(f"Processing: {filename}")
            fix_html_links(filename, is_blog=False)
            route = add_route(filename, is_blog=False)
            add_nav_link(filename, route, is_blog=False)
            print()

    # --- BLOGS ---
    blog_files = get_blog_files()
    # Blog files are tracked with "blogs/" prefix in routes
    new_blogs = [f for f in blog_files if f"../blogs/{f}" not in registered]

    if new_blogs:
        found_new = True
        print(f"[Blogs] Found {len(new_blogs)} new article(s): {', '.join(new_blogs)}\n")
        for filename in new_blogs:
            print(f"Processing blog: {filename}")
            fix_html_links(filename, is_blog=True)
            route = add_route(filename, is_blog=True)
            print()

    if not found_new:
        print("No new pages or articles found. Everything is already registered.")
        print(f"\nRegistered: {', '.join(sorted(registered))}")
        return

    print("=== Done! Restart Flask to see changes. ===\n")

if __name__ == "__main__":
    main()