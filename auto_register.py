import os
import re
import json
from datetime import datetime

TEMPLATES_DIR = "templates"
BLOGS_DIR = "blogs"
ROUTES_FILE = "site_routes.py"
BLOGS_JSON = "blogs.json"

SKIP_FILES = {"index.html", "index_1.html", "index_2.html"}

# ─── FILENAME HELPERS ────────────────────────────────────────────────

def filename_to_route(filename, is_blog=False):
    name = filename.replace(".html", "")
    name = re.sub(r'^iexchange-', '', name)
    name = re.sub(r'^blog-', '', name)
    name = name.replace("_", "-").lower()
    return f"/blog/{name}" if is_blog else f"/{name}"

def filename_to_func(filename, is_blog=False):
    name = filename.replace(".html", "")
    name = re.sub(r'^iexchange-', '', name)
    name = re.sub(r'^blog-', '', name)
    name = name.replace("-", "_").lower()
    if name[0].isdigit():
        name = "page_" + name
    return f"blog_{name}" if is_blog else name

def filename_to_slug(filename):
    name = filename.replace(".html", "")
    name = re.sub(r'^blog-', '', name)
    return name.lower()

def filename_to_label(filename):
    name = filename.replace(".html", "")
    name = re.sub(r'^iexchange-', '', name)
    name = re.sub(r'^blog-', '', name)
    return name.replace("-", " ").replace("_", " ").title()

# ─── EXTRACT METADATA FROM BLOG HTML ────────────────────────────────

def extract_blog_metadata(filename):
    filepath = os.path.join(BLOGS_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    slug = filename_to_slug(filename)

    title_match = re.search(r'<title>(.+?)\s*\|.*?</title>', content)
    title = title_match.group(1).strip() if title_match else filename_to_label(filename)

    excerpt_match = re.search(r'class="article-subtitle"[^>]*>(.+?)</p>', content, re.DOTALL)
    if excerpt_match:
        excerpt = re.sub(r'<[^>]+>', '', excerpt_match.group(1)).strip()
        excerpt = re.sub(r'\s+', ' ', excerpt)
    else:
        excerpt = title

    tag_match = re.search(r'class="article-tag">(.+?)</div>', content)
    tag = tag_match.group(1).strip() if tag_match else "Product Update"

    date_match = re.search(r'class="meta-item">(\w+ \d+, \d{4})<', content)
    date = date_match.group(1).strip() if date_match else datetime.today().strftime("%B %d, %Y")

    read_match = re.search(r'class="meta-item">(\d+ min read)<', content)
    read_time = read_match.group(1).strip() if read_match else "3 min read"

    emoji_match = re.search(r'class="article-cover">(.+?)</div>', content)
    if emoji_match:
        raw = emoji_match.group(1).strip()
        emoji = ''.join(c for c in raw if ord(c) > 127) or "📄"
    else:
        emoji = "📄"

    return {
        "slug": slug,
        "title": title,
        "excerpt": excerpt[:160],
        "tag": tag,
        "date": date,
        "read_time": read_time,
        "emoji": emoji
    }

# ─── BLOGS.JSON SYNC ─────────────────────────────────────────────────

def sync_blogs_json():
    """
    Full two-way sync between blogs/ folder and blogs.json.
    - Rebuilds blogs.json entirely from scratch every run.
    - Reads all blog HTML files and extracts metadata fresh.
    - This means no stale/corrupted entries ever persist.
    """
    if not os.path.exists(BLOGS_DIR):
        os.makedirs(BLOGS_DIR)

    blog_files = [f for f in os.listdir(BLOGS_DIR) if f.endswith(".html")]

    if not blog_files:
        # No blog files — wipe JSON clean
        with open(BLOGS_JSON, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)
        print(f"  [=] blogs.json: no blog files found, cleared.")
        return

    # Rebuild entire JSON from scratch by reading each file
    articles = []
    for filename in blog_files:
        try:
            metadata = extract_blog_metadata(filename)
            articles.append(metadata)
            print(f"  [✓] blogs.json: read '{metadata['title'][:55]}...'")
        except Exception as e:
            print(f"  [!] Could not read {filename}: {e}")

    # Sort by date descending (newest first)
    def parse_date(article):
        try:
            return datetime.strptime(article["date"], "%B %d, %Y")
        except:
            return datetime.min

    articles.sort(key=parse_date, reverse=True)

    # Always write with utf-8 encoding so emojis are never corrupted
    with open(BLOGS_JSON, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)

    print(f"  [=] blogs.json rebuilt from scratch. Total: {len(articles)} articles.")

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
    """Remove nav link for a deleted page from ALL HTML files."""
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

# ─── HTML LINK FIXER ─────────────────────────────────────────────────

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

# ─── ROUTES SYNC ─────────────────────────────────────────────────────

def get_template_files():
    if not os.path.exists(TEMPLATES_DIR):
        print(f"ERROR: templates/ folder not found.")
        exit(1)
    return [f for f in os.listdir(TEMPLATES_DIR) if f.endswith(".html")]

def get_blog_files():
    if not os.path.exists(BLOGS_DIR):
        os.makedirs(BLOGS_DIR)
    return [f for f in os.listdir(BLOGS_DIR) if f.endswith(".html")]

def sync_routes():
    """
    Full two-way sync of site_routes.py.
    - New files → ADD route + nav link
    - Deleted files → REMOVE route + remove nav link
    """
    with open(ROUTES_FILE, "r", encoding="utf-8") as f:
        original = f.read()

    template_files = set(get_template_files())
    blog_files = set(get_blog_files())

    route_block_pattern = re.compile(
        r'(@site_bp\.route\(".+?"\)\s*\ndef \w+\(\):\s*\n\s*return render_template\(["\'](.+?)["\']\))',
        re.DOTALL
    )

    blocks_to_keep = []
    removed_routes = []

    for match in route_block_pattern.finditer(original):
        block = match.group(1)
        template_ref = match.group(2).strip()
        if template_ref.startswith("../blogs/"):
            actual_file = template_ref.replace("../blogs/", "")
            exists = actual_file in blog_files
        else:
            actual_file = template_ref
            exists = actual_file in template_files
        if exists:
            blocks_to_keep.append(block)
        else:
            route_match = re.search(r'@site_bp\.route\("(.+?)"\)', block)
            if route_match:
                removed_routes.append(route_match.group(1))
            print(f"  [-] Route removed for deleted file: {actual_file}")

    # Remove nav links for deleted pages
    for route in removed_routes:
        remove_nav_links(route)

    # Rebuild header
    header_match = re.match(
        r'(from flask import.*?\n(?:import.*?\n)*.*?site_bp = Blueprint\(.+?\)\n)',
        original, re.DOTALL
    )
    header = header_match.group(1) if header_match else \
        'from flask import Blueprint, render_template\nimport json\nimport os\n\nsite_bp = Blueprint("site", __name__)\n'

    # Preserve get_articles function
    get_articles_match = re.search(r'(def get_articles\(\).+?)(?=\n@site_bp|\Z)', original, re.DOTALL)
    get_articles_func = "\n" + get_articles_match.group(1) + "\n" if get_articles_match else ""

    new_content = header + get_articles_func
    for block in blocks_to_keep:
        new_content += "\n" + block + "\n"

    # Find already registered templates
    existing_refs = set()
    for block in blocks_to_keep:
        ref_match = re.search(r'render_template\(["\'](.+?)["\']\)', block)
        if ref_match:
            existing_refs.add(ref_match.group(1))

    added = 0

    # Add new template pages
    for filename in sorted(template_files):
        if filename in SKIP_FILES:
            continue
        if filename not in existing_refs:
            route = filename_to_route(filename)
            func_name = filename_to_func(filename)
            existing_funcs = set(re.findall(r'def (\w+)\(\)', new_content))
            base = func_name
            counter = 2
            while func_name in existing_funcs:
                func_name = f"{base}_{counter}"
                counter += 1
            if filename == "iexchange-blog.html":
                new_content += f'\n@site_bp.route("{route}")\ndef {func_name}():\n    articles = get_articles()\n    return render_template("{filename}", articles=articles)\n'
            else:
                new_content += f'\n@site_bp.route("{route}")\ndef {func_name}():\n    return render_template("{filename}")\n'
            print(f"  [+] Route added: {route} -> {filename}")
            added += 1
            fix_html_links(filename, is_blog=False)
            add_nav_link(filename, route)

    # Add new blog pages
    for filename in sorted(blog_files):
        template_path = f"../blogs/{filename}"
        if template_path not in existing_refs:
            route = filename_to_route(filename, is_blog=True)
            func_name = filename_to_func(filename, is_blog=True)
            existing_funcs = set(re.findall(r'def (\w+)\(\)', new_content))
            base = func_name
            counter = 2
            while func_name in existing_funcs:
                func_name = f"{base}_{counter}"
                counter += 1
            new_content += f'\n@site_bp.route("{route}")\ndef {func_name}():\n    return render_template("{template_path}")\n'
            print(f"  [+] Route added: {route} -> {filename}")
            added += 1
            fix_html_links(filename, is_blog=True)

    with open(ROUTES_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"  [=] site_routes.py: {added} added, {len(removed_routes)} removed.")

# ─── MAIN ────────────────────────────────────────────────────────────

def main():
    print("\n=== i.Exchange Auto Page Registrar ===\n")

    print("[Step 1] Rebuilding blogs.json from blogs/ folder...")
    sync_blogs_json()
    print()

    print("[Step 2] Syncing site_routes.py and nav links...")
    sync_routes()
    print()

    print("=== Done! Flask is starting... ===\n")

if __name__ == "__main__":
    main()