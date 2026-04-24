import os
import re
import json
from datetime import datetime

BLOGS_DIR = "blogs"
ROUTES_FILE = "site_routes.py"
BLOGS_JSON = "blogs.json"

# ─── FILENAME HELPERS ────────────────────────────────────────────────

def filename_to_route(filename):
    name = filename.replace(".html", "")
    name = re.sub(r'^blog-', '', name)
    name = name.replace("_", "-").lower()
    return f"/blog/{name}"

def filename_to_func(filename):
    name = filename.replace(".html", "")
    name = re.sub(r'^blog-', '', name)
    name = name.replace("-", "_").lower()
    if name[0].isdigit():
        name = "page_" + name
    return f"blog_{name}"

def filename_to_slug(filename):
    name = filename.replace(".html", "")
    name = re.sub(r'^blog-', '', name)
    return name.lower()

# ─── EXTRACT METADATA FROM BLOG HTML ────────────────────────────────

def extract_blog_metadata(filename):
    filepath = os.path.join(BLOGS_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    slug = filename_to_slug(filename)

    title_match = re.search(r'<title>(.+?)\s*\|.*?</title>', content)
    title = title_match.group(1).strip() if title_match else slug.replace("-", " ").title()

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
    Fully rebuilds blogs.json from scratch by reading every file in blogs/.
    Guarantees no stale entries, no corrupted emojis.
    """
    if not os.path.exists(BLOGS_DIR):
        os.makedirs(BLOGS_DIR)

    blog_files = [f for f in os.listdir(BLOGS_DIR) if f.endswith(".html")]

    if not blog_files:
        with open(BLOGS_JSON, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)
        print("  [=] blogs.json: no blog files found, cleared.")
        return

    articles = []
    for filename in blog_files:
        try:
            metadata = extract_blog_metadata(filename)
            articles.append(metadata)
            print(f"  [✓] Read: '{metadata['title'][:55]}...'")
        except Exception as e:
            print(f"  [!] Could not read {filename}: {e}")

    # Sort newest first
    def parse_date(a):
        try:
            return datetime.strptime(a["date"], "%B %d, %Y")
        except:
            return datetime.min

    articles.sort(key=parse_date, reverse=True)

    with open(BLOGS_JSON, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)

    print(f"  [=] blogs.json rebuilt. Total: {len(articles)} articles.")

# ─── HTML LINK FIXER ─────────────────────────────────────────────────

def fix_html_links(filename):
    filepath = os.path.join(BLOGS_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    original = content
    replacements = {
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

def sync_blog_routes():
    """
    Sync blog routes in site_routes.py.
    - New blog files → ADD route
    - Deleted blog files → REMOVE route
    """
    if not os.path.exists(BLOGS_DIR):
        os.makedirs(BLOGS_DIR)

    blog_files = set(f for f in os.listdir(BLOGS_DIR) if f.endswith(".html"))

    with open(ROUTES_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    existing_refs = set(re.findall(r'render_template\(["\'](.+?)["\']\)', content))

    added = 0
    removed = 0

    # REMOVE routes for deleted blog files
    route_block_pattern = re.compile(
        r'\n@site_bp\.route\("/blog/.+?"\)\ndef \w+\(\):\n\s*return render_template\(["\'](.+?)["\']\)\n',
        re.DOTALL
    )
    for match in route_block_pattern.finditer(content):
        template_ref = match.group(1).strip()
        # Check if file exists (template_ref is just filename now)
        if template_ref not in blog_files:
            content = content.replace(match.group(0), '')
            print(f"  [-] Blog route removed for deleted file: {template_ref}")
            removed += 1

    # ADD routes for new blog files
    existing_refs = set(re.findall(r'render_template\(["\'](.+?)["\']\)', content))
    existing_funcs = set(re.findall(r'def (\w+)\(\)', content))

    for filename in sorted(blog_files):
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
            content += new_block
            existing_refs.add(filename)
            print(f"  [+] Blog route added: {route} -> {filename}")
            added += 1
            fix_html_links(filename)

    with open(ROUTES_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  [=] Blog routes: {added} added, {removed} removed.")

def get_blog_files():
    if not os.path.exists(BLOGS_DIR):
        os.makedirs(BLOGS_DIR)
    return [f for f in os.listdir(BLOGS_DIR) if f.endswith(".html")]

def main():
    print("\n[Blogs] Syncing blog articles...\n")
    sync_blogs_json()
    print()
    sync_blog_routes()
    print("\n[Blogs] Done.\n")

if __name__ == "__main__":
    main()
