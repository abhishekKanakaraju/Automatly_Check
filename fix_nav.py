import os
import re

TEMPLATES_DIR = "templates"
BLOGS_DIR = "blogs"

# Single clean nav for ALL pages — never changes
CLEAN_NAV = """  <ul class="nav-links">
    <li><a href="/for-job-seekers">For Job Seekers</a></li>
    <li><a href="/for-employers">For Employers</a></li>
    <li><a href="/how-it-works">How It Works</a></li>
    <li><a href="/pricing">Pricing</a></li>
    <li><a href="/blog">Blog</a></li>
    <li><a href="/about">About</a></li>
  </ul>"""

# Active class map for template pages
ACTIVE_MAP = {
    "index.html":                  "/",
    "iexchange-jobseekers.html":   "/for-job-seekers",
    "iexchange-employers.html":    "/for-employers",
    "iexchange-how-it-works.html": "/how-it-works",
    "iexchange-pricing.html":      "/pricing",
    "iexchange-blog.html":         "/blog",
    "iexchange-about.html":        "/about",
    "iexchange-government.html":   "/government",
}

SCROLL_FIX = """
  // Force scroll to top on every page load
  if (history.scrollRestoration) {
    history.scrollRestoration = 'manual';
  }
  window.scrollTo(0, 0);

  // Show elements already in viewport immediately
  document.querySelectorAll('.fade-up').forEach(el => {
    const rect = el.getBoundingClientRect();
    if (rect.top < window.innerHeight) el.classList.add('visible');
  });
"""

def fix_file(filepath, is_blog=False):
    filename = os.path.basename(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # Fix 1 — Replace entire nav-links ul with clean version
    pattern = re.compile(r'<ul class="nav-links">.*?</ul>', re.DOTALL)

    if pattern.search(content):
        # Blog articles don't get active class — nav is same on all
        if is_blog:
            clean = CLEAN_NAV.replace('href="/blog">', 'href="/blog" class="active">')
        else:
            active_route = ACTIVE_MAP.get(filename, "")
            clean = CLEAN_NAV
            if active_route:
                clean = clean.replace(
                    f'href="{active_route}">',
                    f'href="{active_route}" class="active">'
                )
        content = pattern.sub(clean, content)

    # Fix 2 — Scroll fix + viewport trigger
    if "scrollRestoration" not in content:
        if "<script>" in content:
            content = content.replace("<script>", f"<script>{SCROLL_FIX}", 1)
        else:
            content = content.replace("</body>", f"<script>{SCROLL_FIX}\n</script>\n</body>")

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  [+] Fixed: {filename}")
    else:
        print(f"  [=] Already clean: {filename}")

def main():
    print("\n=== Fixing nav in ALL HTML files ===\n")

    print("[Templates]")
    if os.path.exists(TEMPLATES_DIR):
        for filename in sorted(os.listdir(TEMPLATES_DIR)):
            if filename.endswith(".html"):
                fix_file(os.path.join(TEMPLATES_DIR, filename), is_blog=False)

    print("\n[Blogs]")
    if os.path.exists(BLOGS_DIR):
        for filename in sorted(os.listdir(BLOGS_DIR)):
            if filename.endswith(".html"):
                fix_file(os.path.join(BLOGS_DIR, filename), is_blog=True)

    print("\n=== Done! Restart Flask. ===\n")

if __name__ == "__main__":
    main()