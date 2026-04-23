const fs = require('fs');
const path = require('path');
const file = path.join(__dirname, 'data', 'sample_products.json');
let data = fs.readFileSync(file, 'utf8');
const oldLen = data.length;
data = data.replace(/("affiliate_url":\\s*"[^"]*")\\s*\\n\\s*("rating":)/g, '$1,\\n    $2');
fs.writeFileSync(file, data);
console.log(`Fixed sample_products.json: ${oldLen} -> ${data.length} chars. Added commas.`);