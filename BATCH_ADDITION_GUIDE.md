# WorthItGoods - Batch Addition & Maintenance Guide

**Last Updated:** 2026-05-20

---

## ⚡ Quick Model Handoff Summary (Read This First)

**Golden Rule:** Always start from the *last known-good working commit*, **never** the latest master commit.

**Core Actions for Every Batch:**
1. Branch from the last successful deployment commit (ask user if unsure).
2. **Prepend** new products to `data/sample_products.json` — do **not** replace.
3. Create **both** `.md` and `.html` versions of the blog post.
4. Manually add the new post card to the **top** of `blog.html`.
5. Run `./build.sh` and verify locally before pushing.
6. Push → PR → merge to `master` → monitor Cloudflare deployment.

**Never do these:**
- Work from the absolute latest commit on master.
- Replace or delete existing products.
- Only create a `.md` blog file (the `.html` is required).
- Skip local verification.

If something breaks, check the **Failure Modes** section below.

---

## Core Principles

1. **Never work from the absolute latest commit on master** when adding a new batch. Always base your work on the **last known-good stable commit** that produced a working deployment.
2. **Always prepend**, never replace or overwrite the existing product list.
3. **Blog posts must have both** a `.md` source file **and** a matching static `.html` file (or the project must build them).
4. **The blog index (`blog.html`) must be manually updated** — do not rely on `generate-*.js` scripts unless you have verified they work.
5. **Verify every link and image** before declaring the work complete.

---

## Project Structure (Critical Files)

| File | Purpose | Notes |
|------|---------|-------|
| `data/sample_products.json` | Master list of all products shown on homepage | **Never replace** — always prepend new items |
| `blog.html` | Blog index page | Must manually add new post card at the top of `.product-grid` |
| `generate-pages.js` | Builds `_site/` and homepage | Run via `build.sh` |
| `build.sh` | Main build command | Run this after changes to test locally |
| `blog/YYYY-MM-DD-batch-XX-....md` | Markdown source for blog posts | Required |
| `blog/YYYY-MM-DD-batch-XX-....html` | Rendered blog post | Required for links to work on live site |

---

## Standard Operating Procedure (Adding a New Batch)

### Step 0: Identify the Correct Base Commit
- Find the most recent commit hash that produced a **working, deployed site** with all previous products.
- Example (as of May 2026): `64f1757` = last good state with 78 products.
- **Never** use a commit that contains a broken or incomplete `sample_products.json`.

You can find good commits by:
- Checking the successful Cloudflare Pages deployment logs for the commit SHA
- Looking at `git log --oneline` and matching dates to known good deployments
- Asking the user for the last working dev URL and tracing back to the commit

### Step 1: Create a Fresh Branch from the Stable Commit
```bash
git checkout -b batch-XX-description <stable-commit-sha>
# Example:
git checkout -b batch16-exact-78 64f1757
```

### Step 2: Add New Products (Prepend Only)
1. Load the current `data/sample_products.json` (should have the previous count).
2. Insert the **new batch items at the very top** of the array.
3. Keep every existing product exactly as-is.
4. Validate the JSON:
   ```bash
   python3 -c "import json; data=json.load(open('data/sample_products.json')); print(len(data))"
   ```
5. Commit with clear message:  
   `Batch XX: prepend N new products to the previous M-product list`

### Step 3: Create the Blog Post
Create **two files**:

**A. Markdown source** (for the repo)
`blog/YYYY-MM-DD-batch-XX-name.md`

**B. Static HTML** (so the link works on the live site)
`blog/YYYY-MM-DD-batch-XX-name.html`

The HTML version should be a complete, styled page that matches the existing blog posts (use one of the recent posts as a template).

### Step 4: Update the Blog Index
Edit `blog.html` and **insert the new post card at the very top** of the `.product-grid` div.

Use the exact same pattern and styling as the existing cards (gradient color, emoji icon, date, short description, "Read More →" button).

### Step 5: Local Verification (Mandatory)
Before pushing, run:
```bash
./build.sh
```
Then open `_site/index.html` and `_site/blog.html` locally and check:
- All new products appear at the top of the grid
- Links and images load
- Blog index shows the new post as the first card
- Clicking the blog card opens the correct post with images and formatting

### Step 6: Push and Deploy
```bash
git push -u origin <branch-name>
```
Create a PR → merge into `master`.

After merge, monitor the next Cloudflare Pages deployment. Confirm the live site shows the correct number of products and that the new blog post link resolves.

---

## Pre-Push Checklist (Mandatory)

Before running `git push`, you **must** complete this checklist:

- [ ] Product count in `data/sample_products.json` is correct (previous count + new batch)
- [ ] All new products are at the **top** of the list
- [ ] JSON is valid (no syntax errors)
- [ ] Both `.md` and `.html` blog post files exist and have matching names
- [ ] Blog index (`blog.html`) has the new post card at the very top of `.product-grid`
- [ ] `./build.sh` runs without errors
- [ ] Local `_site/` preview shows correct products and blog post
- [ ] All images load and links work in local preview
- [ ] Commit message follows the standard format (see Naming Conventions)

If any item fails, **fix it before pushing**.

---

## Failure Modes & Recovery

| Failure | Symptoms | Root Cause | Fix |
|---------|----------|------------|-----|
| Broken / truncated `sample_products.json` | `SyntaxError: Unterminated string` during build | Previous write operation was cut off | Restore from last good commit, re-apply only the new products |
| Blog card links to 404 or home page | Clicking new post goes to homepage or shows "not found" | Only `.md` file was created, no matching `.html` | Create the static `.html` version of the blog post |
| Wrong product count after deployment | Site shows old count or duplicate products | Started from wrong base commit or replaced instead of prepending | Reset to last good commit and re-do the prepend |
| Merge conflicts on `blog.html` or JSON | Git merge fails with conflict markers | Another branch modified the same files | Abort merge, rebase onto the correct stable branch, resolve manually |
| Images not loading on live site | Broken image icons or missing visuals | Incorrect image URLs or relative paths | Use full Amazon CDN URLs; verify in local build first |
| Blog post looks ugly or unstyled | Plain text, no cards, missing formatting | Used minimal placeholder HTML instead of full styled version | Replace with complete HTML matching existing post style |

**Recovery Command (most common case):**
```bash
git checkout <last-good-commit-sha>
git checkout -b recovery-branch
# Re-apply only the intended changes
```

---

## Post-Deployment Verification Steps

After Cloudflare finishes deploying, verify the following on the **live site**:

1. **Homepage** – Refresh and confirm the new products appear at the top of the grid.
2. **Product count** – Check the total number of products matches expectations.
3. **Blog Index** – Visit `/blog` and confirm the new post is the first card.
4. **Blog Post Link** – Click the new blog card and verify it loads the full post with images and formatting.
5. **Images** – Check that all product images on both homepage and blog post load correctly.
6. **Old functionality** – Spot-check that existing products and older blog posts still work.

If anything is broken, **do not** tell the user it is fixed. Immediately investigate and fix.

---

## Naming Conventions & Commit Message Templates

### Branch Naming
- Format: `batchXX-<short-description>`
- Examples:
  - `batch16-fathersday`
  - `batch17-outdoor-gear`
  - `batch18-tech-cleanup`

### Blog Post File Naming
- Markdown: `blog/YYYY-MM-DD-batch-XX-name.md`
- HTML: `blog/YYYY-MM-DD-batch-XX-name.html`
- Example: `blog/2026-06-21-batch-16-fathers-day.html`

### Commit Messages
Use clear, consistent messages:

- **Product addition:** `Batch 16: prepend 15 new Father's Day products to 78-product stable list`
- **Blog post:** `Add full rich HTML version of Batch 16 Father's Day blog post`
- **Blog index update:** `Add Batch 16 Father's Day blog post card to top of blog index`
- **Fix:** `Fix: repair truncated sample_products.json from previous incomplete write`

---

## Post-Deployment Verification (Quick Version)

After every merge to master, you should do this:

1. Wait for Cloudflare deployment to complete.
2. Visit the live site.
3. Confirm:
   - New products appear at the top
   - Blog post card shows up and links correctly
   - All images load
   - No console errors

Log the successful deployment URL and commit hash in the "Current Known Good State" section below.

---

## Current Known Good State (Update After Every Successful Batch)

- **Last stable commit:** `64f1757` (78 products)
- **Product count after Batch 16:** 93
- **Blog index last updated:** 2026-06-21
- **Most recent successful deployment URL example:** https://65dcbeba.worthitgoods-site.pages.dev/

**Next batch should start from:** `716b9e0` (or the latest confirmed good commit on master)

---

## Notes for Future Models

If you are an AI model working on this site:
- Read this file **first** before making any changes.
- If the user says "add Batch XX", ask them for the commit SHA of the last working deployment if you are unsure.
- Always confirm the current product count before touching `sample_products.json`.
- Treat the creation of the static `.html` blog post as a required step, not optional.

---

**End of Guide** — Update this document after every successful batch.