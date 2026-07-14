#!/usr/bin/env node
/**
 * Generate RSS feed for WorthItGoods blog posts.
 * Reads blog/*.html files, extracts metadata, produces feed.xml.
 */
const fs = require('fs');
const path = require('path');

const BLOG_DIR = path.join(__dirname, 'blog');
const SITE_DIR = path.join(__dirname, '_site');
const SITE_URL = 'https://www.worthitgoods.com';

// Blog post entries: parse filename dates and extract <title>
const entries = [];

fs.readdirSync(BLOG_DIR).forEach(file => {
    if (!file.endsWith('.html') || file.startsWith('custom-')) return;
    
    const filePath = path.join(BLOG_DIR, file);
    const html = fs.readFileSync(filePath, 'utf8');
    
    // Extract title from <title> tag
    const titleMatch = html.match(/<title>([^<]+)<\/title>/);
    if (!titleMatch) return;
    const title = titleMatch[1].replace(/ - WorthIt Goods$/, '').trim();
    
    // Extract a short description from meta description or first paragraph
    const descMatch = html.match(/<meta name="description"[^>]+content="([^"]+)"/) ||
                      html.match(/<meta property="og:description"[^>]+content="([^"]+)"/);
    const description = descMatch ? descMatch[1] : '';
    
    // Try to find an image for the post
    const imgMatch = html.match(/<meta property="og:image"[^>]+content="([^"]+)"/) ||
                     html.match(/<img[^>]+src="([^"]+)"[^>]*>/);
    const image = imgMatch ? imgMatch[1] : SITE_URL + '/assets/og-image-v2.jpg';
    
    // Parse date from filename: YYYY-MM-DD-*.html
    const dateMatch = file.match(/^(\d{4}-\d{2}-\d{2})/);
    const pubDate = dateMatch 
        ? new Date(dateMatch[1] + 'T12:00:00Z').toUTCString()
        : new Date().toUTCString();
    
    const slug = file.replace(/\.html$/, '');
    
    entries.push({
        title,
        description,
        url: `${SITE_URL}/blog/${encodeURIComponent(slug)}.html`,
        image,
        pubDate,
    });
});

// Sort by date descending
entries.sort((a, b) => new Date(b.pubDate) - new Date(a.pubDate));

// Build RSS XML
const now = new Date().toUTCString();

const rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>WorthIt Goods — Blog</title>
    <link>${SITE_URL}/blog.html</link>
    <description>Honest, hand-picked products that actually deliver. Weekly finds, seasonal guides, and gear worth your money.</description>
    <language>en-us</language>
    <lastBuildDate>${now}</lastBuildDate>
    <atom:link href="${SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
    ${entries.map(entry => `    <item>
      <title>${escapeXml(entry.title)}</title>
      <link>${entry.url}</link>
      <guid isPermaLink="true">${entry.url}</guid>
      <pubDate>${entry.pubDate}</pubDate>
      <description>${escapeXml(entry.description)}</description>
      <media:content url="${escapeXml(entry.image)}" medium="image"/>
    </item>`).join('\n')}
  </channel>
</rss>`;

fs.writeFileSync(path.join(SITE_DIR, 'feed.xml'), rss);
console.log(`RSS feed generated: ${entries.length} entries → _site/feed.xml`);

function escapeXml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;').replace(/'/g, '&apos;');
}