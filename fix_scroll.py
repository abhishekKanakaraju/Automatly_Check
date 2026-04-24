import os
import re

TEMPLATES_DIR = "templates"
BLOGS_DIR = "blogs"

SCROLL_FIX = """
  // Force scroll to top on every page load
  if (history.scrollRestoration) {
    history.scrollRestoration = 'manual';
  }
  window.scrollTo(0, 0);
"""

def fix_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    filename = os.path.basename(filepath)
    fixes = []

    # Fix 1 — anchor links that only work on home page
    if filename != "index.html":
        if 'href="#how"' in content:
            content = content.replace('href="#how"', 'href="/#how"')
            fixes.append("fixed #how link")
        if 'href="#testimonials"' in content:
            content = content.replace('href="#testimonials"', 'href="/#testimonials"')
            fixes.append("fixed #testimonials link")
        if 'href="#"' in content:
            content = content.replace('href="#"', 'href="/"')
            fixes.append("fixed empty # links")

    # Fix 2 — scroll to top on page load
    if "scrollRestoration" not in content:
        if "<script>" in content:
            content = content.replace("<script>", f"<script>{SCROLL_FIX}", 1)
        else:
            content = content.replace("</body>", f"<script>{SCROLL_FIX}</script>\n</body>")
        fixes.append("added scroll fix")

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  [+] {filename}: {', '.join(fixes)}")
    else:
        print(f"  [=] {filename}: already clean")

def main():
    print("\n=== Fixing nav links and scroll position ===\n")

    if os.path.exists(TEMPLATES_DIR):
        print("[Templates]")
        for filename in sorted(os.listdir(TEMPLATES_DIR)):
            if filename.endswith(".html"):
                fix_file(os.path.join(TEMPLATES_DIR, filename))

    if os.path.exists(BLOGS_DIR):
        print("\n[Blogs]")
        for filename in sorted(os.listdir(BLOGS_DIR)):
            if filename.endswith(".html"):
                fix_file(os.path.join(BLOGS_DIR, filename))

    print("\n=== Done! Restart Flask. ===\n")

if __name__ == "__main__":
    main()