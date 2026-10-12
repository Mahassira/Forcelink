#!/usr/bin/env python3
"""Generate the FORCE LINK GENERAL TRADING LLC website into ./site.

- Pure static output (HTML, CSS, JS, optimized images). No server runtime.
- All relative links, so the site works under a GitHub Pages repository subpath.
- Optional SITE_URL env var (e.g. https://example.com/ or https://user.github.io/repo/)
  enables canonical URLs, Open Graph tags, breadcrumb structured data and sitemap.xml.

Usage:
    python3 build/build_site.py
Requires: Pillow
"""

import html
import json
import os
import re
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-assets"
STATIC = ROOT / "static"
OUT = ROOT / "site"
SITE_URL = os.environ.get("SITE_URL", "").strip()
if SITE_URL and not SITE_URL.endswith("/"):
    SITE_URL += "/"

# ---------------------------------------------------------------------------
# Company data (single source of truth)
# ---------------------------------------------------------------------------

COMPANY = {
    "name": "FORCE LINK GENERAL TRADING LLC",
    "email": "info@forcelink-ae.com",
    "phone_display": "+971 52 211 7950",
    "phone_tel": "+971522117950",
    "location": "Dubai, United Arab Emirates",
    "founded": "2023",
    "tagline": "Connecting Global Fertilizer Markets",
    "description": (
        "FORCE LINK GENERAL TRADING LLC is an international trading company based in "
        "Dubai, United Arab Emirates, focused on fertilizers and related raw materials."
    ),
}

SALES = {
    "y2025": {"value": "1.5", "decimals": "1", "label": "Metric tons sold",
              "period": "Calendar year 2025"},
    "y2026": {"value": "1.7", "decimals": "1", "label": "Metric tons sold",
              "period": "January–September 2026 (year to date, not a full-year figure)"},
}

MARKETS = [
    ("India", "Reported destination market in South Asia."),
    ("China", "Reported destination market in East Asia."),
    ("Malaysia", "Reported destination market in Southeast Asia."),
    ("Vietnam", "Reported destination market in Southeast Asia."),
    ("Indonesia", "Reported destination market in Southeast Asia."),
    ("Europe", "Reported destination market. Shown as a regional designation."),
]

EMBLEM_SIZE = (250, 29)  # display size of the footer logo; set by optimise_images()

GLOBE_LEGEND_MARKETS = ["India", "China", "Malaysia", "Vietnam", "Indonesia", "Europe (region)"]

PRODUCTS = [
    {
        "slug": "phosphate-rock",
        "name": "Phosphate Rock",
        "title_short": "Phosphate Rock",
        "tag": "Raw material",
        "source": "Phosphate_Rock.png",
        "alt": "Lump of brown-grey phosphate rock on a transparent background",
        "short": "The mined mineral that is the primary raw material for most phosphate fertilizers.",
        "lead": "A naturally occurring, mined mineral and the primary feedstock for phosphate fertilizer production.",
        "overview": [
            "Phosphate rock is extracted from sedimentary and igneous deposits and processed before use. "
            "It is the starting material from which phosphate fertilizers such as DAP, SSP and TSP are made.",
            "Because grade and impurity profile affect how rock is processed, buyers usually confirm the "
            "relevant technical information with the supplier before placing an order.",
        ],
        "role": (
            "In the fertilizer value chain, phosphate rock sits upstream. Processors convert it into soluble "
            "phosphate products, while some agricultural markets apply ground rock directly where soil "
            "conditions make that practical."
        ),
        "uses": [
            "Feedstock for manufacturing phosphate fertilizers such as DAP, SSP and TSP",
            "Raw material for phosphoric acid and other phosphate chemicals",
            "Direct application in limited agronomic situations, depending on soil conditions",
        ],
        "uses_note": "General application information. Suitability depends on crop, soil and local agronomic practice.",
    },
    {
        "slug": "dap",
        "name": "DAP — Diammonium Phosphate",
        "title_short": "DAP — Diammonium Phosphate",
        "tag": "Phosphate · Nitrogen",
        "source": "Diammonium_Phosphate.png",
        "alt": "Pile of dark granular DAP fertilizer on a white background",
        "short": "A granular fertilizer that supplies both phosphorus and nitrogen in a single product.",
        "lead": "A granular phosphate fertilizer that supplies two key plant nutrients, phosphorus and nitrogen.",
        "overview": [
            "Diammonium phosphate, known as DAP, is one of the most widely traded phosphate fertilizers. "
            "It is supplied as granules, which makes it practical to handle, store and spread with standard equipment.",
            "Its combined phosphorus and nitrogen content makes DAP a common choice in programmes that call for both nutrients.",
        ],
        "role": (
            "DAP is frequently used as a basal application before planting and is also a standard component "
            "in blended and compound fertilizer programmes."
        ),
        "uses": [
            "Basal application ahead of planting or sowing",
            "Blending with other granular fertilizers for customised programmes",
            "Phosphorus and nitrogen supply where both nutrients are required",
        ],
        "uses_note": "General application information. Rates and timing depend on crop, soil analysis and local recommendations.",
    },
    {
        "slug": "ssp",
        "name": "SSP — Single Superphosphate",
        "title_short": "SSP — Single Superphosphate",
        "tag": "Phosphate",
        "source": "Single_Superphosphate.png",
        "alt": "Pile of grey-white SSP fertilizer granules on a white background",
        "short": "A phosphorus fertilizer that also supplies sulfur and calcium.",
        "lead": "A long-established phosphate fertilizer produced by treating phosphate rock with sulfuric acid.",
        "overview": [
            "Single superphosphate is one of the oldest commercial phosphate fertilizers. Because of how it is "
            "produced, it also contains sulfur and calcium alongside its phosphorus content.",
            "For soils or crops where those secondary nutrients are also needed, SSP is often considered as a "
            "single product that covers several requirements.",
        ],
        "role": (
            "SSP is valued both for its phosphorus supply and for the secondary nutrients it provides. It is "
            "commonly applied as a base dressing before sowing."
        ),
        "uses": [
            "Phosphorus supply for field and horticultural crops",
            "Sulfur and calcium supplementation where these nutrients are needed",
            "Base dressing ahead of sowing or planting",
        ],
        "uses_note": "General application information. Suitability depends on crop, soil and local agronomic practice.",
    },
    {
        "slug": "tsp",
        "name": "TSP — Triple Superphosphate",
        "title_short": "TSP — Triple Superphosphate",
        "tag": "Phosphate",
        "source": "Triple_Superphosphate.png",
        "alt": "Pile of grey granular TSP fertilizer on a white background",
        "short": "A concentrated phosphate fertilizer with a higher phosphorus content than SSP.",
        "lead": "A concentrated phosphate fertilizer, produced using phosphoric acid rather than sulfuric acid.",
        "overview": [
            "Triple superphosphate is a concentrated phosphate fertilizer. Because it delivers more phosphorus "
            "per unit of product than single superphosphate, it is a practical choice where a compact product is preferred.",
            "TSP is supplied in granular form and is typically selected by buyers who want a high-phosphorus "
            "product for basal or blended use.",
        ],
        "role": (
            "TSP is an important phosphate option in fertilizer programmes that prioritise concentrated "
            "phosphorus delivery. It is frequently used in blends and basal applications."
        ),
        "uses": [
            "Concentrated phosphorus supply for basal application",
            "Blending into custom granular fertilizer programmes",
            "Phosphorus supply where a higher-analysis product is preferred",
        ],
        "uses_note": "General application information. Rates and timing depend on crop, soil analysis and local recommendations.",
    },
    {
        "slug": "urea",
        "name": "Urea",
        "title_short": "Urea",
        "tag": "Nitrogen",
        "source": "Urea.png",
        "alt": "Pile of white urea prills on a white background",
        "short": "A high-nitrogen solid fertilizer that is widely produced and traded internationally.",
        "lead": "A high-nitrogen solid fertilizer, one of the most widely produced and traded nitrogen products.",
        "overview": [
            "Urea supplies nitrogen, an essential nutrient for plant growth. It is supplied as white prills or "
            "granules and is one of the most widely traded solid nitrogen fertilizers.",
            "Because its nitrogen content is high, urea is handled as a concentrated product. Buyers typically "
            "confirm the required grade and packaging when they request a quotation.",
        ],
        "role": (
            "Urea is a core nitrogen source in global agriculture. It is commonly used for top-dressing during "
            "the growing season and, depending on the crop and soil, as a basal application."
        ),
        "uses": [
            "Nitrogen top-dressing during the growing season",
            "Basal application depending on crop and soil conditions",
            "Nitrogen supply in blended fertilizer programmes",
        ],
        "uses_note": "General application information. Timing and rates depend on crop, soil and local recommendations.",
    },
    {
        "slug": "sulfur",
        "name": "Sulfur",
        "title_short": "Sulfur",
        "tag": "Raw material · Sulfur",
        "source": "Sulfur.png",
        "alt": "Pile of yellow granular sulfur on a white background",
        "short": "An essential plant nutrient and a key feedstock for sulfuric acid used in phosphate production.",
        "lead": "An essential plant nutrient and a key feedstock for the sulfuric acid used in phosphate fertilizer production.",
        "overview": [
            "Sulfur is an essential plant nutrient, and it is also a central industrial input. Much of the "
            "sulfur traded internationally is converted into sulfuric acid.",
            "Sulfuric acid is used in the production of phosphate fertilizers, which makes sulfur an important "
            "raw material in the broader fertilizer value chain.",
        ],
        "role": (
            "Sulfur supports crop nutrition as a secondary nutrient and supplies the acid route for producing "
            "SSP and DAP. This dual role links sulfur closely to fertilizer production."
        ),
        "uses": [
            "Secondary nutrient supply for crops with sulfur demand",
            "Feedstock for sulfuric acid, used in phosphate fertilizer production",
            "Soil amendment in suitable conditions",
        ],
        "uses_note": "General application information. Suitability depends on crop, soil analysis and local practice.",
    },
]

PRODUCT_BY_SLUG = {p["slug"]: p for p in PRODUCTS}

NAV = [
    ("Home", "", "home"),
    ("About", "about/", "about"),
    ("Products", "products/", "products"),
    ("Markets", "markets/", "markets"),
    ("Contact", "contact/", "contact"),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def esc(value):
    return html.escape(str(value), quote=True)


def root_for(path):
    segments = [s for s in path.split("/") if s]
    return "../" * len(segments) or "./"


def nav_items(root, current):
    items = []
    for label, target, key in NAV:
        aria = ' aria-current="page"' if key == current else ""
        items.append(f'<li><a href="{root}{target}"{aria}>{esc(label)}</a></li>')
    return "\n".join(items)


def header_html(root, current):
    return f"""<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
  <div class="container header-inner">
    <a class="brand" href="{root}" aria-label="{esc(COMPANY['name'])} — home">
      <img src="{root}assets/img/forcelink-logo.svg" alt="{esc(COMPANY['name'])}" width="300" height="39">
    </a>
    <nav class="nav" aria-label="Primary">
      <ul>
{nav_items(root, current)}
      </ul>
    </nav>
    <div class="header-cta">
      <a class="btn btn--navy" href="{root}contact/">Contact Our Team</a>
    </div>
    <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="mobile-nav">
      <span class="sr-only">Menu</span>
      <span class="bars" aria-hidden="true"></span>
    </button>
  </div>
  <div class="mobile-nav" id="mobile-nav">
    <nav aria-label="Mobile">
      <ul>
{nav_items(root, current)}
      </ul>
    </nav>
    <div class="container"><a class="btn btn--gold" href="{root}contact/">Contact Our Team</a></div>
  </div>
</header>"""


def footer_html(root):
    product_links = "\n".join(
        f'<li><a href="{root}products/{p["slug"]}/">{esc(p["name"])}</a></li>' for p in PRODUCTS
    )
    return f"""<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <div class="footer-brand">
          <img class="footer-logo" src="{root}assets/img/forcelink-footer-logo.png" alt="{esc(COMPANY['name'])}" width="{EMBLEM_SIZE[0]}" height="{EMBLEM_SIZE[1]}" loading="lazy">
        </div>
        <p class="footer-desc">International trading of fertilizers and related raw materials, based in Dubai, United Arab Emirates. Established {COMPANY['founded']}.</p>
      </div>
      <nav aria-label="Footer: company">
        <h3>Company</h3>
        <ul>
          <li><a href="{root}">Home</a></li>
          <li><a href="{root}about/">About</a></li>
          <li><a href="{root}markets/">Markets</a></li>
          <li><a href="{root}contact/">Contact</a></li>
        </ul>
      </nav>
      <nav aria-label="Footer: products">
        <h3>Products</h3>
        <ul>
          <li><a href="{root}products/">All products</a></li>
{product_links}
        </ul>
      </nav>
      <div>
        <h3>Contact</h3>
        <ul>
          <li><a href="mailto:{COMPANY['email']}">{COMPANY['email']}</a></li>
          <li><a href="tel:{COMPANY['phone_tel']}">{COMPANY['phone_display']}</a></li>
          <li>{esc(COMPANY['location'])}</li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© <span data-year>{2026}</span> {esc(COMPANY['name'])}. All rights reserved.</span>
      <span>Dubai, United Arab Emirates</span>
    </div>
  </div>
</footer>"""


# Header banners for inner pages. Four supplied photographs, reused by page subject.
# Each entry: source file in source-assets/ (without the banner- prefix and .png),
# and the alt text. Edit PAGE_BANNER to change which photograph a page uses.
BANNER_IMAGES = {
    # (source file, alt text, object-position for the wide crop)
    "seeding": ("banner-seeding.png", "A hand sowing granules onto soil", "center 78%"),
    "warehouse": ("banner-warehouse.png", "Fertilizer bags stacked on pallets in a storage warehouse", "center 40%"),
    "granules": ("banner-granules.png", "Fertilizer granules in white, pink and brown", "center 50%"),
    "plant": ("banner-plant.png", "An industrial processing plant beside water, with a quarried hillside in the foreground", "center 45%"),
}
PAGE_BANNER = {
    "about": "seeding",
    "contact": "seeding",
    "markets": "warehouse",
    "products": "granules",
    "phosphate-rock": "plant",
    "dap": "granules",
    "ssp": "granules",
    "tsp": "granules",
    "urea": "granules",
    "sulfur": "warehouse",
}


def banner_html(key, root):
    name = PAGE_BANNER[key]
    _src, alt, pos = BANNER_IMAGES[name]
    return f"""  <div class="container">
    <figure class="page-banner">
      <img src="{root}assets/img/banners/{name}.webp" alt="{esc(alt)}" width="1050" height="1050" style="object-position:{pos}">
    </figure>
  </div>
"""


def page(path, title, description, body, current="", jsonld=(), scripts=()):
    root = root_for(path)
    canonical = f'<link rel="canonical" href="{SITE_URL}{path}">' if SITE_URL else ""
    og = ""
    if SITE_URL:
        og = (
            f'<meta property="og:type" content="website">'
            f'<meta property="og:site_name" content="{esc(COMPANY["name"])}">'
            f'<meta property="og:title" content="{esc(title)}">'
            f'<meta property="og:description" content="{esc(description)}">'
            f'<meta property="og:url" content="{SITE_URL}{path}">'
            f'<meta property="og:image" content="{SITE_URL}assets/img/og-image.jpg">'
            f'<meta name="twitter:card" content="summary_large_image">'
        )
    ld = "".join(
        f'<script type="application/ld+json">{json.dumps(block, ensure_ascii=False)}</script>'
        for block in jsonld
    )
    script_tags = "".join(f'<script src="{root}assets/js/{s}" defer></script>' for s in ("main.js",) + tuple(scripts))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="theme-color" content="#0E305D">
{canonical}
{og}
<link rel="icon" href="{root}assets/img/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{root}assets/css/site.css">
{ld}
</head>
<body>
{header_html(root, current)}
<main id="main">
{body}
</main>
{footer_html(root)}
{script_tags}
</body>
</html>
"""


def breadcrumbs(path, trail):
    """trail: list of (label, path). Visual breadcrumb plus optional JSON-LD."""
    root = root_for(path)
    items = []
    for i, (label, target) in enumerate(trail):
        if i == len(trail) - 1:
            items.append(f'<li aria-current="page">{esc(label)}</li>')
        else:
            items.append(f'<li><a href="{root}{target}">{esc(label)}</a></li>')
    markup = (
        '<nav class="crumbs" aria-label="Breadcrumb"><ol>' + "".join(items) + "</ol></nav>"
    )
    return markup


def breadcrumb_jsonld(trail):
    if not SITE_URL:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": label, "item": f"{SITE_URL}{target}"}
            for i, (label, target) in enumerate(trail)
        ],
    }


def cta_band(root, heading, text, primary=("Contact Our Team", "contact/")):
    return f"""<section class="section section--navy">
  <div class="container grid grid-2" style="align-items:center">
    <div>
      <h2>{esc(heading)}</h2>
      <p class="lead" style="color:#D6DEE9">{esc(text)}</p>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:12px;justify-content:flex-start" class="cta-actions">
      <a class="btn btn--gold" href="{root}{primary[1]}">{esc(primary[0])}</a>
      <a class="btn btn--outline" href="{root}products/">View Products</a>
    </div>
  </div>
</section>"""


def product_card(p, root):
    return f"""<a class="product-card reveal" href="{root}products/{p['slug']}/">
  <div class="thumb"><img src="{root}assets/img/products/{p['slug']}.webp" alt="{esc(p['alt'])}" width="800" height="800" loading="lazy"></div>
  <div class="body">
    <span class="tag">{esc(p['tag'])}</span>
    <h3>{esc(p['name'])}</h3>
    <p>{esc(p['short'])}</p>
    <span class="more">View product →</span>
  </div>
</a>"""


def metric_block(key, root_count=True):
    s = SALES[key]
    year_text = "2025" if key == "y2025" else "2026"
    return f"""<div class="metric reveal">
  <div class="metric-value"><span data-count="{s['value']}" data-decimals="{s['decimals']}">{s['value']}</span><span class="unit">M MT</span></div>
  <p class="metric-label">{s['label']} in {year_text}</p>
  <p class="metric-period">{esc(s['period'])}</p>
</div>"""


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


def home_page():
    r = "./"
    hero = f"""<section class="hero">
  <picture>
    <source media="(max-width: 760px)" srcset="{r}assets/img/hero-mobile.webp" type="image/webp">
    <img class="hero-img" src="{r}assets/img/hero-desktop.webp" alt="Aerial view of a bulk carrier at sea, its cargo hatches and deck marked with the FORCE LINK emblem" width="1920" height="1080" fetchpriority="high">
  </picture>
  <div class="container hero-content">
    <p class="eyebrow">Dubai, United Arab Emirates · Established {COMPANY['founded']}</p>
    <h1>{esc(COMPANY['tagline'])}</h1>
    <p class="lead">Connecting fertilizer products with international markets through a focused approach to global trading and commercial relationships.</p>
    <div class="hero-actions">
      <a class="btn btn--gold" href="products/">Explore Our Products</a>
      <a class="btn btn--outline" href="contact/">Contact Our Team</a>
    </div>
  </div>
</section>"""

    scale = f"""<section class="section" aria-labelledby="scale-heading">
  <div class="container">
    <div class="section-head">
      <div>
        <p class="eyebrow">Commercial scale</p>
        <h2 id="scale-heading">Reported sales volumes</h2>
      </div>
      <p>Volumes as reported by the company, shown with their reporting periods.</p>
    </div>
  </div>
  <div class="container metrics">
    {metric_block('y2025')}
    {metric_block('y2026')}
  </div>
</section>"""

    product_grid = "\n".join(product_card(p, r) for p in PRODUCTS)
    products = f"""<section class="section section--off" aria-labelledby="products-heading">
  <div class="container">
    <div class="section-head">
      <div>
        <p class="eyebrow">Product portfolio</p>
        <h2 id="products-heading">Fertilizers and raw materials</h2>
      </div>
      <a class="link-arrow" href="products/">View all products</a>
    </div>
    <div class="grid grid-3">
{product_grid}
    </div>
  </div>
</section>"""

    intro = f"""<section class="section" aria-labelledby="intro-heading">
  <div class="container split">
    <div>
      <p class="eyebrow">About FORCE LINK</p>
      <h2 id="intro-heading">A Dubai-based international trading company</h2>
      <p class="lead">{esc(COMPANY['name'])} is an international trading company based in Dubai, United Arab Emirates, established in {COMPANY['founded']}.</p>
      <p>We focus on the international trading of fertilizers and related raw materials, connecting products with buyers across Asia and Europe. Our approach is commercially direct: clear product information, clear terms and regular communication with the people we work with.</p>
      <p><a class="link-arrow" href="about/">Learn More About Us</a></p>
    </div>
    <figure class="globe-figure" style="margin:0">
      <div class="globe" id="globe" role="img" aria-label="Illustrative globe showing arcs from Dubai, United Arab Emirates, to the reported destination markets: India, China, Malaysia, Vietnam, Indonesia and Europe.">
        <div class="globe-fallback" aria-hidden="true"></div>
      </div>
      <ul class="globe-legend" aria-label="Map legend">
        <li><span class="sw sw--base" aria-hidden="true"></span><span><strong>Dubai, UAE</strong> — Company base</span></li>
        {''.join(f'<li><span class="sw sw--dest" aria-hidden="true"></span><span>{esc(label)}</span></li>' for label in GLOBE_LEGEND_MARKETS)}
      </ul>
      <figcaption class="note globe-caption">An illustrative visualization of FORCE LINK’s connections to its reported destination markets. The arcs are schematic and do not represent actual vessel routes or live shipment tracking.</figcaption>
    </figure>
  </div>
</section>"""

    market_items = "\n".join(f"<li>{esc(name)}</li>" for name, _ in MARKETS)
    markets = f"""<section class="section section--off" aria-labelledby="markets-heading">
  <div class="container split">
    <figure class="figure reveal" style="margin:0">
      <img src="{r}assets/img/map.webp" alt="World map with highlighted markers across Asia and Europe" width="1920" height="1080" loading="lazy">
      <figcaption>Illustrative map. Markers show the company's reported destination markets. They do not represent shipment routes.</figcaption>
    </figure>
    <div>
      <p class="eyebrow">Destination markets</p>
      <h2 id="markets-heading">Connecting markets across Asia and Europe</h2>
      <p class="lead">The company's reported destination markets are India, China, Malaysia, Vietnam, Indonesia and Europe.</p>
      <ul class="market-list">
{market_items}
      </ul>
      <p style="margin-top:24px"><a class="link-arrow" href="markets/">Explore our markets</a></p>
    </div>
  </div>
</section>"""

    band = cta_band(r, "Discuss Your Fertilizer Requirements",
                    "Contact our team to discuss your product requirements and potential trading opportunities.")

    body = hero + scale + products + intro + markets + band
    jsonld = [{
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": COMPANY["name"],
        "description": COMPANY["description"],
        "email": COMPANY["email"],
        "telephone": COMPANY["phone_display"],
        "foundingDate": COMPANY["founded"],
        "address": {"@type": "PostalAddress", "addressLocality": "Dubai", "addressCountry": "AE"},
        **({"url": SITE_URL} if SITE_URL else {}),
    }]
    return page(
        "",
        "FORCE LINK GENERAL TRADING LLC | Fertilizer Trading, Dubai",
        "International trading of fertilizers and related raw materials from Dubai, UAE. Phosphate Rock, DAP, SSP, TSP, Urea and Sulfur for markets across Asia and Europe.",
        body,
        current="home",
        jsonld=jsonld,
        scripts=("geo.js", "globe.js"),
    )


def about_page():
    path = "about/"
    r = root_for(path)
    trail = [("Home", ""), ("About", "about/")]
    hero = f"""<section class="page-hero">
  <div class="container">
    {breadcrumbs(path, trail)}
    <p class="eyebrow" style="margin-top:36px">About us</p>
    <h1>A focused international fertilizer trading business</h1>
    <p class="lead">{esc(COMPANY['name'])} is based in Dubai, United Arab Emirates, and was established in {COMPANY['founded']}. The company focuses on the international trading of fertilizers and related raw materials.</p>
  </div>
{banner_html('about', r)}</section>"""

    story = f"""<section class="section">
  <div class="container split">
    <div class="image-panel reveal">
      <img src="{r}assets/img/hero-desktop.webp" alt="Aerial view of a bulk carrier at sea" width="1920" height="1080" loading="lazy">
    </div>
    <div class="prose">
      <p class="eyebrow">Our positioning</p>
      <h2>{esc(COMPANY['tagline'])}</h2>
      <p>FORCE LINK positions itself as an international trading partner connecting fertilizer products with global markets. Our role is commercial: matching product requirements with supply, and keeping communication clear between buyers and partners.</p>
      <p>Our product portfolio covers phosphate rock, DAP, SSP, TSP, urea and sulfur. Each product has its own information page, and we provide technical details on request.</p>
      <p>We are a trading business. We do not describe ourselves as a manufacturer of every product in our portfolio.</p>
    </div>
  </div>
</section>"""

    figures = f"""<section class="section section--off" aria-labelledby="figures-heading">
  <div class="container">
    <div class="section-head">
      <div>
        <p class="eyebrow">Reported commercial figures</p>
        <h2 id="figures-heading">Volumes sold</h2>
      </div>
      <p>Company-reported figures. The 2026 figure covers January to September only and is not a full-year total.</p>
    </div>
  </div>
  <div class="container metrics" style="background:#fff">
    {metric_block('y2025')}
    {metric_block('y2026')}
  </div>
</section>"""

    portfolio_items = "\n".join(
        f'<li><a class="link-arrow" href="{r}products/{p["slug"]}/" style="color:var(--navy)">{esc(p["name"])}</a></li>'
        for p in PRODUCTS
    )
    portfolio = f"""<section class="section" aria-labelledby="portfolio-heading">
  <div class="container split">
    <div>
      <p class="eyebrow">Product portfolio</p>
      <h2 id="portfolio-heading">Six products, each with its own information page</h2>
      <p>Our portfolio is deliberately focused on phosphate, nitrogen and sulfur products that are central to fertilizer supply chains.</p>
    </div>
    <ul class="check-list">
{portfolio_items}
    </ul>
  </div>
</section>"""

    markets = f"""<section class="section section--off" aria-labelledby="about-markets">
  <div class="container split">
    <div>
      <p class="eyebrow">Destination markets</p>
      <h2 id="about-markets">Reported destination markets</h2>
      <p>India, China, Malaysia, Vietnam, Indonesia and Europe. Europe is a regional designation.</p>
      <p><a class="link-arrow" href="{r}markets/">See the markets page</a></p>
    </div>
    <ul class="market-list">
{''.join(f'<li>{esc(n)}</li>' for n, _ in MARKETS)}
    </ul>
  </div>
</section>"""

    values = f"""<section class="section">
  <div class="container">
    <div class="section-head">
      <div>
        <p class="eyebrow">How we work</p>
        <h2>Our approach</h2>
      </div>
    </div>
    <div class="grid grid-3">
      <div class="value"><h3>Clear communication</h3><p>Product information and commercial terms are confirmed directly with you before any commitment.</p></div>
      <div class="value"><h3>A focused portfolio</h3><p>A defined set of six fertilizer products and raw materials, rather than a broad catalogue.</p></div>
      <div class="value"><h3>Lasting relationships</h3><p>We aim to build repeat commercial relationships with buyers and partners across our markets.</p></div>
    </div>
  </div>
</section>"""

    band = cta_band(r, "Discuss your requirements with our team",
                    "Contact us to discuss product requirements, destination markets and potential trading opportunities.")

    body = hero + story + figures + portfolio + markets + values + band
    return page(
        path,
        "About FORCE LINK GENERAL TRADING LLC | Dubai Fertilizer Trader",
        "About FORCE LINK GENERAL TRADING LLC: a Dubai-based international trading company established in 2023, focused on fertilizers and related raw materials.",
        body,
        current="about",
        jsonld=[b for b in [breadcrumb_jsonld(trail)] if b],
    )


def products_index_page():
    path = "products/"
    r = root_for(path)
    trail = [("Home", ""), ("Products", "products/")]
    hero = f"""<section class="page-hero">
  <div class="container">
    {breadcrumbs(path, trail)}
    <p class="eyebrow" style="margin-top:36px">Products</p>
    <h1>Fertilizer and raw material portfolio</h1>
    <p class="lead">Six products across phosphate, nitrogen and sulfur. Technical information, including specifications and documentation, is provided on request.</p>
  </div>
{banner_html('products', r)}</section>"""
    grid = "\n".join(product_card(p, r) for p in PRODUCTS)
    body = hero + f"""<section class="section">
  <div class="container">
    <div class="grid grid-3">
{grid}
    </div>
    <p class="note" style="margin-top:32px">Commercial availability varies. Please contact us to confirm current availability for a specific product and destination.</p>
  </div>
</section>""" + cta_band(r, "Request product information",
                         "Tell us which product you need and where it is required. We will respond with the relevant commercial and technical information.",
                         primary=("Request Product Information", "contact/"))
    return page(
        path,
        "Products | Phosphate Rock, DAP, SSP, TSP, Urea and Sulfur | FORCE LINK",
        "Browse FORCE LINK's fertilizer and raw material portfolio: Phosphate Rock, DAP, SSP, TSP, Urea and Sulfur. Request product information from our Dubai-based team.",
        body,
        current="products",
        jsonld=[b for b in [breadcrumb_jsonld(trail)] if b],
    )


def product_page(p):
    path = f"products/{p['slug']}/"
    r = root_for(path)
    trail = [("Home", ""), ("Products", "products/"), (p["name"], path)]
    hero = f"""<section class="page-hero" style="border-bottom:0;padding-bottom:48px">
  <div class="container grid grid-2 product-hero">
    <div>
      {breadcrumbs(path, trail)}
      <p class="eyebrow" style="margin-top:36px">{esc(p['tag'])}</p>
      <h1>{esc(p['name'])}</h1>
      <p class="lead">{esc(p['lead'])}</p>
      <div class="product-cta">
        <a class="btn btn--gold" href="{r}contact/?product={p['slug']}">Request Product Information</a>
        <a class="btn btn--line" href="{r}contact/">Contact Our Team</a>
      </div>
    </div>
    <div class="product-visual">
      <img src="{r}assets/img/products/{p['slug']}.webp" alt="{esc(p['alt'])}" width="800" height="800">
    </div>
  </div>
{banner_html(p['slug'], r)}</section>"""

    overview = f"""<section class="section">
  <div class="container prose">
    <p class="eyebrow">Overview</p>
    <h2>About {esc(p['title_short'])}</h2>
    <p>{esc(p['overview'][0])}</p>
    <p>{esc(p['overview'][1])}</p>
  </div>
</section>"""

    role = f"""<section class="section section--off">
  <div class="container split">
    <div>
      <p class="eyebrow">Industry role</p>
      <h2>Role in the fertilizer industry</h2>
    </div>
    <p class="lead" style="margin:0">{esc(p['role'])}</p>
  </div>
</section>"""

    uses = "\n".join(f"<li>{esc(u)}</li>" for u in p["uses"])
    applications = f"""<section class="section">
  <div class="container split">
    <div>
      <p class="eyebrow">Typical applications</p>
      <h2>Where it is used</h2>
      <p class="note">{esc(p['uses_note'])}</p>
    </div>
    <ul class="check-list">
{uses}
    </ul>
  </div>
</section>"""

    inquiry = f"""<section class="section section--off" aria-labelledby="inquiry-{p['slug']}">
  <div class="container prose">
    <p class="eyebrow">Commercial inquiries</p>
    <h2 id="inquiry-{p['slug']}">Availability and requirements</h2>
    <div class="callout">
      <p>Commercial availability, packaging options, delivery arrangements and technical documentation are confirmed on request. This page does not list prices, grades, minimum order quantities or delivery times.</p>
      <p style="margin-top:20px"><a class="btn btn--navy" href="{r}contact/?product={p['slug']}">Request Product Information</a></p>
    </div>
  </div>
</section>"""

    others = [q for q in PRODUCTS if q["slug"] != p["slug"]][:3]
    related_cards = "\n".join(product_card(q, r) for q in others)
    related = f"""<section class="section">
  <div class="container">
    <div class="section-head">
      <div>
        <p class="eyebrow">Related products</p>
        <h2>Other products in our portfolio</h2>
      </div>
      <a class="link-arrow" href="{r}products/">All products</a>
    </div>
    <div class="grid grid-3">
{related_cards}
    </div>
  </div>
</section>"""

    band = cta_band(r, f"Discuss your {p['title_short']} requirements",
                    "Contact our team to discuss commercial availability, destination market and the information you need.")

    body = hero + overview + role + applications + inquiry + related + band
    jsonld = [b for b in [breadcrumb_jsonld(trail)] if b]
    return page(
        path,
        f"{p['name']} | Fertilizer Product Information | FORCE LINK",
        f"{p['name']} from FORCE LINK GENERAL TRADING LLC. {p['short']} Request product information from our Dubai-based team.",
        body,
        current="products",
        jsonld=jsonld,
    )


def markets_page():
    path = "markets/"
    r = root_for(path)
    trail = [("Home", ""), ("Markets", "markets/")]
    hero = f"""<section class="page-hero">
  <div class="container">
    {breadcrumbs(path, trail)}
    <p class="eyebrow" style="margin-top:36px">Markets</p>
    <h1>International market focus</h1>
    <p class="lead">FORCE LINK reports destination markets across Asia and Europe. Our trading activity connects fertilizer supply with buyers in these regions.</p>
  </div>
{banner_html('markets', r)}</section>"""

    map_block = f"""<section class="section" style="padding-bottom:40px">
  <div class="container">
    <figure class="figure" style="margin:0">
      <img src="{r}assets/img/map.webp" alt="World map with highlighted markers across Asia and Europe" width="1920" height="1080">
      <figcaption>Illustrative map. Markers indicate the company's reported destination markets. They do not show shipment routes, volumes or customer locations.</figcaption>
    </figure>
  </div>
</section>"""

    cards = "\n".join(
        f"""<div class="value"><h3>{esc(name)}</h3><p>{esc(desc)}</p></div>""" for name, desc in MARKETS
    )
    markets = f"""<section class="section" aria-labelledby="reported-markets">
  <div class="container">
    <div class="section-head">
      <div>
        <p class="eyebrow">Reported destination markets</p>
        <h2 id="reported-markets">India, China, Malaysia, Vietnam, Indonesia and Europe</h2>
      </div>
    </div>
    <div class="grid grid-3">
{cards}
    </div>
  </div>
</section>"""

    commentary = f"""<section class="section section--off">
  <div class="container split">
    <div>
      <p class="eyebrow">Why connectivity matters</p>
      <h2>Working across several regions</h2>
    </div>
    <div class="prose">
      <p>Fertilizer demand follows planting and growing seasons, and buyers in different regions often have different product and delivery requirements. Working across several destination markets allows us to align product requirements with appropriate supply.</p>
      <p>Europe is shown as a regional designation. More specific destination countries are not listed here.</p>
    </div>
  </div>
</section>"""

    band = cta_band(r, "Discuss your market requirements",
                    "Tell us your destination market and product requirements, and our team will respond.")

    body = hero + map_block + markets + commentary + band
    return page(
        path,
        "Markets | India, China, Malaysia, Vietnam, Indonesia, Europe | FORCE LINK",
        "FORCE LINK's reported destination markets: India, China, Malaysia, Vietnam, Indonesia and Europe. Fertilizer trading connected to Asia and Europe.",
        body,
        current="markets",
        jsonld=[b for b in [breadcrumb_jsonld(trail)] if b],
    )


def contact_page():
    path = "contact/"
    r = root_for(path)
    trail = [("Home", ""), ("Contact", "contact/")]
    hero = f"""<section class="page-hero" style="padding-bottom:40px">
  <div class="container">
    {breadcrumbs(path, trail)}
    <p class="eyebrow" style="margin-top:36px">Contact</p>
    <h1>Discuss your requirements</h1>
    <p class="lead">Contact our team to discuss your product requirements and potential trading opportunities.</p>
  </div>
{banner_html('contact', r)}</section>"""

    product_options ='<option value="">Select a product</option>\n' + "\n".join(
        f'<option value="{p["slug"]}">{esc(p["name"])}</option>' for p in PRODUCTS
    )
    market_options = '<option value="">Select a market (optional)</option>\n' + "\n".join(
        f'<option value="{esc(n)}">{esc(n)}</option>' for n, _ in MARKETS
    )

    form = f"""<form class="form" id="inquiry-form" novalidate>
  <div class="row">
    <div class="field">
      <label for="fullName">Full name <span class="req" aria-hidden="true">*</span></label>
      <input id="fullName" name="fullName" type="text" autocomplete="name" required aria-describedby="fullName-error">
      <p class="error" id="fullName-error">Please enter your full name.</p>
    </div>
    <div class="field">
      <label for="company">Company name <span class="req" aria-hidden="true">*</span></label>
      <input id="company" name="company" type="text" autocomplete="organization" required aria-describedby="company-error">
      <p class="error" id="company-error">Please enter your company name.</p>
    </div>
  </div>
  <div class="row">
    <div class="field">
      <label for="email">Business email <span class="req" aria-hidden="true">*</span></label>
      <input id="email" name="email" type="email" autocomplete="email" required aria-describedby="email-error">
      <p class="error" id="email-error">Please enter a valid business email address.</p>
    </div>
    <div class="field">
      <label for="phone">Telephone <span class="muted">(optional)</span></label>
      <input id="phone" name="phone" type="tel" autocomplete="tel">
    </div>
  </div>
  <div class="row">
    <div class="field">
      <label for="product">Product of interest <span class="req" aria-hidden="true">*</span></label>
      <select id="product" name="product" required aria-describedby="product-error">
{product_options}
      </select>
      <p class="error" id="product-error">Please select a product.</p>
    </div>
    <div class="field">
      <label for="market">Destination market <span class="muted">(optional)</span></label>
      <select id="market" name="market">
{market_options}
      </select>
    </div>
  </div>
  <div class="field">
    <label for="quantity">Estimated quantity or requirements <span class="muted">(optional)</span></label>
    <input id="quantity" name="quantity" type="text">
    <p class="hint">For example, an approximate volume or the period you have in mind.</p>
  </div>
  <div class="field">
    <label for="message">Message <span class="req" aria-hidden="true">*</span></label>
    <textarea id="message" name="message" required aria-describedby="message-error"></textarea>
    <p class="error" id="message-error">Please describe your requirements.</p>
  </div>
  <div class="form-actions">
    <button class="btn btn--navy" type="submit">Prepare Inquiry Email</button>
    <span class="note">Fields marked * are required.</span>
  </div>
  <div class="form-status" id="form-status" role="status" aria-live="polite"></div>
  <div class="summary-wrap" id="summary-wrap" hidden>
    <label for="inquiry-summary" style="font-weight:600;color:var(--navy);display:block;margin-bottom:6px">Your inquiry details</label>
    <textarea id="inquiry-summary" readonly rows="10" style="width:100%;font:inherit;padding:12px;border:1px solid #CBD5E1;border-radius:4px"></textarea>
  </div>
</form>"""

    body = hero + f"""<section class="section" style="padding-top:24px">
  <div class="container grid grid-2" style="gap:56px;align-items:start">
    <div>
      <p class="eyebrow">Company details</p>
      <dl class="contact-facts">
        <div><dt>Company</dt><dd>{esc(COMPANY['name'])}</dd></div>
        <div><dt>Email</dt><dd><a href="mailto:{COMPANY['email']}">{COMPANY['email']}</a></dd></div>
        <div><dt>Telephone</dt><dd><a href="tel:{COMPANY['phone_tel']}">{COMPANY['phone_display']}</a></dd></div>
        <div><dt>Location</dt><dd>{esc(COMPANY['location'])}</dd></div>
      </dl>
      <h2 style="margin-top:40px;font-size:1.5rem">Business inquiries</h2>
      <p>Include the product, destination market and any volume or timing requirements. The more detail you share, the more useful our response.</p>
      <div class="privacy" style="border-top:0;padding-top:0">
        <p><strong>How your inquiry is handled.</strong> This is a static website, so the form does not send your details to a server. When you submit, your browser prepares a summary of your inquiry and opens your own email application addressed to {COMPANY['email']}. You review the message and send it yourself. Please do not include sensitive personal information in the form.</p>
        <p>If you have questions about how your details are used once you have sent an email, please contact us at the address above.</p>
      </div>
    </div>
    <div class="form-card">
      <h2 style="font-size:1.5rem">Send an inquiry</h2>
      <p class="note" style="margin-bottom:24px">All fields are reviewed by our team. Required fields are marked.</p>
{form}
    </div>
  </div>
</section>"""

    return page(
        path,
        "Contact FORCE LINK GENERAL TRADING LLC | Dubai",
        "Contact FORCE LINK GENERAL TRADING LLC in Dubai, UAE. Email info@forcelink-ae.com or call +971 52 211 7950 to discuss fertilizer product requirements.",
        body,
        current="contact",
        jsonld=[b for b in [breadcrumb_jsonld(trail)] if b],
        scripts=(),
    )


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------


def write_svg_variants():
    src = (SRC / "logosvg.svg").read_text(encoding="utf-8")
    open_tag = re.search(r"<svg[^>]*>", src).group(0)

    def rewrite(tag, width, height, viewbox):
        new = re.sub(r'\swidth="[^"]*"', f' width="{width}"', tag, count=1)
        new = re.sub(r'\sheight="[^"]*"', f' height="{height}"', new, count=1)
        new = re.sub(r'\sviewBox="[^"]*"', f' viewBox="{viewbox}"', new, count=1)
        return new

    # Header/footer wordmark: crop to the logo bounds. Geometry and colours are untouched.
    wordmark = src.replace(open_tag, rewrite(open_tag, 1090, 140, "205 680 1090 140"), 1)
    (OUT / "assets/img/forcelink-logo.svg").write_text(wordmark, encoding="utf-8")

    # Favicon: the square emblem only.
    icon = src.replace(open_tag, rewrite(open_tag, 124, 124, "213 688 124 124"), 1)
    (OUT / "assets/img/favicon.svg").write_text(icon, encoding="utf-8")


def optimise_images():
    img_dir = OUT / "assets/img"
    prod_dir = img_dir / "products"
    prod_dir.mkdir(parents=True, exist_ok=True)

    def save_webp(src_name, dst, width=None, quality=80, keep_alpha=False):
        im = Image.open(SRC / src_name)
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA" if keep_alpha else "RGB")
        if width and im.width > width:
            height = round(im.height * width / im.width)
            im = im.resize((width, height), Image.LANCZOS)
        im.save(dst, "WEBP", quality=quality, method=6)

    save_webp("HeroDesktop.png", img_dir / "hero-desktop.webp", width=1920, quality=78)
    save_webp("HeroMobile.png", img_dir / "hero-mobile.webp", width=1080, quality=78)
    save_webp("MapDesktop.png", img_dir / "map.webp", width=1920, quality=84)

    banner_dir = img_dir / "banners"
    banner_dir.mkdir(parents=True, exist_ok=True)
    for key, (src_name, _alt, _pos) in BANNER_IMAGES.items():
        save_webp(src_name, banner_dir / f"{key}.webp", width=1050, quality=82)

    for p in PRODUCTS:
        keep = p["slug"] == "phosphate-rock"  # transparent background
        save_webp(p["source"], prod_dir / f"{p['slug']}.webp", width=800, quality=82, keep_alpha=keep)

    # Footer logo: supplied reversed (white) wordmark for dark backgrounds, cropped to its visible bounds. Not recoloured or redrawn.
    global EMBLEM_SIZE
    emblem = Image.open(SRC / "footer-logo-reversed.png").convert("RGBA")
    alpha_box = emblem.getchannel("A").getbbox()
    if alpha_box:
        pad = 4
        l, t, r, b = alpha_box
        emblem = emblem.crop((max(0, l - pad), max(0, t - pad), min(emblem.width, r + pad), min(emblem.height, b + pad)))
    emblem.save(img_dir / "forcelink-footer-logo.png", "PNG", optimize=True)
    display_w = 250
    EMBLEM_SIZE = (display_w, round(emblem.height * display_w / emblem.width))

    # Social sharing image (1200x630), centred crop of the hero.
    hero = Image.open(SRC / "HeroDesktop.png").convert("RGB")
    target_ratio = 1200 / 630
    w, h = hero.size
    new_w = int(h * target_ratio)
    left = (w - new_w) // 2
    og = hero.crop((left, 0, left + new_w, h)).resize((1200, 630), Image.LANCZOS)
    og.save(img_dir / "og-image.jpg", "JPEG", quality=82, optimize=True)


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def write(rel, content):
    dest = OUT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    shutil.copytree(STATIC / "assets", OUT / "assets")
    (OUT / "assets/img").mkdir(parents=True, exist_ok=True)
    write_svg_variants()
    optimise_images()

    write("index.html", home_page())
    write("about/index.html", about_page())
    write("products/index.html", products_index_page())
    for p in PRODUCTS:
        write(f"products/{p['slug']}/index.html", product_page(p))
    write("markets/index.html", markets_page())
    write("contact/index.html", contact_page())

    # GitHub Pages: serve files starting with underscores; no Jekyll processing.
    write(".nojekyll", "")

    robots = "User-agent: *\nAllow: /\n"
    if SITE_URL:
        robots += f"\nSitemap: {SITE_URL}sitemap.xml\n"
    write("robots.txt", robots)

    if SITE_URL:
        paths = [""] + ["about/", "products/", "markets/", "contact/"] + [
            f"products/{p['slug']}/" for p in PRODUCTS
        ]
        entries = "\n".join(f"  <url><loc>{SITE_URL}{p}</loc></url>" for p in paths)
        write(
            "sitemap.xml",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{entries}\n</urlset>\n",
        )

    print(f"Built {OUT} ({sum(1 for _ in OUT.rglob('*.html'))} HTML pages)")
    if not SITE_URL:
        print("Note: SITE_URL is not set. Canonical, Open Graph, sitemap and breadcrumb structured data were skipped.")


if __name__ == "__main__":
    main()
