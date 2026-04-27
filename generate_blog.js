#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

function generateBlog(batchFile) {
  const batch = JSON.parse(fs.readFileSync(batchFile, 'utf8'));
  const today = new Date().toISOString().split('T')[0];
  const slug = `blog/${today}-batch-${batchFile.match(/batch(\d+)/)?.[1] || 'unknown'}`;
  const outputPath = path.join(__dirname, `${slug}.md`);

  // Determine category from first product
  const category = batch[0]?.category || 'general';
  const productIds = batch.map(p => p.id).join(', ');

  let md = `---\ntitle: "Top 5 ${category} Deals – ${today} Edition"\ndate: ${today}\ndescription: "Curated picks for ${category}. All products include Amazon affiliate links."\ncategories: [${category}]\nproducts: [${productIds}]\n---\n\n`;

  md += `Welcome to our latest batch of top picks in the ${category} category. Each product below has been selected for its quality, usefulness, and value.\n\n`;

  // Quick comparison table
  md += `## Quick Comparison\n\n| Product | Best For | Price* | Rating |\n|---------|----------|--------|--------|\n`;
  batch.forEach(p => {
    const snippet = p.description.split('.')[0];
    md += `| ${p.title} | ${snippet} | Check Amazon | ⭐⭐⭐⭐ |\n`;
  });
  md += `> *Prices fluctuate; see Amazon for current deals.*\n\n`;

  // In-depth reviews
  md += `## In-Depth Reviews\n\n`;
  batch.forEach((p, i) => {
    md += `### ${i+1}. ${p.title}\n\n`;
    md += `![Image](${p.image})\n\n`;
    md += `**Why we picked it:** ${p.description}\n\n`;
    md += `**Key features:**\n`;
    md += `- ${p.description.split('.')[0]}\n`;
    md += `- Practical benefit from description\n`;
    md += `- Consumer appeal point\n\n`;
    md += `**Ideal for:** ${p.category} enthusiasts\n\n`;
    md += `👉 [Buy on Amazon](${p.affiliate_url})\n\n`;
  });

  // Which one is right
  md += `## Which One Is Right for You?\n\n`;
  batch.forEach(p => {
    md += `- ${p.title}: ${p.description.split('.')[0]}\n`;
  });

  md += `\n## Final Thoughts\n\nWe hope this curated list helps you find exactly what you need. If you enjoyed this post, consider subscribing to our newsletter for weekly deals.\n\n`;
  md += `*Disclosure: This post contains Amazon affiliate links. We earn a commission on qualifying purchases at no extra cost to you.*\n`;

  // Ensure directory
  const dir = path.dirname(outputPath);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(outputPath, md);
  console.log(`Generated: ${outputPath}`);
}

const batchFile = process.argv[2];
if (!batchFile) {
  console.error('Usage: node generate_blog.js <batch.json>');
  process.exit(1);
}
generateBlog(batchFile);
