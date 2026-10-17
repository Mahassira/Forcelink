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

from PIL import Image, ImageDraw, ImageFont

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
    "phone_display": "+971 56 661 4040",
    "phone_tel": "+971566614040",
    "phone2_display": "+20 102 050 0504",
    "phone2_tel": "+201020500504",
    "tagline": "Connecting Global Fertilizer Markets",
    "description": (
        "FORCE LINK GENERAL TRADING LLC is an Egyptian international trading company with branches in "
        "Cairo, Egypt and Dubai, United Arab Emirates, focused on fertilizers and related raw materials."
    ),
}

# Branch offices: shown in the footer, on the contact page and in structured data.
BRANCHES = [
    {"label": "Dubai branch", "city": "Dubai", "country": "AE",
     "address": "Court Tower, Office No. 2004, Business Bay, Dubai, United Arab Emirates"},
    {"label": "Cairo branch", "city": "Cairo", "country": "EG",
     "address": "Office 2, 1st floor, ENAWALKS Mall, 5th Settlement, New Cairo, Egypt, 11865"},
]

def branch_items_html():
    return "".join(f'<li><strong>{esc_(b["label"])}:</strong> {esc_(b["address"])}</li>' for b in BRANCHES)

def branch_rows_html():
    return "".join(f'<div><dt>{esc_(b["label"])}</dt><dd>{esc_(b["address"])}</dd></div>' for b in BRANCHES)

def phone_links_html():
    return (f'<a href="tel:{COMPANY["phone_tel"]}">{COMPANY["phone_display"]}</a><br>'
            f'<a href="tel:{COMPANY["phone2_tel"]}">{COMPANY["phone2_display"]}</a>')


def phone_items_html():
    return (f'<li><a href="tel:{COMPANY["phone_tel"]}">{COMPANY["phone_display"]}</a></li>\n'
            f'          <li><a href="tel:{COMPANY["phone2_tel"]}">{COMPANY["phone2_display"]}</a></li>')


def esc_(v):
    return html.escape(str(v), quote=True)

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
    ("Brazil", "Reported destination market in South America."),
    ("Europe", "Reported destination market. Shown as a regional designation."),
]

EMBLEM_SIZE = (250, 29)  # display size of the footer logo; set by optimise_images()

GLOBE_LEGEND_MARKETS = ["India", "China", "Malaysia", "Vietnam", "Indonesia", "Brazil", "Europe (region)"]

PRODUCTS = [
    {
        "slug": "phosphate-rock",
        "name": "Phosphate Rock",
        "title_short": "Phosphate Rock",
        "tag": "Raw material",
        "source": "Phosphate_Rock.png",
        "alt": "Sandy-tan phosphate rock powder piled on a white background",
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
    ("Careers", "careers/", "careers"),
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
      <img src="{root}assets/img/forcelink-logo.png" alt="{esc(COMPANY['name'])}" width="300" height="36">
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
          <img class="footer-logo" src="{root}assets/img/forcelink-footer-logo.png" alt="{esc(COMPANY['name'])}" width="{EMBLEM_SIZE[0]}" height="{EMBLEM_SIZE[1]}">
        </div>
        <p class="footer-desc">International trading of fertilizers and related raw materials, with branches in Cairo, Egypt and Dubai, United Arab Emirates.</p>
      </div>
      <nav aria-label="Footer: company">
        <h3>Company</h3>
        <ul>
          <li><a href="{root}">Home</a></li>
          <li><a href="{root}about/">About</a></li>
          <li><a href="{root}markets/">Markets</a></li>
          <li><a href="{root}careers/">Careers</a></li>
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
          {phone_items_html()}
{branch_items_html()}
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© <span data-year>{2026}</span> {esc(COMPANY['name'])}. All rights reserved.</span>
      <span>Cairo, Egypt · Dubai, United Arab Emirates</span>
    </div>
  </div>
</footer>"""


# Page headers for inner pages. Four supplied photographs, each with a desktop and a mobile version.
# HEADER_IMAGES: key -> (desktop file, mobile file, alt text, desktop object-position, mobile object-position)
HEADER_IMAGES = {
    "seeding": ("header-seeding.jpg", "header-seeding-mobile.jpg",
                "A hand sowing granules onto soil", "62% 50%", "50% 62%"),
    "hand-plant": ("header-hand-plant.jpg", "header-hand-plant-mobile.jpg",
                   "A hand holding fertilizer granules beside a young plant", "50% 50%", "50% 45%"),
    "granules": ("header-granules.jpg", "header-granules-mobile.jpg",
                 "Fertilizer granules in white, pink and brown", "50% 50%", "50% 50%"),
    "contact": ("header-contact.jpg", "header-contact-mobile.jpg",
                "A keyboard with blue keys marked contact us, phone and email", "50% 50%", "50% 50%"),
    "ship": ("HeroDesktop.png", "HeroMobile.png",
             "Aerial view of a bulk carrier at sea, its cargo hatches and deck marked with the FORCE LINK emblem", "center", "center"),
    "career": ("desk-career.webp", "design-career.jpg",
               "Four colleagues look at a laptop together in a bright office", "50% 40%", "50% 50%"),
    "plant": ("header-plant.jpg", "header-plant-mobile.jpg",
              "An industrial processing plant beside water, with a quarried hillside in the foreground", "50% 60%", "40% 50%"),
}
# Which photograph each page uses. Change a value here to swap the image for a page.
PAGE_BANNER = {
    "about": "hand-plant",
    "markets": "ship",
    "contact": "contact",
    "products": "granules",
    "phosphate-rock": "plant",
    "dap": "hand-plant",
    "ssp": "granules",
    "tsp": "seeding",
    "urea": "granules",
    "sulfur": "plant",
    "career": "career",
}


def soil_html(root, desk_key, mobile_file):
    """Two continuation strips: one for desktop, one for phones. Each starts at the header's bottom edge."""
    return (
        f'<div class="hero-soil hero-soil--d" aria-hidden="true" style="background-image:url(\'{root}assets/img/headers/desk-{desk_key}-soil.webp\')"></div>'
        f'<div class="hero-soil hero-soil--m" aria-hidden="true" style="background-image:url(\'{root}assets/img/headers/{mobile_file}\')"></div>'
    )


DESIGN_HEADERS = ("about", "markets", "products", "contact", "career")  # phone headers designed with their text baked in


HOME_LEAD = ("Connecting fertilizer products with international markets through a focused approach "
             "to global trading and commercial relationships.")

DESIGN_TEXT = {
    "about": ("A focused international fertilizer trading business", "FORCE LINK GENERAL TRADING LLC is an international trading company with branches in Cairo, Egypt and Dubai, United Arab Emirates, focused on fertilizers and related raw materials."),
    "products": ("Fertilizer and raw material portfolio", "Six main products across phosphate, nitrogen and sulfur. Technical information, including specifications and documentation, is provided on request."),
    "markets": ("International market focus", "FORCE LINK reports destination markets across Asia, Europe and South America. Our trading activity connects fertilizer supply with buyers in these regions."),
    "contact": ("Discuss your requirements", "Contact our team to discuss your product requirements and potential trading opportunities."),
    "career": ("Join the FORCE LINK team", "We are a growing international trading company with offices in Cairo and Dubai. Send us your application and tell us about the role that suits you."),
}


# Phone headers: the supplied photographs have no text, so the page text is set into a navy panel at the centre.
FONT_DIR = ROOT / "build" / "fonts"


def _wrap(text, font, width, draw):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and draw.textlength(trial, font=font) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def bake_mobile_header(src_name, title, lead, sub=None):
    im = Image.open(SRC / src_name).convert("RGB")
    W, H = im.size
    draw = ImageDraw.Draw(im)
    f_title = ImageFont.truetype(str(FONT_DIR / "Inter-SemiBold.otf"), 68)
    f_sub = ImageFont.truetype(str(FONT_DIR / "Inter-SemiBold.otf"), 40)
    f_lead = ImageFont.truetype(str(FONT_DIR / "Inter-Regular.otf"), 40)
    box_w = round(W * 0.8)
    pad = 56
    inner = box_w - 2 * pad
    t_lines = _wrap(title, f_title, inner, draw)
    s_lines = _wrap(sub, f_sub, inner, draw) if sub else []
    l_lines = _wrap(lead, f_lead, inner, draw)
    lh_t, lh_s, lh_l = 84, 56, 58
    height = (pad + 6 + 36 + len(t_lines) * lh_t
              + (24 + len(s_lines) * lh_s if s_lines else 0)
              + 24 + len(l_lines) * lh_l + pad)
    x0, y0 = (W - box_w) // 2, (H - height) // 2
    draw.rectangle((x0, y0, x0 + box_w, y0 + height), fill=(14, 48, 93))
    gold, white, soft = (214, 167, 44), (255, 255, 255), (214, 222, 233)
    y = y0 + pad
    draw.rectangle((x0 + pad, y, x0 + pad + 96, y + 6), fill=gold)
    y += 36
    for ln in t_lines:
        draw.text((x0 + pad, y), ln, font=f_title, fill=white)
        y += lh_t
    if s_lines:
        y += 24
        for ln in s_lines:
            draw.text((x0 + pad, y), ln, font=f_sub, fill=gold)
            y += lh_s
    y += 24
    for ln in l_lines:
        draw.text((x0 + pad, y), ln, font=f_lead, fill=soft)
        y += lh_l
    return im


def page_header(key, root, path, trail, eyebrow, h1, lead):
    name = PAGE_BANNER[key]
    desk, mob, alt, desk_pos, mob_pos = HEADER_IMAGES[name]
    base = name
    mobile_base = f"{name}-mobile"
    if key in DESIGN_HEADERS:
        mobile_base = f"design-{key}"
        soil = "" if key == "career" else soil_html(root, key, f"design-{key}-soil.webp")  # the careers photo has no soil edge to continue
        h1, lead = DESIGN_TEXT[key]
        return f"""<section class="page-header page-header--design">
  <picture>
    <source media="(max-width: 760px)" srcset="{root}assets/img/headers/{mobile_base}.webp" type="image/webp">
    <img class="page-header__img" src="{root}assets/img/headers/desk-{key}.webp" alt="{esc(alt)}" width="1920" height="1080" style="--pos-d:{desk_pos};--pos-m:{mob_pos}" fetchpriority="high">
  </picture>
  <div class="container page-header__content">
    {breadcrumbs(path, trail)}
    <p class="eyebrow">{esc(eyebrow)}</p>
    <h1>{esc(h1)}</h1>
    <p class="lead">{esc(lead)}</p>
  </div>
</section>
{soil}
"""
    return f"""<section class="page-header">
  <picture>
    <source media="(max-width: 760px)" srcset="{root}assets/img/headers/{mobile_base}.webp" type="image/webp">
    <img class="page-header__img" src="{root}assets/img/headers/{base}.webp" alt="{esc(alt)}" width="1920" height="1080" style="--pos-d:{desk_pos};--pos-m:{mob_pos}" fetchpriority="high">
  </picture>
  <div class="container page-header__content">
    {breadcrumbs(path, trail)}
    <p class="eyebrow">{esc(eyebrow)}</p>
    <h1>{esc(h1)}</h1>
    <p class="lead">{lead}</p>
  </div>
</section>
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
  <div class="thumb"><img src="{root}assets/img/products/{p['slug']}.webp" alt="{esc(p['alt'])}" width="800" height="800"></div>
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



# Markets map: supplied illustration, 1000 x 1000. Marker centres are in the image's pixel coordinates.
MM_W, MM_H = 1000, 1000
MM_BASE = (616, 450)   # FLT Dubai (centre of the box)
MM_CAIRO = (534, 449)  # FLT Cairo (centre of the box)
MM_ROUTES = [  # name, marker x, marker y, pulse delay (s); each route runs from the Dubai box to its market
    ("Europe", 500, 379, 0.0),
    ("China", 809, 435, 0.6),
    ("India", 704, 475, 1.2),
    ("Vietnam", 780, 475, 1.8),
    ("Malaysia", 824, 515, 2.4),
    ("Indonesia", 780, 547, 3.0),
    ("Brazil", 332, 568, 3.6),
]


def market_map_html(root):
    bx, by = MM_BASE
    cx, cy = MM_CAIRO
    tracks, flows, pulses = [], [], []
    for name, x, y, delay in MM_ROUTES:
        d = f"M{bx},{by} L{x},{y}"
        tracks.append(f'<path class="mm-track" d="{d}"/>')
        flows.append(f'<path class="mm-flow" d="{d}" style="animation-delay:{delay}s"/>')
        pulses.append(f'<circle class="mm-pulse" cx="{x}" cy="{y}" r="8" style="animation-delay:{delay}s"/>')
    # Gold connector between the Cairo and Dubai boxes
    link = f"M{cx + 13},{cy} L{bx - 13},{by}"
    tracks.append(f'<path class="mm-track" d="{link}"/>')
    flows.append(f'<path class="mm-flow" d="{link}" style="animation-delay:0s"/>')
    pulses.append(f'<circle class="mm-pulse mm-pulse--base" cx="{bx}" cy="{by}" r="8" style="animation-delay:0s"/>')
    pulses.append(f'<circle class="mm-pulse mm-pulse--base" cx="{cx}" cy="{cy}" r="8" style="animation-delay:1.5s"/>')
    inner = ''.join(tracks) + ''.join(flows) + ''.join(pulses)
    return f"""<figure class="market-map" style="margin:0">
  <div class="market-map__frame" style="--mm-ar:{MM_W}/{MM_H}">
    <picture>
      <img src="{root}assets/img/markets-map.webp" alt="World map showing FORCE LINK’s offices in Cairo and Dubai, with illustrative gold routes to reported destination markets in Europe, China, India, Vietnam, Malaysia, Indonesia and Brazil." width="{MM_W}" height="{MM_H}">
    </picture>
    <svg class="market-map__svg market-map__svg--d" viewBox="0 0 {MM_W} {MM_H}" aria-hidden="true" focusable="false">{inner}</svg>
  </div>
  <figcaption class="note market-map__caption">An illustrative visualization of FORCE LINK’s connections to its reported destination markets. The arcs are schematic and do not represent actual vessel routes or live shipment tracking.</figcaption>
</figure>
"""


def home_page():
    r = "./"
    hero = f"""<section class="hero hero--image">
  <picture>
    <source media="(max-width: 760px)" srcset="{r}assets/img/headers/home-mobile.webp" type="image/webp">
    <img class="hero-img" src="{r}assets/img/headers/desk-home.webp" alt="FORCE LINK General Trading. Connecting global fertilizer markets. A hand sowing granules onto soil." width="1920" height="1080" fetchpriority="high">
  </picture>
  <div class="container hero-content">
    <h1>{esc(COMPANY['name'])}</h1>
    <p class="hero-sub">{esc(COMPANY['tagline'])}</p>
    <p class="lead">{esc(HOME_LEAD)}</p>
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
      <h2 id="intro-heading">Connecting Markets Across Egypt and the UAE</h2>
      <p class="lead">FORCE LINK is an Egyptian international trading company, with branches in Egypt and the United Arab Emirates, including Cairo and Dubai.</p>
      <p>We specialize in the international trading of fertilizers and related raw materials, connecting suppliers with buyers across Asia and Europe. Our approach is built on clear product information, transparent commercial terms, and direct communication to support trading opportunities across our markets.</p>
      <p><a class="link-arrow" href="about/">Learn More About Us</a></p>
    </div>
  </div>
</section>"""

    market_items = "\n".join(f"<li>{esc(name)}</li>" for name, _ in MARKETS)
    markets = f"""<section class="section section--off" aria-labelledby="markets-heading">
  <div class="container split">
    {market_map_html(r)}
    <div>
      <p class="eyebrow">Destination markets</p>
      <h2 id="markets-heading">Connecting markets across Asia, Europe and South America</h2>
      <p class="lead">The company's reported destination markets are India, China, Malaysia, Vietnam, Indonesia, Brazil and Europe.</p>
      <ul class="market-list">
{market_items}
      </ul>
      <p style="margin-top:24px"><a class="link-arrow" href="markets/">Explore our markets</a></p>
    </div>
  </div>
</section>"""

    band = cta_band(r, "Discuss Your Fertilizer Requirements",
                    "Contact our team to discuss your product requirements and potential trading opportunities.")

    soil = soil_html("./", "home", "home-soil.webp")
    body = hero + soil + products + intro + markets + band
    jsonld = [{
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": COMPANY["name"],
        "description": COMPANY["description"],
        "email": COMPANY["email"],
        "telephone": COMPANY["phone_display"],
        "address": [
            {"@type": "PostalAddress", "streetAddress": b["address"],
             "addressLocality": b["city"], "addressCountry": b["country"]}
            for b in BRANCHES
        ],
        **({"url": SITE_URL} if SITE_URL else {}),
    }]
    return page(
        "",
        "FORCE LINK GENERAL TRADING LLC | Fertilizer Trading, Cairo and Dubai",
        "International trading of fertilizers and related raw materials from Cairo, Egypt and Dubai, UAE. Phosphate Rock, DAP, SSP, TSP, Urea and Sulfur for markets across Asia, Europe and South America.",
        body,
        current="home",
        jsonld=jsonld,
        scripts=(),
    )


def about_page():
    path = "about/"
    r = root_for(path)
    trail = [("Home", ""), ("About", "about/")]
    hero = page_header("about", r, path, trail, "About us",
                       "A focused international fertilizer trading business",
                       f"{esc(COMPANY['name'])} is an Egyptian international trading company with branches in Cairo and Dubai. The company focuses on the international trading of fertilizers and related raw materials.")

    story = f"""<section class="section">
  <div class="container">
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
      <p>India, China, Malaysia, Vietnam, Indonesia, Brazil and Europe. Europe is a regional designation.</p>
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

    vision = f"""<section class="section" aria-label="Our value and vision">
  <div class="container grid grid-2 vision-grid">
    <div class="vision-box">
      <h2>Our Value</h2>
      <p>We connect buyers with suitable products and sourcing opportunities through clear communication and tailored commercial solutions.</p>
    </div>
    <div class="vision-box">
      <h2>Our Vision</h2>
      <p>To build trusted, long-term partnerships and strengthen our presence in global fertilizer markets.</p>
    </div>
  </div>
</section>"""

    body = hero + story + vision + figures + portfolio + markets + values + band
    return page(
        path,
        "About FORCE LINK GENERAL TRADING LLC | Cairo and Dubai Fertilizer Trader",
        "About FORCE LINK GENERAL TRADING LLC: an Egyptian international trading company with branches in Cairo and Dubai, focused on fertilizers and related raw materials.",
        body,
        current="about",
        jsonld=[b for b in [breadcrumb_jsonld(trail)] if b],
    )


def products_index_page():
    path = "products/"
    r = root_for(path)
    trail = [("Home", ""), ("Products", "products/")]
    hero = page_header("products", r, path, trail, "Products",
                       "Fertilizer and raw material portfolio",
                       "Six products across phosphate, nitrogen and sulfur. Technical information, including specifications and documentation, is provided on request.")
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
        "Browse FORCE LINK's fertilizer and raw material portfolio: Phosphate Rock, DAP, SSP, TSP, Urea and Sulfur. Request product information from our team in Cairo and Dubai.",
        body,
        current="products",
        jsonld=[b for b in [breadcrumb_jsonld(trail)] if b],
    )


def product_page(p):
    path = f"products/{p['slug']}/"
    r = root_for(path)
    trail = [("Home", ""), ("Products", "products/"), (p["name"], path)]
    hero = f"""<section class="section product-intro">
  <div class="container">
    {breadcrumbs(path, trail)}
    <figure class="product-intro__figure">
      <img src="{r}assets/img/products/{p['slug']}.webp" alt="{esc(p['alt'])}" width="800" height="800">
    </figure>
    <div class="product-intro__text">
      <p class="eyebrow">{esc(p['tag'])}</p>
      <h1>{esc(p['name'])}</h1>
      <p class="lead">{esc(p['lead'])}</p>
      <div class="product-cta">
        <a class="btn btn--gold" href="{r}contact/?product={p['slug']}">Request Product Information</a>
        <a class="btn btn--line" href="{r}contact/">Contact Our Team</a>
      </div>
    </div>
  </div>
</section>"""

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
        f"{p['name']} from FORCE LINK GENERAL TRADING LLC. {p['short']} Request product information from our team in Cairo and Dubai.",
        body,
        current="products",
        jsonld=jsonld,
    )


def markets_page():
    path = "markets/"
    r = root_for(path)
    trail = [("Home", ""), ("Markets", "markets/")]
    hero = page_header("markets", r, path, trail, "Markets",
                       "International market focus",
                       "FORCE LINK reports destination markets across Asia, Europe and South America. Our trading activity connects fertilizer supply with buyers in these regions.")

    map_block = f"""<section class="section" style="padding-bottom:40px">
  <div class="container">
{market_map_html(r)}
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
        <h2 id="reported-markets">India, China, Malaysia, Vietnam, Indonesia, Brazil and Europe</h2>
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
        "Markets | India, China, Malaysia, Vietnam, Indonesia, Brazil, Europe | FORCE LINK",
        "FORCE LINK's reported destination markets: India, China, Malaysia, Vietnam, Indonesia, Brazil and Europe. Fertilizer trading connected to Asia, Europe and South America.",
        body,
        current="markets",
        jsonld=[b for b in [breadcrumb_jsonld(trail)] if b],
    )


def contact_page():
    path = "contact/"
    r = root_for(path)
    trail = [("Home", ""), ("Contact", "contact/")]
    hero = page_header("contact", r, path, trail, "Contact",
                       "Discuss your requirements",
                       "Contact our team to discuss your product requirements and potential trading opportunities.")

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
        <div><dt>Telephone</dt><dd>{phone_links_html()}</dd></div>
        {branch_rows_html()}
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
        "Contact FORCE LINK GENERAL TRADING LLC | Cairo and Dubai",
        "Contact FORCE LINK GENERAL TRADING LLC, with offices in Cairo, Egypt and Dubai, UAE. Email info@forcelink-ae.com or call +971 56 661 4040 or +20 102 050 0504 to discuss fertilizer product requirements.",
        body,
        current="contact",
        jsonld=[b for b in [breadcrumb_jsonld(trail)] if b],
        scripts=(),
    )


def career_page():
    path = "careers/"
    r = root_for(path)
    trail = [("Home", ""), ("Careers", "careers/")]
    hero = page_header("career", r, path, trail, "Careers",
                       "Join the FORCE LINK team",
                       DESIGN_TEXT["career"][1])

    intro = f"""<section class="section" aria-labelledby="career-intro">
  <div class="container split">
    <div>
      <p class="eyebrow">Working with us</p>
      <h2 id="career-intro">A focused team across Cairo and Dubai</h2>
    </div>
    <div class="prose">
      <p>{esc(COMPANY['name'])} is an international fertilizer trading company with branches in Cairo, Egypt and Dubai, United Arab Emirates. We work across Asia, Europe and South America.</p>
      <p>We are interested in hearing from people with experience in trading, commercial work, logistics or administration. If you do not see a role that matches your background, send us your CV anyway.</p>
    </div>
  </div>
</section>"""

    steps = """<section class="section section--off" aria-labelledby="how-apply">
  <div class="container">
    <div class="section-head">
      <div>
        <p class="eyebrow">How to apply</p>
        <h2 id="how-apply">Three simple steps</h2>
      </div>
    </div>
    <div class="grid grid-3">
      <div class="value"><h3>1. Complete the form</h3><p>Fill in your details and describe the role you are interested in below.</p></div>
      <div class="value"><h3>2. Review the email</h3><p>Your email app opens with your details filled in, addressed to our team.</p></div>
      <div class="value"><h3>3. Attach your CV</h3><p>Attach your CV as a PDF to that email, then send it. Nothing is sent from this website by itself.</p></div>
    </div>
  </div>
</section>"""

    def field(fid, label, typ="text", required=False, hint=""):
        req = ' <span class="req" aria-hidden="true">*</span>' if required else ""
        attrs = " required" if required else ""
        err = f'<p class="error" id="{fid}-error">Please enter a valid {esc(label.lower())}.</p>' if required else ""
        extra = f'<p class="hint">{esc(hint)}</p>' if hint else ""
        return f"""  <div class="field">
    <label for="{fid}">{esc(label)}{req}</label>
    <input id="{fid}" name="{fid}" type="{typ}"{attrs} aria-describedby="{fid}-error">
    {extra}{err}
  </div>"""

    form = f"""<form class="form" id="career-form" novalidate>
{field('fullName', 'Full name', required=True)}
{field('email', 'Email', 'email', required=True)}
{field('phone', 'Telephone', 'tel', hint='Include the country code, for example +20 or +971.')}
  <div class="field">
    <label for="preferredLocation">Preferred location</label>
    <select id="preferredLocation" name="preferredLocation">
      <option value="No preference">No preference</option>
      <option value="Cairo, Egypt">Cairo, Egypt</option>
      <option value="Dubai, United Arab Emirates">Dubai, United Arab Emirates</option>
    </select>
  </div>
{field('position', 'Position of interest', hint='Enter the role you are applying for, or leave it general.')}
  <div class="field">
    <label for="message">Cover note <span class="req" aria-hidden="true">*</span></label>
    <textarea id="message" name="message" required aria-describedby="message-error"></textarea>
    <p class="error" id="message-error">Please write a short cover note.</p>
  </div>
  <div class="form-actions">
    <button class="btn btn--navy" type="submit">Prepare Application Email</button>
    <span class="note">Fields marked * are required.</span>
  </div>
  <div class="form-status" id="career-status" role="status" aria-live="polite"></div>
  <div class="summary-wrap" id="career-summary-wrap" hidden>
    <label for="career-summary" style="font-weight:600;color:var(--navy);display:block;margin-bottom:6px">Your application details</label>
    <textarea id="career-summary" readonly rows="10" style="width:100%;font:inherit;padding:12px;border:1px solid #CBD5E1;border-radius:4px"></textarea>
  </div>
</form>"""

    apply_section = f"""<section class="section" aria-labelledby="apply-heading">
  <div class="container grid grid-2" style="gap:56px;align-items:start">
    <div>
      <p class="eyebrow">Send your application</p>
      <h2 id="apply-heading">Application form</h2>
      <p>Your application is sent by email to <a href="mailto:{COMPANY['email']}">{COMPANY['email']}</a>. Please attach your CV as a PDF before you press send.</p>
      <div class="privacy" style="border-top:0;padding-top:0">
        <p><strong>How your application is handled.</strong> This is a static website, so the form does not send your details to a server. When you submit, your browser prepares a summary and opens your own email application. You review the message, attach your CV and send it yourself. Please do not include sensitive personal information beyond what your application needs.</p>
      </div>
    </div>
    <div class="form-card">
      <h2 style="font-size:1.5rem">Apply now</h2>
      <p class="note" style="margin-bottom:24px">Required fields are marked.</p>
{form}
    </div>
  </div>
</section>"""

    body = hero + intro + steps + apply_section
    return page(
        path,
        "Careers | Join FORCE LINK GENERAL TRADING LLC",
        "Careers at FORCE LINK GENERAL TRADING LLC, an international fertilizer trading company with offices in Cairo, Egypt and Dubai, UAE. Apply by email.",
        body,
        current="careers",
        jsonld=[b for b in [breadcrumb_jsonld(trail)] if b],
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
    (img_dir / "headers").mkdir(parents=True, exist_ok=True)
    for _k in ("home", "about", "products", "markets", "contact", "career"):
        _w = Image.open(SRC / f"desk-{_k}.webp").convert("RGB")
        _w.save(img_dir / "headers" / f"desk-{_k}.webp", "WEBP", quality=82, method=6)
        _ws = _w.crop((0, _w.height - 120, _w.width, _w.height))
        _ws.transpose(Image.FLIP_TOP_BOTTOM).save(img_dir / "headers" / f"desk-{_k}-soil.webp", "WEBP", quality=80, method=6)
    for _k in DESIGN_HEADERS:
        _d = bake_mobile_header(f"design-{_k}.jpg", *DESIGN_TEXT[_k])
        _d.resize((1080, round(_d.height * 1080 / _d.width)), Image.LANCZOS).save(img_dir / "headers" / f"design-{_k}.webp", "WEBP", quality=82, method=6)
        _strip = _d.crop((0, _d.height - 420, _d.width, _d.height))
        _strip.transpose(Image.FLIP_TOP_BOTTOM).save(img_dir / "headers" / f"design-{_k}-soil.webp", "WEBP", quality=82, method=6)
    _home = Image.open(SRC / "home-mobile.jpg").convert("RGB")
    # Mirror the soil band so its top row equals the header image's bottom row (no visible seam).
    _soil = _home.crop((0, _home.height - 420, _home.width, _home.height))
    _soil.transpose(Image.FLIP_TOP_BOTTOM).save(img_dir / "headers" / "home-soil.webp", "WEBP", quality=82, method=6)
    _home.save(img_dir / "headers" / "home-mobile.webp", "WEBP", quality=82, method=6)
    save_webp("MapDesktop.png", img_dir / "map.webp", width=1920, quality=84)
    _mm_full = Image.open(SRC / "markets-map.png").convert("RGB")
    _mm_full.save(img_dir / "markets-map.webp", "WEBP", quality=88, method=6)

    save_webp("about-plant.jpg", img_dir / "about-plant.webp", width=1000, quality=84)

    header_dir = img_dir / "headers"
    header_dir.mkdir(parents=True, exist_ok=True)
    for key, (desk, mob, _alt, _dp, _mp) in HEADER_IMAGES.items():
        save_webp(desk, header_dir / f"{key}.webp", width=1920, quality=80)
        save_webp(mob, header_dir / f"{key}-mobile.webp", width=1080, quality=80)

    for p in PRODUCTS:
        keep = p["slug"] == "phosphate-rock"  # transparent background
        save_webp(p["source"], prod_dir / f"{p['slug']}.webp", width=800, quality=82, keep_alpha=keep)

    # Footer logo: supplied reversed (white) wordmark for dark backgrounds, cropped to its visible bounds. Not recoloured or redrawn.
    global EMBLEM_SIZE
    emblem = Image.open(SRC / "logo-white.png").convert("RGBA")
    alpha_box = emblem.getchannel("A").getbbox()
    if alpha_box:
        pad = 4
        l, t, r, b = alpha_box
        emblem = emblem.crop((max(0, l - pad), max(0, t - pad), min(emblem.width, r + pad), min(emblem.height, b + pad)))
    emblem.save(img_dir / "forcelink-footer-logo.png", "PNG", optimize=True)
    display_w = 250
    EMBLEM_SIZE = (display_w, round(emblem.height * display_w / emblem.width))
    # Header wordmark: navy logo for light backgrounds, cropped to its visible bounds.
    _hl = Image.open(SRC / "logo-navy.png").convert("RGBA")
    _hb = _hl.getchannel("A").getbbox()
    _hl = _hl.crop((max(0, _hb[0] - 4), max(0, _hb[1] - 4), min(_hl.width, _hb[2] + 4), min(_hl.height, _hb[3] + 4)))
    _hl = _hl.resize((900, round(_hl.height * 900 / _hl.width)), Image.LANCZOS)
    _hl.save(img_dir / "forcelink-logo.png", "PNG", optimize=True)

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
    write("careers/index.html", career_page())

    # GitHub Pages: serve files starting with underscores; no Jekyll processing.
    write(".nojekyll", "")

    robots = "User-agent: *\nAllow: /\n"
    if SITE_URL:
        robots += f"\nSitemap: {SITE_URL}sitemap.xml\n"
    write("robots.txt", robots)

    if SITE_URL:
        paths = [""] + ["about/", "products/", "markets/", "careers/", "contact/"] + [
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
