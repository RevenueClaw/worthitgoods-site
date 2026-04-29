// Simple MD to HTML converter for blogs
const fs = require('fs');
const path = require('path');
const blogDir = './blog';
const outDir = './_site/blog';

const mdToHtml = (md) => {
  // Basic MD parser: headers, bold, lists, links, images, paragraphs
  let html = md
    .replace(/^### (.*$)/gm, '<h3>$1</h3>')
    .replace(/^## (.*$)/gm, '<h2>$1</h2>')
    .replace(/^# (.*$)/gm, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" style="max-width:100%;height:auto;">')
    .replace(/\[(.*?)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
    .replace(/^[-*] (.*$)/gm, '<li>$1</li>')
    .replace(/<li>/g, (m, offset, s) => s.slice(0, offset).match(/<ul>|<ol>/) ? m : '<ul><li>' + m.slice(4))
    .replace(/<\/li>\n\n/g, '</li></ul>\n\n')
    .replace(/^(\n+)/, '<p>')
    .replace(/(\n+)$/gm, '</p>')
    .replace(/\n\n/g, '</p><p>');
  return html.replace(/<p>(\s*<\/?(h[1-6]|ul|ol|li|img|a|strong|em)>)/g, '$1').replace(/<\/?(p)>\s*<\/p>/g, '');
};

fs.readdirSync(blogDir).forEach(file => {
  if (file.endsWith('.md')) {
    const md = fs.readFileSync(path.join(blogDir, file), 'utf8');
    const frontmatter = md.match(/---\n([\s\S]*?)\n---/);
    const content = md.slice(frontmatter ? frontmatter[0].length : 0).trim();
    const htmlContent = mdToHtml(content);
    const title = frontmatter ? frontmatter[1].match(/title: (.*)/)?.[1] || path.basename(file, '.md') : 'Blog Post';
    const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title} | WorthItGoods</title>
  <link rel="stylesheet" href="/style.css">
</head>
<body>
  <header><!-- NAV PLACEHOLDER --></header>
  <article style="max-width:800px;margin:4rem auto;padding:2rem;background:white;border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,0.1);">
    <h1>${title}</h1>
    ${htmlContent}
  </article>
  <footer><!-- FOOTER --></footer>
</body>
</html>`;
    fs.writeFileSync(path.join(outDir, file.replace('.md', '.html')), html);
    console.log(`Converted ${file} to HTML`);
  }
});
