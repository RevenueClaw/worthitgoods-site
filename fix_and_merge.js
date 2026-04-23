const fs = require('fs');
const path = require('path');
const workspace = '/home/ubuntu/.openclaw/workspace';
const dir = path.join(workspace, 'worthitgoods-site', 'data');
const file = path.join(dir, 'sample_products.json');
let data = fs.readFileSync(file, 'utf8');
// Fix missing commas after affiliate_url
data = data.replace(/(\"affiliate_url\"\\s*:\\s*\"[^\"]+\")\\s*([^{,\"])/g, '$1,$2');
fs.writeFileSync(file, data);
console.log('Fixed commas');
const old = JSON.parse(fs.readFileSync(file, 'utf8'));
const batch = JSON.parse(fs.readFileSync(path.join(dir, 'batch5.json'), 'utf8'));
const updated = [...old, ...batch];
fs.writeFileSync(file, JSON.stringify(updated, null, 2));
console.log(`Merged: ${old.length} + ${batch.length} = ${updated.length}`);
fs.unlinkSync(path.join(dir, 'batch5.json'));