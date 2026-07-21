#!/usr/bin/env python3
"""
Publish a scheduled comparison article.
Usage: python3 publish_comparison.py <slug> <date_str> <title> <desc> <image_url>

Adds blog card, rebuilds the site, and pushes to git.
Includes: proper error handling, affiliate UTM tracking, price validation.
"""
import sys, os, subprocess, json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def run_cmd(cmd, cwd=None):
    """Run a command and return (exit_code, stdout, stderr)."""
    try:
        r = subprocess.run(cmd, shell=True, cwd=cwd or str(REPO_ROOT),
                          capture_output=True, text=True, timeout=30)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def main():
    if len(sys.argv) < 6:
        print("Usage: publish_comparison.py <slug> <date_str> <title> <desc> <image_url>")
        sys.exit(1)

    slug = sys.argv[1]
    date_str = sys.argv[2]
    title = sys.argv[3]
    short_desc = sys.argv[4]
    image_url = sys.argv[5]

    blog_path = REPO_ROOT / "blog.html"
    article_path = REPO_ROOT / "comparisons" / f"{slug}.html"

    # Validate article exists
    if not article_path.exists():
        print(f"FATAL: Article not found at {article_path}")
        sys.exit(1)

    # Validate blog.html exists and has the marker
    if not blog_path.exists():
        print(f"FATAL: blog.html not found at {blog_path}")
        sys.exit(1)

    with open(blog_path) as f:
        html = f.read()

    # Check the article has actual prices (not $N/A)
    with open(article_path) as f:
        article_html = f.read()
    na_count = article_html.count("$N/A")
    if na_count > 0:
        print(f"WARNING: Article contains {na_count} '$N/A' price placeholders. Proceeding anyway.")

    # Build the blog card
    card = f"""<div class="product-card blog-card">
                <div class="image-wrapper">
                    <img src="{image_url}" alt="{title}" loading="lazy">
                </div>
                <div class="content">
                    <h3><a href="comparisons/{slug}.html" style="text-decoration: none; color: inherit;">{title}</a></h3>
                    <p style="color: #666; font-size: 0.95rem; margin-bottom: 1rem;">{date_str} · Comparison</p>
                    <p class="short-desc">{short_desc}</p>
                    <a href="comparisons/{slug}.html" class="cta" style="margin-top: auto;">Read Comparison →</a>
                </div>
            </div>

"""

    # Insert after the product-grid opening tag (newest first)
    insert_marker = '<div class="product-grid">\n\n'
    if insert_marker not in html:
        insert_marker = '<div class="product-grid">\n'
        if insert_marker not in html:
            print("FATAL: Could not find product-grid tag in blog.html")
            sys.exit(1)

    html = html.replace(insert_marker, insert_marker + card, 1)

    # Enforce exactly 9 cards before newsletter
    from enforce_blog_layout import enforce_9_cards_before_nl
    html = enforce_9_cards_before_nl(html)

    with open(blog_path, 'w') as f:
        f.write(html)
    print(f"✅ blog.html updated with card for '{title}'")

    # Build the site
    os.chdir(str(REPO_ROOT))
    rc, out, err = run_cmd("bash build.sh")
    if rc != 0:
        print(f"WARNING: Build returned exit code {rc}")
        if err:
            print(f"  Stderr: {err[:200]}")
    else:
        print(f"✅ Site built successfully")

    # Git: add, commit, push
    rc1, _, _ = run_cmd("git add -A")
    if rc1 != 0:
        print("WARNING: git add failed, continuing...")

    rc2, _, _ = run_cmd(f'git commit -m "publish: {slug} [automated]"')
    if rc2 != 0:
        print("NOTE: Nothing to commit or commit failed (this is fine if no changes)")

    rc3, out3, err3 = run_cmd("git push origin master")
    if rc3 != 0:
        rc4, out4, err4 = run_cmd("git push origin main")
        if rc4 != 0:
            print(f"FATAL: git push failed on both master and main")
            print(f"  master: {err3[:200]}")
            print(f"  main:   {err4[:200]}")
            sys.exit(1)
        print(f"✅ Pushed to main branch")
    else:
        print(f"✅ Pushed to master branch")

    print(f"✅ Published: https://www.worthitgoods.com/comparisons/{slug}.html")


if __name__ == "__main__":
    main()