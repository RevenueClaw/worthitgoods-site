#!/usr/bin/env node
/**
 * Generate RSS feed for WorthItGoods blog posts + comparisons.
 * Reads blog/*.html and comparisons/*.html, extracts metadata, produces feed.xml.
 *
 * BUGFIX 2026-07-31:
 * - Blog posts without YYYY-MM-DD filename prefix now check article:published_time meta tag
 * - Comparisons with "Published Month Year" (no day) default to 1st of month
 * - Comparisons with no Published line fall back to article:published_time meta, then file mtime
 * - Future-dated content (pre-scheduled) is properly detected and skipped
 */
const fs = require('fs');
const path = require('path');

const BLOG_DIR = path.join(__dirname, 'blog');
const COMP_DIR = path.join(__dirname, 'comparisons');
const SITE_DIR = path.join(__dirname, '_site');
const SITE_URL = 'https://www.worthitgoods.com';

const entries = [];

function extractMeta(filePath) {
    const html = fs.readFileSync(filePath, 'utf8');
    const titleMatch = html.match(/<title>([^<]+)<\/title>/);
    if (!titleMatch) return null;
    const title = titleMatch[1].replace(/ \| WorthIt Goods/, '').replace(/ - WorthIt Goods$/, '').trim();

    const descMatch = html.match(/<meta name="description"[^>]+content="([^"]+)"/) ||
                      html.match(/<meta property="og:description"[^>]+content="([^"]+)"/);
    const description = descMatch ? descMatch[1] : '';

    const imgMatch = html.match(/<meta property="og:image"[^>]+content="([^"]+)"/) ||
                     html.match(/<img[^>]+src="([^"]+)"[^>]*>/);
    const image = imgMatch ? imgMatch[1] : SITE_URL + '/assets/og-image-v2.jpg';

    // Extract article:published_time meta tag
    const pubTimeMatch = html.match(/<meta\s+property="article:published_time"[^>]+content="([^"]+)"/);
    const publishedTime = pubTimeMatch ? pubTimeMatch[1] : null;

    return { title, description, image, publishedTime };
}

/**
 * Parse a date string from various formats into a Date object.
 * Returns null if unparseable.
 */
function parseDate(str) {
    if (!str) return null;
    try {
        const d = new Date(str);
        if (!isNaN(d.getTime())) return d;
    } catch (e) {}
    return null;
}

/**
 * Best-effort date extraction for a file.
 * Priority: 1) explicit date from content, 2) article:published_time meta, 3) file mtime
 */
function extractDate(html, meta, filePath) {
    // 1) article:published_time meta tag (works for any file type)
    if (meta.publishedTime) {
        const d = parseDate(meta.publishedTime);
        if (d) return d;
    }

    // 2) File mtime as last resort
    try {
        const stat = fs.statSync(filePath);
        return stat.mtime;
    } catch (e) {}

    return null;
}

// Scan blog posts
fs.readdirSync(BLOG_DIR).forEach(file => {
    if (!file.endsWith('.html') || file.startsWith('custom-')) return;
    const filePath = path.join(BLOG_DIR, file);
    const meta = extractMeta(filePath);
    if (!meta) return;

    const html = fs.readFileSync(filePath, 'utf8');

    // Try filename date prefix first
    const dateMatch = file.match(/^(\d{4}-\d{2}-\d{2})/);
    let pubDate = null;
    if (dateMatch) {
        pubDate = new Date(dateMatch[1] + 'T12:00:00Z');
    } else {
        // Fall back to article:published_time meta or file mtime
        pubDate = extractDate(html, meta, filePath);
    }

    if (!pubDate) {
        pubDate = new Date(); // last resort — should never happen
    }

    const slug = file.replace(/\.html$/, '');
    entries.push({
        ...meta,
        url: `${SITE_URL}/blog/${encodeURIComponent(slug)}.html`,
        pubDate: pubDate.toUTCString(),
        category: 'Blog Post',
    });
});

// Scan comparison articles
fs.readdirSync(COMP_DIR).forEach(file => {
    if (!file.endsWith('.html')) return;
    // Skip the duplicate nested comparisons/ dir if it exists
    if (file.startsWith('comparisons')) return;
    const filePath = path.join(COMP_DIR, file);
    const meta = extractMeta(filePath);
    if (!meta) return;

    const html = fs.readFileSync(filePath, 'utf8');

    // Try multiple date patterns from the HTML content
    const dateMetaMatch = html.match(/Published\s+(\w+\s+\d+,\s+\d{4})/i) ||
                          html.match(/(\w+\s+\d+,\s+\d{4})\s*·\s*Comparison/) ||
                          html.match(/Comparison\s*·\s*(\w+\s+\d+,\s+\d{4})/) ||
                          // Handle "Published July 2026" (no day) — default to 1st
                          html.match(/Published\s+(\w+)\s+(\d{4})/i);

    let pubDate = null;

    if (dateMetaMatch) {
        if (dateMetaMatch[2]) {
            // "Published July 2026" format — use 1st of month
            pubDate = new Date(`${dateMetaMatch[1]} 1, ${dateMetaMatch[2]}`);
        } else {
            // "Published July 22, 2026" format
            pubDate = new Date(dateMetaMatch[1]);
        }
    }

    // If no date found in content, try meta tag or file mtime
    if (!pubDate || isNaN(pubDate.getTime())) {
        pubDate = extractDate(html, meta, filePath);
    }

    // Skip articles with future publish dates (pre-scheduled content)
    if (pubDate && pubDate > new Date()) {
        return;
    }

    // Last resort (shouldn't happen with mtime fallback)
    if (!pubDate || isNaN(pubDate.getTime())) {
        pubDate = new Date();
    }

    const slug = file.replace(/\.html$/, '');
    entries.push({
        ...meta,
        url: `${SITE_URL}/comparisons/${encodeURIComponent(slug)}.html`,
        pubDate: pubDate.toUTCString(),
        category: 'Comparison',
    });
});

// Sort by date descending (newest first)
entries.sort((a, b) => new Date(b.pubDate) - new Date(a.pubDate));

// Build RSS XML
const now = new Date().toUTCString();

const rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>WorthIt Goods — Blog &amp; Comparisons</title>
    <link>${SITE_URL}/blog.html</link>
    <description>Honest, hand-picked products that actually deliver. Weekly finds, seasonal guides, comparisons, and gear worth your money.</description>
    <language>en-us</language>
    <lastBuildDate>${now}</lastBuildDate>
    <atom:link href="${SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
    ${entries.map(entry => `    <item>
      <title>${escapeXml(entry.title)}</title>
      <link>${entry.url}</link>
      <guid isPermaLink="true">${entry.url}</guid>
      <pubDate>${entry.pubDate}</pubDate>
      <category>${escapeXml(entry.category)}</category>
      <description>${escapeXml(entry.description)}</description>
      <media:content url="${escapeXml(entry.image)}" medium="image"/>
    </item>`).join('\n')}
  </channel>
</rss>`;

fs.writeFileSync(path.join(SITE_DIR, 'feed.xml'), rss);
console.log(`RSS feed generated: ${entries.length} entries (${entries.filter(e => e.category === 'Blog Post').length} blog + ${entries.filter(e => e.category === 'Comparison').length} comparisons) → _site/feed.xml`);

function escapeXml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;').replace(/'/g, '&apos;');
}