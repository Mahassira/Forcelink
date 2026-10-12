# FORCE LINK GENERAL TRADING LLC — website

Static corporate website (7 page types, 11 HTML pages) for FORCE LINK GENERAL TRADING LLC, Dubai.

## Structure

```
build/build_site.py        Generator: all copy, product data, page templates, image optimisation
static/assets/css/site.css Design system and layout
static/assets/js/main.js   Navigation, reveal, count-up, inquiry form
static/assets/js/geo.js     Lat/lon maths for markers and arcs (shared, testable)
static/assets/js/globe.js   Market-connections globe: Three.js, home page only, CSS fallback
tests/geo.test.js          Node tests for coordinates and arc alignment (`node tests/geo.test.js`)
source-assets/             Original brand assets supplied by the company (do not edit)
site/                      Generated output (what GitHub Pages serves)
.github/workflows/pages.yml  Build and deploy to GitHub Pages
```

## Build

```bash
pip install pillow
python3 build/build_site.py                       # relative links only
SITE_URL=https://example.com/ python3 build/build_site.py   # enables canonical/OG/sitemap
```

Output is written to `site/`. All links are relative, so the site works under a repository subpath
(`https://<user>.github.io/<repo>/`) without configuration.

## Deployment (GitHub Pages)

1. Repository **Settings → Pages → Build and deployment → Source: GitHub Actions**.
2. Optional: add repository variable `SITE_URL` (Settings → Secrets and variables → Actions → Variables)
   once the production URL is confirmed.
3. Merge to `main`; the workflow builds and deploys.

## Contact form

The site is static, so no server receives form submissions. The inquiry form validates input, copies a
summary to the clipboard where the browser allows it, and opens the visitor's email app addressed to
`info@forcelink-ae.com`. The page never states that a message was sent.

To enable hosted submissions later (for example Formspree or a similar provider), the company must choose
a provider, create the form, and then update `static/assets/js/main.js` and the privacy text in
`build/build_site.py`. No secret keys should be placed in browser code.

## Items requiring company input before launch

- Production URL (for `SITE_URL`): canonical tags, Open Graph, sitemap and structured breadcrumbs are
  skipped until it is set.
- Confirmed street address, if one should be shown (currently only "Dubai, United Arab Emirates").
- Hosted form provider, if inquiries should reach the team without an email client.
- Confirmation of product technical information, if the company wants specifications published
  (currently "Request Product Information" only).
- Apple touch icon (PNG) and a dedicated social image; the current OG image is a crop of the hero photo.
- Confirmation of which product image file corresponds to each product (filenames were used as supplied).
- Confirmation that the market coordinates on the globe are acceptable as representative (they are country-level points, not shipment data).

## Notes

- Typography: Inter is named first in the font stack; it is not bundled or loaded from a CDN, so visitors
  without Inter installed see the system sans-serif.
- The logo is the company's SVG, with only its viewBox cropped for header/footer use. Colours and geometry are unchanged.
