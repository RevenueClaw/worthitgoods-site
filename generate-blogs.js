const fs = require('fs');
const path = require('path');
const blogDir = './blog';
const outDir = './_site/blog';
const stylePath = './style.css';

if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

// Basic frontmatter + MD parser
function parseFrontmatter(md) {
  const fmMatch = md.match(/---\n([\s\S]*?)\n---/);
  const frontmatter = {};
  if (fmMatch) {
    fmMatch[1].split('\n').forEach(line => {
      const [key, val] = line.split(': ');
      if (key && val) frontmatter[key.trim()] = val.trim();
    });
  }
  const content = md.replace(/---[\s\S]*?---\n*/, '').trim();
  return { frontmatter, content };
}

function mdToHtml(md) {
  return md
    .replace(/^### (.*$)/gm, '<h3>$1</h3>')
    .replace(/^## (.*$)/gm, '<h2>$1</h2>')
    .replace(/^# (.*$)/gm, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" style="max-width:100%;height:auto;border-radius:8px;">')
    .replace(/\[(.*?)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    .replace(/^[-*+] (.*$)/gm, '<li>$1</li>')
    .replace(/(<li>)/g, '<ul>$1') // Simple list wrap
    .replace(/<\/li>\s*<\/ul>/g, '</li></ul>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^/gm, '<p>')
    .replace(/<\/p>\s*<\/p>/g, '</p>');
}

fs.readdirSync(blogDir).filter(f => f.endsWith('.md')).forEach(file => {
  const mdPath = path.join(blogDir, file);
  const md = fs.readFileSync(mdPath, 'utf8');
  const { frontmatter, content } = parseFrontmatter(md);
  const title = frontmatter.title || path.basename(file, '.md').replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  const desc = frontmatter.description || content.substring(0, 160) + '...';
  const date = frontmatter.date || new Date().toISOString().split('T')[0];

  const htmlContent = mdToHtml(content);

  const fullHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title} | WorthItGoods</title>
  <meta name="description" content="${desc}">
  <link rel="canonical" href="https://worthitgoods.com/blog/${file.replace('.md', '')}">
  <link rel="stylesheet" href="/style.css">
</head>
<body>
  <header>
    <nav>
      <a href="/" class="logo">WorthItGoods</a>
      <ul>
        <li><a href="/">Home</a></li>
        <li><a href="/blog.html">Blog</a></li>
      </ul>
    </nav>
  </header>
  <main style="max-width:800px;margin:4rem auto;padding:2rem;background:white;border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,0.1);">
    <article>
      <h1>${title}</h1>
      <p class="date">${date}</p>
      ${htmlContent}
    </article>
    <nav style="margin-top:3rem;padding-top:2rem;border-top:1px solid #eee;text-align:center;">
      <a href="/blog.html" style="margin-right:1rem;">← Back to Blog</a>
      <a href="/">Back to Home</a>
    </nav>
  </main>
  <footer style="background:#1a1a1a;color:#aaa;text-align:center;padding:2rem;">
    <p>© 2026 WorthItGoods. Amazon affiliate links.</p>
  </footer>
</body>
</html>`;

  fs.writeFileSync(path.join(outDir, file.replace('.md', '.html')), fullHtml);
  console.log(`Generated ${file} → ${file.replace('.md', '.html')}`);
});