import os
from datetime import datetime

# Dynamically determine the project root (one directory up from this script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
BASE_URL = "https://wllclngn.github.io/SomeKindofFiction"
OUTPUT_FILE = os.path.join(ROOT_DIR, "sitemap.xml")
EXCLUDED_DIRS = {"tests", "test"}

def find_html_files(root_dir):
    html_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Exclude unwanted directories in-place (modifies os.walk traversal)
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS and not d.startswith('.')]
        rel_dir = os.path.relpath(dirpath, root_dir)
        for filename in filenames:
            if filename.endswith(".html"):
                rel_file = os.path.relpath(os.path.join(dirpath, filename), root_dir)
                html_files.append(rel_file.replace("\\", "/"))
    return html_files

def get_lastmod(filepath):
    try:
        mtime = os.path.getmtime(os.path.join(ROOT_DIR, filepath))
        return datetime.utcfromtimestamp(mtime).strftime("%Y-%m-%d")
    except Exception:
        return None

def url_for_file(filepath):
    # Output homepage as trailing slash
    if filepath == "index.html":
        return f"{BASE_URL}/"
    return f"{BASE_URL}/{filepath.lstrip('/')}"

def generate_sitemap(files):
    urls = []
    for file in files:
        lastmod = get_lastmod(file)
        url = url_for_file(file)
        url_entry = f"  <url>\n    <loc>{url}</loc>"
        if lastmod:
            url_entry += f"\n    <lastmod>{lastmod}</lastmod>"
        url_entry += "\n    <changefreq>Occasionally</changefreq>\n    <priority>0.8</priority>\n  </url>"
        urls.append(url_entry)
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += "\n".join(urls)
    sitemap += '\n</urlset>\n'
    return sitemap

if __name__ == "__main__":
    html_files = find_html_files(ROOT_DIR)
    print("HTML files found:", html_files)  # Debugging aid
    sitemap_content = generate_sitemap(html_files)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(sitemap_content)
    print(f"Sitemap generated with {len(html_files)} URLs → {OUTPUT_FILE}")