import os
import re

TEMPLATES_DIR = "templates"
ROUTES_FILE = "site_routes.py"

SKIP_FILES = {"index.html", "index_1.html", "index_2.html"}

# ─── FILENAME HELPERS ────────────────────────────────────────────────

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

def filename_to_label(filename):
    name = filename.replace(".html", "")
    name = re.sub(r'^iexchange-', '', name)
    return name.replace("-", " ").replace("_", " ").title()

# ─── HTML LINK FIXER ─────────────────────────────────────────────────

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

# ─── NAV LINK HELPERS ────────────────────────────────────────────────

def add_nav_link(filename, route):
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

def remove_nav_links(route):
    if not os.path.exists(TEMPLATES_DIR):
        return
    html_files = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith(".html")]
    for html_file in html_files:
        filepath = os.path.join(TEMPLATES_DIR, html_file)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        pattern = rf'\n?\s*<li><a href="{re.escape(route)}"[^>]*>.*?</a></li>'
        new_content = re.sub(pattern, '', content)
        if new_content != content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"  [-] Nav link removed from: {html_file}")

# ─── GET REGISTERED FUNCS ────────────────────────────────────────────

def get_registered_funcs(content):
    return set(re.findall(r'def (\w+)\(\)', content))

# ─── MAIN SYNC FUNCTION ──────────────────────────────────────────────

def sync_pages(routes_content, template_files, existing_refs):
    """
    Sync template pages into site_routes.py.
    Returns updated routes_content and count of added/removed.
    """
    added = 0
    removed_routes = []

    # Parse existing route blocks
    route_block_pattern = re.compile(
        r'(@site_bp\.route\(".+?"\)\s*\ndef \w+\(\):\s*\n(?:\s+.+\n)*?\s*return render_template\(["\'](.+?)["\']\))',
        re.DOTALL
    )

    blocks_to_keep = []
    for match in route_block_pattern.finditer(routes_content):
        block = match.group(1)
        template_ref = match.group(2).strip()
        # Only process non-blog routes here
        if template_ref.startswith("../blogs/") or template_ref in [f for f in os.listdir("blogs") if f.endswith(".html")]:
            blocks_to_keep.append(block)
            continue
        if template_ref in template_files:
            blocks_to_keep.append(block)
        else:
            route_match = re.search(r'@site_bp\.route\("(.+?)"\)', block)
            if route_match:
                removed_routes.append(route_match.group(1))
            print(f"  [-] Page route removed for deleted file: {template_ref}")

    # Remove nav links for deleted pages
    for route in removed_routes:
        remove_nav_links(route)

    # Add new pages not yet registered
    for filename in sorted(template_files):
        if filename in SKIP_FILES:
            continue
        if filename not in existing_refs:
            route = filename_to_route(filename)
            func_name = filename_to_func(filename)
            existing_funcs = get_registered_funcs(routes_content)
            base = func_name
            counter = 2
            while func_name in existing_funcs:
                func_name = f"{base}_{counter}"
                counter += 1
            if filename == "iexchange-blog.html":
                new_block = f'\n@site_bp.route("{route}")\ndef {func_name}():\n    articles = get_articles()\n    return render_template("{filename}", articles=articles)\n'
            else:
                new_block = f'\n@site_bp.route("{route}")\ndef {func_name}():\n    return render_template("{filename}")\n'
            routes_content += new_block
            existing_refs.add(filename)
            print(f"  [+] Page route added: {route} -> {filename}")
            added += 1
            fix_html_links(filename)
            add_nav_link(filename, route)

    print(f"  [=] Pages: {added} added, {len(removed_routes)} removed.")
    return routes_content

def get_template_files():
    if not os.path.exists(TEMPLATES_DIR):
        print(f"ERROR: templates/ folder not found.")
        exit(1)
    return [f for f in os.listdir(TEMPLATES_DIR) if f.endswith(".html")]

def main():
    print("\n[Pages] Syncing template pages...\n")
    template_files = set(get_template_files())

    with open(ROUTES_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    existing_refs = set(re.findall(r'render_template\(["\'](.+?)["\']\)', content))
    updated = sync_pages(content, template_files, existing_refs)

    with open(ROUTES_FILE, "w", encoding="utf-8") as f:
        f.write(updated)

    print("[Pages] Done.\n")

if __name__ == "__main__":
    main()
