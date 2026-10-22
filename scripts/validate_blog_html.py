#!/usr/bin/env python3
"""
Build-time validation for blog.html (and its _site copy).

Guards against the class of bug introduced 2026-09-27, where a card-extraction
regression in enforce_blog_layout.py silently dropped each card's outer closing
</div>, shipping 11 unclosed <div>s and collapsing the live /blog grid.

Checks:
  1. Balanced <div> / <section> nesting (stack-based, void + self-closing aware).
  2. Direct children of .product-grid are only .product-card.blog-card elements
     or the .newsletter-section.
  3. Prints the file and the first mismatch (line + tag), then exits non-zero.

Dependency-light: Python 3 standard library only.

Usage:
    python3 scripts/validate_blog_html.py blog.html _site/blog.html
Missing files are skipped (so it can run before _site/blog.html exists).
"""

import sys
from html.parser import HTMLParser

# Elements that never have a closing tag.
VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

CHECKED_TAGS = {"div", "section"}


class _Mismatch:
    def __init__(self, line, msg):
        self.line = line
        self.msg = msg

    def __str__(self):
        return "line %d: %s" % (self.line, self.msg)


class BlogValidator(HTMLParser):
    """Stack-based nesting checker + .product-grid child auditor."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        # stack entries: [tag, line]
        self.stack = []
        self.mismatch = None

        # .product-grid tracking
        self.grid_depth = None          # stack depth at which grid is open
        self.grid_children = []         # list of (tag, classes, line)

    # ── helpers ──────────────────────────────────────────────────────────
    def _classes(self, attrs):
        for name, value in attrs:
            if name == "class" and value:
                return value.split()
        return []

    def _fail(self, line, msg):
        if self.mismatch is None:
            self.mismatch = _Mismatch(line, msg)

    # ── parser hooks ─────────────────────────────────────────────────────
    def handle_starttag(self, tag, attrs):
        line = self.getpos()[0]
        classes = self._classes(attrs)

        # Record direct children of an open .product-grid.
        if self.grid_depth is not None and len(self.stack) == self.grid_depth + 1:
            self.grid_children.append((tag, classes, line))

        if "product-grid" in classes:
            self.grid_depth = len(self.stack)

        # Void elements never have a closing tag — never push them, or they
        # would be reported as unclosed at end of file.
        if tag in VOID_ELEMENTS:
            return

        self.stack.append([tag, line])

    def handle_startendtag(self, tag, attrs):
        # <tag /> — element opens and closes; count as balanced, record child.
        line = self.getpos()[0]
        classes = self._classes(attrs)
        if self.grid_depth is not None and len(self.stack) == self.grid_depth + 1:
            self.grid_children.append((tag, classes, line))

    def handle_endtag(self, tag):
        line = self.getpos()[0]
        if tag in VOID_ELEMENTS:
            return
        if not self.stack:
            self._fail(line, "stray closing </%s> with no matching open tag" % tag)
            return
        if self.stack[-1][0] == tag:
            self.stack.pop()
            if self.grid_depth is not None and len(self.stack) <= self.grid_depth:
                self.grid_depth = None
            return
        # Mismatch: closing tag doesn't match the innermost open tag.
        open_line = self.stack[-1][1]
        # Try to find a matching ancestor.
        match_idx = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                match_idx = i
                break
        if match_idx is None:
            self._fail(line, "stray closing </%s> (innermost open is <%s> from line %d)"
                       % (tag, self.stack[-1][0], open_line))
            return
        # Closing tag closes an ancestor; everything above it is unclosed.
        unclosed = [s[0] for s in self.stack[match_idx + 1:]]
        self._fail(line, "closing </%s> closes an outer tag; unclosed: %s (opened at line %s)"
                   % (tag, ", ".join("<%s>" % t for t in unclosed),
                      ", ".join(str(s[1]) for s in self.stack[match_idx + 1:])))
        del self.stack[match_idx:]

    def close(self):
        super().close()
        if self.mismatch is None and self.stack:
            first = self.stack[0]
            self._fail(first[1], "unclosed <%s> at end of file (never closed)" % first[0])


def validate_file(path):
    """Return list of error strings for one file ([] == valid)."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            html = fh.read()
    except FileNotFoundError:
        return []  # nothing to validate yet
    except OSError as exc:
        return ["%s: cannot read file: %s" % (path, exc)]

    parser = BlogValidator()
    parser.feed(html)
    parser.close()

    errors = []

    # 1. Nesting.
    if parser.mismatch is not None:
        errors.append("%s: unbalanced <div>/<section> nesting — %s" % (path, parser.mismatch))

    # 2. .product-grid direct children.
    if parser.grid_depth is None and not parser.grid_children:
        # grid may be closed cleanly; we still collected children above.
        pass
    if not parser.grid_children and '<div class="product-grid">' in html:
        errors.append("%s: .product-grid found but no direct children parsed" % path)
    for tag, classes, line in parser.grid_children:
        allowed = (
            (tag == "div" and "product-card" in classes and "blog-card" in classes)
            or (tag == "section" and "newsletter-section" in classes)
        )
        if not allowed:
            shown = " ".join(classes) if classes else "(no class)"
            errors.append(
                "%s: .product-grid direct child is not allowed at line %d — "
                "<%s class=\"%s\">; expected .product-card.blog-card or .newsletter-section"
                % (path, line, tag, shown)
            )
            break  # report first mismatch only

    return errors


def main(argv):
    targets = argv[1:] or ["blog.html", "_site/blog.html"]
    all_errors = []
    checked = []
    for path in targets:
        errors = validate_file(path)
        checked.append(path)
        all_errors.extend(errors)

    if all_errors:
        print("✖ blog.html validation FAILED", file=sys.stderr)
        for err in all_errors:
            print("  " + err, file=sys.stderr)
        print("", file=sys.stderr)
        print("Fix the malformed HTML before it ships. If enforce_blog_layout.py produced",
              file=sys.stderr)
        print("this, inspect its card-extraction logic (dropped outer </div> regression).",
              file=sys.stderr)
        return 1

    print("✔ blog.html validation passed (%s)" % ", ".join(checked))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
