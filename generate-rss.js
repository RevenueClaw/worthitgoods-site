#!/usr/bin/env node
/**
 * Generate RSS feed for WorthItGoods blog posts + comparisons.
 * Reads blog/*.html and comparisons/*.html, extracts metadata, produces feed.xml.
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

    return { title, description, image };
}

// Scan blog posts
fs.readdirSync(BLOG_DIR).forEach(file => {
    if (!file.endsWith('.html') || file.startsWith('custom-')) return;
    const meta = extractMeta(path.join(BLOG_DIR, file));
    if (!meta) return;

    const dateMatch = file.match(/^(\d{4}-\d{2}-\d{2})/);
    const pubDate = dateMatch
        ? new Date(dateMatch[1] + 'T12:00:00Z').toUTCString()
        : null;

    const slug = file.replace(/\.html$/, '');
    entries.push({
        ...meta,
        url: `${SITE_URL}/blog/${encodeURIComponent(slug)}.html`,
        pubDate: pubDate || new Date().toUTCString(),
        category: 'Blog Post',
    });
});

// Scan comparison articles
fs.readdirSync(COMP_DIR).forEach(file => {
    if (!file.endsWith('.html')) return;
    // Skip the duplicate nested comparisons/ dir if it exists
    if (file.startsWith('comparisons')) return;
    const meta = extractMeta(path.join(COMP_DIR, file));
    if (!meta) return;

    // For comparisons, get date from the article meta or file mtime
    const html = fs.readFileSync(path.join(COMP_DIR, file), 'utf8');
    const dateMetaMatch = html.match(/Published\s+(\w+\s+\d+,\s+\d{4})/i) ||
                          html.match(/(\w+\s+\d+,\s+\d{4})\s*·\s*Comparison/) ||
                          html.match(/Comparison\s*·\s*(\w+\s+\d+,\s+\d{4})/);
    const pubDate = dateMetaMatch ? dateMetaMatch[1] : null;

    // Skip articles with future publish dates (pre-scheduled)
    const parsedDate = pubDate ? new Date(pubDate) : null;
    if (parsedDate && parsedDate > new Date()) {
        return;
    }

    const slug = file.replace(/\.html$/, '');
    entries.push({
        ...meta,
        url: `${SITE_URL}/comparisons/${encodeURIComponent(slug)}.html`,
        pubDate: pubDate ? new Date(pubDate).toUTCString() : new Date().toUTCString(),
        category: 'Comparison',
    });
});

// Sort by date descending
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
