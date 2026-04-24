import os
import re

TEMPLATES_DIR = "templates"

# The exact clean nav for ALL pages (same for every page)
CLEAN_NAV = """  <ul class="nav-links">
    <li><a href="/for-job-seekers">For Job Seekers</a></li>
    <li><a href="/for-employers">For Employers</a></li>
    <li><a href="/how-it-works">How It Works</a></li>
    <li><a href="/pricing">Pricing</a></li>
    <li><a href="/blog">Blog</a></li>
    <li><a href="/about">About</a></li>
  </ul>"""

def fix_nav(filepath):
    filename = os.path.basename(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # Replace entire nav-links ul with clean version
    pattern = re.compile(
        r'<ul class="nav-links">.*?</ul>',
        re.DOTALL
    )

    # Set active class based on filename
    active_map = {
        "index.html": "/",
        "iexchange-jobseekers.html": "/for-job-seekers",
        "iexchange-employers.html": "/for-employers",
        "iexchange-how-it-works.html": "/how-it-works",
        "iexchange-pricing.html": "/pricing",
        "iexchange-blog.html": "/blog",
        "iexchange-about.html": "/about",
        "iexchange-government.html": "/government",
    }

    active_route = active_map.get(filename, "")
    clean = CLEAN_NAV
    if active_route:
        clean = clean.replace(
            f'href="{active_route}">',
            f'href="{active_route}" class="active">'
        )

    if pattern.search(content):
        content = pattern.sub(clean, content)

    # Also fix scroll
    if "scrollRestoration" not in content:
        scroll_fix = """
  // Force scroll to top on every page load
  if (history.scrollRestoration) {
    history.scrollRestoration = 'manual';
  }
  window.scrollTo(0, 0);
"""
        if "<script>" in content:
            content = content.replace("<script>", f"<script>{scroll_fix}", 1)

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  [+] Fixed: {filename}")
    else:
        print(f"  [=] Already clean: {filename}")

def main():
    print("\n=== Fixing nav in all template files ===\n")
    for filename in sorted(os.listdir(TEMPLATES_DIR)):
        if filename.endswith(".html"):
            fix_nav(os.path.join(TEMPLATES_DIR, filename))
    print("\n=== Done! Restart Flask. ===\n")

if __name__ == "__main__":
    main()
