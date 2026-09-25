# CouponFinder Architecture & Execution Plan

## 1. Safety Guarantee & Existing Codebase Preservation
- **Preserved Core**: All existing frontend UI, coupon cards, categories, search, modal flow (Step 1 -> Step 2 -> Step 3), and theme toggle will remain intact.
- **Strict CPA Locker Protection**: The OGAds 2-offer selection UI, strict mandatory 1-offer completion requirement, `/api/offers` serverless proxy, `/api/check` anti-cheat polling, multi-site postback routing (`aff_sub4=couponfinder&aff_sub5=[ip]`), and 10-hour `localStorage` bypass logic will not be altered or removed.
- **Bug Fix Incorporated**: In `script.js`, `loadTranslations()` and `applyLanguage()` will be implemented to fix the current runtime `ReferenceError` when loading `data/translations.json`.

---

## 2. File Modification & Creation Inventory

### A. Existing Files to Modify (4 Files)
1. **`vercel.json`**:
   - Add rewrites/routes for `/sitemap.xml` and dynamic sub-sitemaps `/sitemap_:page.xml` pointing to `/api/sitemap.js`.
   - Add routes for pSEO landing pages `/coupons/:slug` and `/:lang/coupons/:slug` pointing to `/api/pseo.js`.
   - Add secure route for the secret admin panel `/secretadmin2026here` and its backend API `/api/admin/:action`.
2. **`script.js`**:
   - Implement missing `loadTranslations()` and `applyLanguage(lang)` to wire up dynamic i18n from `data/translations.json` without touching coupon rendering or modal logic.
3. **`.env.example` / `path`**:
   - Ensure all configuration keys (`ADMIN_USER`, `ADMIN_PASSWORD`, `ADMIN_JWT_SECRET`, `ADMIN_PATH`, `OGADS_API_KEY`, `OGADS_SITE_ID`, `NEXT_PUBLIC_SITE_URL`, `DEFAULT_LOCALE`) are documented with security instructions.
4. **`robots.txt`**:
   - Restrict crawlers from `/secretadmin2026here`, `/api/admin`, and admin files.
   - Point crawlers to `https://findercoupon.vercel.app/sitemap.xml`.

### B. New Files to Create (4 Files)
1. **`secretadmin2026here.html`**:
   - Secure Admin Panel interface matching the website theme.
   - **Tab 1: Dashboard**: Metrics overview (total pSEO pages generated, active coupons, languages).
   - **Tab 2: Language Manager**: Live inline editor for `en`, `es`, `fr`, and `pt` translation dictionaries (`data/translations.json`).
   - **Tab 3: pSEO Engine & Generator**: Interface to add/edit brands, intent modifiers, and templates in `data/pseo-config.json`, plus a 1-click bulk generator capable of scaling to thousands of pages.
   - **Tab 4: Media Downloader (Video & Audio)**: Audio/Video coupon asset manager and download trigger testing module.
   - **Tab 5: CPA Locker & Security**: Real-time postback logs and environment variables status.
2. **`api/admin.js`**:
   - Authenticated serverless backend endpoint for admin operations.
   - JWT creation on login (`/api/admin?action=login`) and timing-safe password verification.
   - Secure token middleware validating `ADMIN_JWT_SECRET`.
   - Read & update endpoints for `data/translations.json` and `data/pseo-config.json`.
   - Automatic bulk pSEO page generator endpoint.
3. **`api/download.js`**:
   - Serverless media download endpoint supporting both audio and video streams/attachments with proper `Content-Disposition` and MIME headers.
4. **`data/pseo-config.json` (Expanded)**:
   - Extend existing dataset to include additional high-volume brands and intent modifiers to scale to thousands of indexable URLs across `en`, `es`, `fr`, and `pt`.

---

## 3. Total Batches: 4 Batches

All subsequent updates will be deployed in 4 sequential batches:

### **Batch 1 of 4: Routing, Sitemap & Core Frontend Fixes**
- **Files**: `vercel.json`, `robots.txt`, `script.js`
- **Actions**:
  - Map `/sitemap.xml` and `/sitemap_:page.xml` to `api/sitemap.js`.
  - Map `/coupons/:slug` and `/:lang/coupons/:slug` to `api/pseo.js`.
  - Map `/secretadmin2026here` to `secretadmin2026here.html`.
  - Add `loadTranslations()` and `applyLanguage()` to `script.js`.
  - Update `robots.txt` to protect the admin panel while exposing the sitemap index.

### **Batch 2 of 4: Secure Backend API & Scalable pSEO Generator**
- **Files**: `api/admin.js`, `api/sitemap.js`, `data/pseo-config.json`
- **Actions**:
  - Implement JWT authentication and HMAC verification using `ADMIN_JWT_SECRET`.
  - Add API endpoints to read/write `data/translations.json` and `data/pseo-config.json`.
  - Implement the automatic bulk generator multiplying brands × intents × 4 languages to produce thousands of valid routes.
  - Update `api/sitemap.js` with fast pagination (`sitemap_1.xml`, `sitemap_2.xml`, etc., 500 URLs per sub-sitemap) with full `xhtml:link hreflang` tags.

### **Batch 3 of 4: Secret Admin Dashboard UI**
- **Files**: `secretadmin2026here.html`
- **Actions**:
  - Build responsive admin dashboard UI at `/secretadmin2026here`.
  - Session-based authentication with auto-redirect to login modal if unauthenticated.
  - Full translation editing interface for `en`, `es`, `fr`, `pt`.
  - pSEO management interface with real-time URL preview and sitemap status checker.
  - Audio and video media download manager.

### **Batch 4 of 4: Media Downloader Engine & Performance Optimizations**
- **Files**: `api/download.js`, `style.css`, `.env.example`
- **Actions**:
  - Implement `/api/download` supporting both audio (`audio/mpeg`) and video (`video/mp4`) asset downloads.
  - Implement edge caching headers (`Cache-Control: public, s-maxage=86400, stale-while-revalidate=43200`) across all dynamic pSEO and sitemap responses.
  - DNS prefetching for CDNs (Clearbit, Unsplash, Google Fonts).
  - Schema.org validation for `Store`, `AggregateOffer`, and `FAQPage`.

---

## 4. Architectural Features & Performance Enhancements

1. **Crawler-Optimized Sitemap Chunking**:
   - Master index `sitemap.xml` references sub-sitemaps `sitemap_1.xml`, `sitemap_2.xml`, etc.
   - Each sub-sitemap contains 500 URLs with multilingual `hreflang` tags (`en`, `es`, `fr`, `pt`, `x-default`), allowing search engines to discover and crawl 10,000+ pages without exceeding payload limits.
2. **Dynamic pSEO Engine**:
   - Dynamic route rendering via `api/pseo.js` ensures thousands of pages can be served on-demand without generating thousands of static HTML files, keeping build times near zero.
3. **Enterprise Admin Security**:
   - Path-obscured admin panel (`/secretadmin2026here`).
   - Stateless JWT tokens signed with `ADMIN_JWT_SECRET` avoiding database dependencies while ensuring server-verified access.
   - Timing-safe authentication checks preventing timing attacks.
4. **Media Downloader Engine**:
   - Dedicated handler for both audio and video downloads with configurable stream buffering and sanitized file headers.
