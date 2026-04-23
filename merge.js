const fs = require('fs');
const old = JSON.parse(fs.readFileSync('./data/sample_products.json'));
const batch5 = JSON.parse(fs.readFileSync('./data/batch5.json'));
const updated = [...old, ...batch5];
fs.writeFileSync('./data/sample_products.json', JSON.stringify(updated, null, 2));
console.log(`Merged ${batch5.length} new products. Total: ${updated.length}`);
fs.unlinkSync('./data/batch5.json');