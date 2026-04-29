const fs = require('fs');
const path = require('path');
const blogDir = './blog';

let posts = fs.readdirSync(blogDir).filter(f => f.endsWith('.md')).map(file => {
  const md = fs.readFileSync(path.join(blogDir, file), 'utf8');
  const fm = md.match(/---\n([\s\S]*?)\n---/)?.[1] || '';
  const titleMatch = fm.match(/title:\s*(.*)/);
  const dateMatch = fm.match(/date:\s*(.*)/);
  const excerpt = md.replace(/---[\s\S]*?---/, '').substring(0, 200).trim() + '...';
  return {
    title: titleMatch ? titleMatch[1].trim() : file.replace('.md', ''),
    date: dateMatch ? dateMatch[1].trim() : 'Recent',
    excerpt,
    url: `/blog/${file.replace('.md', '.html')}`
  };
}).sort((a, b) => new Date(b.date) - new Date(a.date));

const listHtml = posts.map(post => `
  <li style="margin-bottom:2rem;padding-bottom:2rem;border-bottom:1px solid #eee;">
    <h3 style="margin-bottom:0.5rem;"><a href="${post.url}">${post.title}</a></h3>
    <p style="color:#666;margin-bottom:1rem;font-size:0.95rem;">${post.date}</p>
    <p>${post.excerpt}</p>
    <a href="${post.url}" style="color:#2563eb;font-weight:600;">Read More →</a>
  </li>
`).join('');

const indexHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Blog | WorthItGoods</title>
  <link rel="stylesheet" href="/style.css">
</head>
<body>
  <header><!-- NAV --></header>
  <main style="max-width:960px;margin:4rem auto;padding:2rem;">
    <h1>WorthItGoods Blog</h1>
    <p>Latest guides on products worth buying.</p>
    <ul style="list-style:none;padding:0;">${listHtml}</ul>
  </main>
  <footer><!-- FOOTER --></footer>
</body>
</html>`;

fs.writeFileSync(path.join('_site', 'blog.html'), indexHtml);
console.log(`Generated blog.html with ${posts.length} posts`);