# Belgian tax URL crawl (crawl4ai) — findings

## What was implemented

- `fetch_url` in `search.py` loads pages with crawl4ai using a **persistent Chromium profile**, **`DISPLAY` defaulting to `:1`** (headed browser on X11/xvfb), and a **warm-up navigation** to `https://fin.belgium.be/fr/particuliers` before crawling targets.
- `fetch_all_sitemap_urls` reads all keys under `endpoints` in `extracted_sitemap.json`, reuses one crawler session, and **re-runs `fetch_url` once** for any row that failed the first pass.
- `test_fetch_all_sitemap_urls` writes aggregated JSON to `out/fetch_sitemap_results.json`.

## Validation

- Full run: **123 / 123 URLs** returned `success: true` in `out/fetch_sitemap_results.json`.
- A second review pass confirmed counts, all successes, and spot-checked excerpts and `html_length` values.

## WAF / Akamai behaviour

- `finances.belgium.be` often returns an Akamai/TSPD **CAPTCHA interstitial** instead of Drupal HTML when the session is not “trusted”.
- **UndetectedAdapter + persistent context** consistently failed here; **default Playwright + persistent context + fin.belgium.be warm-up** worked reliably.
- When the interstitial appeared, **re-running the same warm-up** before retrying the target URL cleared it in practice.
- Success is detected by **page structure**, not by the presence of `/TSPD/` or `bobcmn` strings (legitimate Drupal responses can still include those).
- Explicit CAPTCHA copy (`testing whether you are a human visitor`) is treated as failure and triggers retries.
- **MyMinfin** (e.g. Fisconet+ redirect to `minfin.fgov.be`) has no Drupal `main-content` landmark; the detector allows **MyMinfin / minfin** hosts and large non-CAPTCHA HTML so those redirects count as success.

## Notable redirects

- `https://fin.belgium.be/fr/particuliers` → `https://fin.belgium.be/fr` (301).
- Fisconet+ → `https://www.minfin.fgov.be/myminfin-web/pages/public/fisconet`.
- Some paths differ only by URL-encoding in `redirected_url` (e.g. `scène` vs `sc%C3%A8ne`).

## Runtime

- A full batch of 123 URLs took on the order of **30 minutes** in this environment, dominated by `networkidle` waits, warm-up replays on retries, and the second pass for any initial failures.
