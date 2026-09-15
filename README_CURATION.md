# WorthItGoods Weekly Curation Pipeline

Automated pipeline run weekly. See cron job `worthitgoods-weekly-curation`.

## Pipeline steps
1. Check seasonal theme is not active.
2. Product search (via scripts).
3. Description generation.
4. Dedup.
5. Merge into catalog.
6. Rebuild site.
7. Commit & deploy.
8. Notify via Telegram.

All steps are script-driven; no manual product entry.
