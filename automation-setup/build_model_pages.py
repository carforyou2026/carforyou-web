import json
import re
import sys

# --- Load data (paths adjusted for this environment) -----------------------

with open("data.js", encoding="utf-8") as f:
    data_text = f.read()
DATA = json.loads(data_text[data_text.index("["):data_text.rindex("]") + 1])

import subprocess

with open("articles.js", encoding="utf-8") as f:
    art_text = f.read()
art_json_str = subprocess.run(
    ["node", "-e", art_text + "\nconsole.log(JSON.stringify(ARTICLES));"],
    capture_output=True, text=True, check=True
).stdout
ARTICLES = json.loads(art_json_str)

# model-specs.js is generated separately (see model-specs.js itself for how
with open("model-specs.js", encoding="utf-8") as f:
    specs_text = f.read()
specs_json_str = subprocess.run(
    ["node", "-e", specs_text + "\nconsole.log(JSON.stringify(MODEL_SPECS));"],
    capture_output=True, text=True, check=True
).stdout
MODEL_SPECS_AGG = json.loads(specs_json_str)  # keyed "Maerke|Model" -> aggregate dict

MODEL_TYPE_LABELS = {"hatchback": "Hatchback", "suv": "SUV", "mpv": "MPV"}


def slugify(s):
    s = s.lower()
    for a, b in [("æ", "ae"), ("ø", "oe"), ("å", "aa"), ("é", "e")]:
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def fmt_kr(n):
    return f"{n:,.0f}".replace(",", ".") + " kr."


LOGO_SVG = '<svg viewBox="0 0 2340 762" xmlns="http://www.w3.org/2000/svg"><text fill="#084F8C" font-family="\'Readex Pro\',sans-serif" font-weight="600" font-size="362" transform="matrix(1 0 0 1 297.57 457)">car</text><text fill="#1081C7" font-family="\'Readex Pro\',sans-serif" font-weight="600" font-size="362" transform="matrix(1 0 0 1 841.84 457)">for</text><text fill="#00B0F0" font-family="\'Readex Pro\',sans-serif" font-weight="600" font-size="362" transform="matrix(1 0 0 1 1355.17 457)">you</text><path d="M0 312.244C0 269.583 34.58 235 77.24 235L182.76 235C225.42 235 260 269.583 260 312.244L260 417.757C260 460.417 225.42 495.001 182.76 495.001L77.24 495.001C34.58 495.001 0 460.417 0 417.757Z" fill="#1081C7" fill-rule="evenodd"/><text fill="#FFFFFF" font-family="\'Readex Pro\',sans-serif" font-weight="600" font-size="83" transform="matrix(1 0 0 1 93.91 444)">cfy</text></svg>'

CAR_ICONS = {
    "hatchback": '<symbol id="car-hatchback" viewBox="0 0 120 60"><rect x="8" y="32" width="104" height="16" rx="8" fill="#1081C7"/><path d="M30 32 L45 14 L80 14 L100 32 Z" fill="#084F8C"/><path d="M33 30 L46 18 L79 18 L96 30 Z" fill="#E3F6FC"/><circle cx="35" cy="48" r="11" fill="#084F8C"/><circle cx="35" cy="48" r="4" fill="#00B0F0"/><circle cx="90" cy="48" r="11" fill="#084F8C"/><circle cx="90" cy="48" r="4" fill="#00B0F0"/></symbol>',
    "suv": '<symbol id="car-suv" viewBox="0 0 120 60"><rect x="6" y="28" width="108" height="20" rx="8" fill="#1081C7"/><path d="M28 28 L42 8 L82 8 L98 28 Z" fill="#084F8C"/><path d="M31 26 L43 12 L81 12 L94 26 Z" fill="#E3F6FC"/><circle cx="32" cy="50" r="13" fill="#084F8C"/><circle cx="32" cy="50" r="4.5" fill="#00B0F0"/><circle cx="92" cy="50" r="13" fill="#084F8C"/><circle cx="92" cy="50" r="4.5" fill="#00B0F0"/></symbol>',
    "mpv": '<symbol id="car-mpv" viewBox="0 0 120 60"><rect x="10" y="26" width="100" height="18" rx="6" fill="#1081C7"/><path d="M18 26 L20 6 L95 6 L100 26 Z" fill="#084F8C"/><path d="M22 24 L23 10 L94 10 L97 24 Z" fill="#E3F6FC"/><circle cx="34" cy="48" r="11" fill="#084F8C"/><circle cx="34" cy="48" r="4" fill="#00B0F0"/><circle cx="88" cy="48" r="11" fill="#084F8C"/><circle cx="88" cy="48" r="4" fill="#00B0F0"/></symbol>',
}

HEADER = f"""<header>
  <div class="inner">
    <a href="index.html" class="logo">{LOGO_SVG}</a>
    <nav>
      <a href="index.html#compare">Priser</a>
      <a href="modeller.html">Modeller</a>
      <a href="sammenlign.html">Sammenlign</a>
      <a href="artikler.html">Artikler</a>
    </nav>
  </div>
</header>"""

FOOTER = """<footer>
  <div class="wrap">CarForYou. Tidlig testversion, ikke tilknyttet de viste bilmærker.</div>
</footer>"""

BASE_CSS = """
  :root{
    --ink:#084F8C; --ink-soft:#3E6A8A; --paper:#F3F6F8; --paper-raised:#FFFFFF;
    --fjord:#1081C7; --fjord-deep:#084F8C; --mint:#E3F6FC; --amber:#00B0F0; --amber-deep:#0C93CE;
    --grey:#5B6472; --line:#DCE3E8;
    --display:'Readex Pro', sans-serif; --body:'Inter', sans-serif; --mono:'JetBrains Mono', monospace;
  }
  *{box-sizing:border-box;}
  body{margin:0; background:var(--paper); color:var(--ink); font-family:var(--body); line-height:1.6;}
  a{color:var(--fjord);}
  .wrap{max-width:900px; margin:0 auto; padding:0 28px;}
  header{padding:22px 0; border-bottom:1px solid var(--line); background:var(--paper-raised);}
  header .inner{max-width:1080px; margin:0 auto; padding:0 28px; display:flex; align-items:center; justify-content:space-between;}
  .logo svg{height:26px; width:auto; display:block;}
  nav a{font-size:14px; color:var(--ink-soft); text-decoration:none; margin-left:24px;}
  nav a:hover{color:var(--fjord);}
  main{padding:44px 0 70px;}
  .breadcrumb{font-size:13px; color:var(--grey); margin-bottom:16px;}
  .breadcrumb a{color:var(--grey); text-decoration:none;}
  .breadcrumb a:hover{color:var(--fjord);}
  .model-head{display:flex; align-items:center; gap:20px; margin-bottom:6px;}
  .model-icon{width:120px; height:64px; background:var(--mint); border-radius:12px; display:flex; align-items:center; justify-content:center; flex-shrink:0;}
  .model-icon svg{width:88px; height:auto;}
  .model-hero-fig{
    background:var(--paper-raised); border:1px solid var(--line); border-radius:10px;
    padding:20px 22px 14px; margin:18px 0 30px;
  }
  .model-hero-fig svg{width:100%; height:auto; display:block;}
  .model-hero-fig figcaption{font-size:11px; color:var(--grey); margin-top:8px; text-align:right;}
  .brand-tag{font-family:var(--mono); font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; color:var(--fjord-deep);}
  h1{font-family:var(--display); font-size:30px; line-height:1.15; letter-spacing:-0.01em; margin:2px 0 0;}
  .from-price{font-size:15px; color:var(--ink-soft); margin:14px 0 30px;}
  .from-price b{font-family:var(--mono); color:var(--ink); font-size:19px;}
  h2{font-family:var(--display); font-size:20px; margin:38px 0 14px; letter-spacing:-0.005em;}
  .spec-grid{display:grid; grid-template-columns:repeat(auto-fit, minmax(150px,1fr)); gap:12px;}
  .spec-box{background:var(--paper-raised); border:1px solid var(--line); border-radius:10px; padding:14px 16px;}
  .spec-box .val{font-family:var(--mono); font-weight:700; font-size:19px; color:var(--ink);}
  .spec-box .lbl{font-size:12px; color:var(--grey); margin-top:2px;}
  .spec-note{font-size:13.5px; color:var(--grey); background:var(--paper-raised); border:1px solid var(--line); border-radius:8px; padding:12px 14px;}
  table{width:100%; border-collapse:collapse; background:var(--paper-raised); border:1px solid var(--line); border-radius:10px; overflow:hidden;}
  th{text-align:left; font-size:11.5px; text-transform:uppercase; letter-spacing:0.04em; color:var(--grey); font-weight:600; padding:12px 14px; border-bottom:1px solid var(--line);}
  td{padding:13px 14px; font-size:14px; border-bottom:1px solid var(--line);}
  tr:last-child td{border-bottom:none;}
  td.price{font-family:var(--mono); font-weight:700; color:var(--ink);}
  .see-offer{font-size:13px; font-weight:600; color:var(--fjord); text-decoration:none; white-space:nowrap;}
  .see-offer:hover{text-decoration:underline;}
  .article-list{display:flex; flex-direction:column;}
  .article-card{display:block; text-decoration:none; color:inherit; padding:18px 0; border-bottom:1px solid var(--line);}
  .article-card:first-child{padding-top:0;}
  .article-tag{font-family:var(--mono); font-size:10.5px; text-transform:uppercase; letter-spacing:0.05em; color:var(--fjord-deep); background:var(--mint); padding:3px 8px; border-radius:4px;}
  .article-card h3{font-family:var(--display); font-size:16px; font-weight:600; margin:8px 0 4px;}
  .article-card:hover h3{color:var(--fjord);}
  .article-card p{font-size:13.5px; color:var(--ink-soft); margin:0;}
  .cta-box{background:var(--ink); color:#fff; border-radius:10px; padding:24px; margin:38px 0 8px; display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap;}
  .cta-box p{margin:0; font-size:14.5px; color:#C3CCDA; max-width:40ch;}
  .cta-box a{background:var(--amber); color:var(--ink); font-weight:600; font-size:14px; text-decoration:none; padding:11px 18px; border-radius:6px; white-space:nowrap;}
  footer{padding:30px 0 50px; text-align:center; color:var(--grey); font-size:13px; border-top:1px solid var(--line); margin-top:20px;}
  .table-scroll{overflow-x:auto;}
  @media (max-width:480px){
    .wrap{padding:0 18px;}
    header .inner{padding-left:18px; padding-right:18px;}
    h1{font-size:23px;}
    .model-head{gap:14px;}
    .model-icon{width:64px; height:34px;}
    .model-icon svg{width:46px;}
    .cta-box{flex-direction:column; align-items:stretch; text-align:center;}
    .cta-box a{text-align:center;}
    table{font-size:12.5px;}
  }
"""


def related_articles(model_key_tags, limit=2):
    scored = []
    for a in ARTICLES:
        overlap = len(set(a["tags"]) & set(model_key_tags))
        if overlap > 0:
            scored.append((overlap, a))
    scored.sort(key=lambda x: (-x[0], x[1]["date"]), reverse=False)
    scored.sort(key=lambda x: -x[0])
    return [a for _, a in scored[:limit]]


def find_comparison_suggestion(maerke, model, type_, cheapest_price, all_grouped):
    candidates = []
    for (m2_maerke, m2_model), records in all_grouped.items():
        if (m2_maerke, m2_model) == (maerke, model):
            continue
        if records[0].get("type", "hatchback") != type_:
            continue
        c_price = min(r["ydelse_kr"] for r in records)
        candidates.append((abs(c_price - cheapest_price), m2_maerke != maerke, m2_maerke, m2_model))
    if not candidates:
        return None
    candidates.sort(key=lambda c: (c[0], not c[1]))
    return candidates[0][2], candidates[0][3]


def build_price_range_svg(variants):
    prices = sorted(set(r["ydelse_kr"] for r in variants))
    min_p, max_p = prices[0], prices[-1]

    if min_p == max_p:
        return (
            '<svg viewBox="0 0 640 90" xmlns="http://www.w3.org/2000/svg" role="img" '
            f'aria-label="Denne model findes i én prisleje: {fmt_kr(min_p)} om måneden.">'
            f'<text x="0" y="30" font-family="Inter,sans-serif" font-size="13" fill="#5B6472">Fast månedspris for denne model</text>'
            f'<text x="0" y="66" font-family="\'JetBrains Mono\',monospace" font-weight="700" font-size="30" fill="#084F8C">{fmt_kr(min_p)}/md.</text>'
            '</svg>'
        )

    track_x0, track_x1 = 10, 630
    span = max_p - min_p

    def px(price):
        return track_x0 + (price - min_p) / span * (track_x1 - track_x0)

    dots = "".join(
        f'<circle cx="{px(p):.1f}" cy="46" r="5" fill="#1081C7" opacity="0.85"/>' for p in prices
    )

    return (
        '<svg viewBox="0 0 640 90" xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-label="Prisspredning for denne model: fra {fmt_kr(min_p)} til {fmt_kr(max_p)} om måneden på tværs af {len(prices)} prisniveauer.">'
        f'<text x="0" y="18" font-family="Inter,sans-serif" font-size="12" fill="#5B6472">Prisspredning på tværs af {len(prices)} varianter/udbetalingstrin</text>'
        f'<line x1="{track_x0}" y1="46" x2="{track_x1}" y2="46" stroke="#DCE3E8" stroke-width="4" stroke-linecap="round"/>'
        f'{dots}'
        f'<text x="{track_x0}" y="80" font-family="\'JetBrains Mono\',monospace" font-weight="700" font-size="16" fill="#084F8C">{fmt_kr(min_p)}</text>'
        f'<text x="{track_x1}" y="80" font-family="\'JetBrains Mono\',monospace" font-weight="700" font-size="16" fill="#084F8C" text-anchor="end">{fmt_kr(max_p)}</text>'
        '</svg>'
    )


def build_model_page(maerke, model, records, all_grouped=None):
    type_ = records[0].get("type", "hatchback")
    slug = f"model-{slugify(maerke)}-{slugify(model)}.html"
    cheapest = min(records, key=lambda r: r["ydelse_kr"])
    # Sort by variant name, then udbetaling, then km/aar -- so with the
    # expanded km/year tiers, all rows for the same trim/down-payment group
    # together in ascending mileage order, instead of scattering by price
    # alone across dozens of rows.
    variants = sorted(records, key=lambda r: (r["variant"], r["udbetaling_kr"], r["km_aar"]))

    tags = [slugify(maerke), type_, "alle-maerker"]
    related = related_articles(tags)
    price_range_svg = build_price_range_svg(records)

    # PATCH: use the pre-aggregated MODEL_SPECS_AGG (keyed "Maerke|Model")
    # instead of re-deriving per-variant specs from a raw PDF text dump.
    spec_html = ""
    agg = MODEL_SPECS_AGG.get(f"{maerke}|{model}")
    if agg:
        boxes = []
        if agg["type"] == "electric":
            boxes.append(f'<div class="spec-box"><div class="val">{agg["raekkevidde_km_min"]:.0f}\u2013{agg["raekkevidde_km_max"]:.0f} km</div><div class="lbl">Rækkevidde (WLTP, varierer pr. variant)</div></div>')
            boxes.append(f'<div class="spec-box"><div class="val">{agg["forbrug"]}</div><div class="lbl">Forbrug (laveste variant)</div></div>')
        else:
            boxes.append(f'<div class="spec-box"><div class="val">{agg["co2_g_km"]:.0f} g/km</div><div class="lbl">CO\u2082-udledning</div></div>')
            boxes.append(f'<div class="spec-box"><div class="val">{agg["forbrug"]}</div><div class="lbl">Forbrug</div></div>')
            boxes.append(f'<div class="spec-box"><div class="val">{fmt_kr(agg["ejerafgift_halvaar_kr"])}</div><div class="lbl">Halvårlig ejerafgift</div></div>')
        spec_html = f'<h2>Specifikationer</h2><div class="spec-grid">{"".join(boxes)}</div><p class="spec-note">Specifikationer hentet direkte fra {maerke}s prisliste. Kan variere pr. variant. Se den fulde oversigt nedenfor.</p>'
    else:
        spec_html = f'<h2>Specifikationer</h2><p class="spec-note">Vi har endnu ikke hentet detaljerede specifikationer (rækkevidde, forbrug) for {maerke} automatisk, kun priser. Klik "Se tilbud" i prisoversigten for de fulde specifikationer hos {maerke}.</p>'

    rows = "".join(
        f'<tr><td>{r["variant"]}</td><td class="price">{fmt_kr(r["ydelse_kr"])}/md.</td>'
        f'<td>{fmt_kr(r["udbetaling_kr"])}</td><td>{r["loebetid_mdr"]} mdr.</td>'
        f'<td>{r["km_aar"]:,}'.replace(",", ".") + f' km/år</td>'
        f'<td><a class="see-offer" href="{r["kilde_url"]}" target="_blank" rel="noopener">Se tilbud \u2192</a></td></tr>'
        for r in variants
    )

    articles_html = ""
    if related:
        cards = "".join(
            f'<a class="article-card" href="{a["filename"]}"><span class="article-tag">{a["tag"]}</span>'
            f'<h3>{a["title"]}</h3><p>{a["summary"]}</p></a>'
            for a in related
        )
        articles_html = f'<h2>Relevante artikler</h2><div class="article-list">{cards}</div>'

    compare_html = ""
    if all_grouped:
        suggestion = find_comparison_suggestion(maerke, model, type_, cheapest["ydelse_kr"], all_grouped)
        if suggestion:
            s_maerke, s_model = suggestion
            s_slug = f"{slugify(maerke)}-{slugify(model)}"
            t_slug = f"{slugify(s_maerke)}-{slugify(s_model)}"
            compare_html = (
                f'<h2>Hvordan klarer den sig mod konkurrenterne?</h2>'
                f'<a class="cta-box" style="text-decoration:none; display:flex;" '
                f'href="sammenlign.html?a={s_slug}&amp;b={t_slug}">'
                f'<p style="color:#fff;">Sammenlign {maerke} {model} direkte med {s_maerke} {s_model}, '
                f'samme biltype og tæt på i pris.</p>'
                f'<span style="background:var(--amber); color:var(--ink); font-weight:600; font-size:14px; padding:11px 18px; border-radius:6px; white-space:nowrap;">Sammenlign \u2192</span>'
                f'</a>'
            )

    type_label = MODEL_TYPE_LABELS.get(type_, type_)
    title = f"{maerke} {model} privatleasing: priser og specifikationer | CarForYou"
    description = f"Se aktuelle privatleasing-priser for {maerke} {model}: {len(variants)} variant(er) fra {fmt_kr(cheapest['ydelse_kr'])}/md. Specifikationer og direkte link til {maerke}."

    offers_schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": f"{maerke} {model}",
        "brand": maerke,
        "offers": [
            {
                "@type": "Offer",
                "name": r["variant"],
                "price": r["ydelse_kr"],
                "priceCurrency": "DKK",
                "url": r["kilde_url"],
                "availability": "https://schema.org/InStock",
            }
            for r in variants
        ],
    }

    icon_symbol = CAR_ICONS.get(type_, CAR_ICONS["hatchback"])

    html = f"""<!DOCTYPE html>
<html lang="da">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{description}">
<style>
  @font-face {{
    font-family: 'Readex Pro';
    src: url('fonts/ReadexPro-Variable.ttf') format('truetype-variations'), url('fonts/ReadexPro-Variable.ttf') format('truetype');
    font-weight: 400 700;
    font-style: normal;
    font-display: swap;
  }}
  @font-face {{
    font-family: 'Inter';
    src: url('fonts/Inter-Variable.ttf') format('truetype-variations'), url('fonts/Inter-Variable.ttf') format('truetype');
    font-weight: 400 700;
    font-style: normal;
    font-display: swap;
  }}
  @font-face {{
    font-family: 'JetBrains Mono';
    src: url('fonts/JetBrainsMono-Variable.ttf') format('truetype-variations'), url('fonts/JetBrainsMono-Variable.ttf') format('truetype');
    font-weight: 400 700;
    font-style: normal;
    font-display: swap;
  }}
</style>
<script type="application/ld+json">{json.dumps(offers_schema, ensure_ascii=False)}</script>
<style>{BASE_CSS}</style>
</head>
<body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>{icon_symbol}</defs></svg>
{HEADER}
<main>
  <div class="wrap">
    <p class="breadcrumb"><a href="index.html">CarForYou</a> / <a href="modeller.html">Modeller</a> / {maerke} {model}</p>
    <div class="model-head">
      <div class="model-icon"><svg><use href="#car-{type_}"/></svg></div>
      <div>
        <div class="brand-tag">{maerke} \u00b7 {type_label}</div>
        <h1>{maerke} {model}</h1>
      </div>
    </div>
    <p class="from-price">Privatleasing fra <b>{fmt_kr(cheapest["ydelse_kr"])}/md.</b> \u00b7 {len(variants)} variant(er) tilgængelig(e)</p>

    <figure class="model-hero-fig">
      {price_range_svg}
      <figcaption>Illustration: CarForYou, baseret på aktuelle priser for {maerke} {model}.</figcaption>
    </figure>

    {spec_html}

    <h2>Alle leasingtilbud for {maerke} {model}</h2>
    <div class="table-scroll">
    <table>
      <thead><tr><th>Variant</th><th>Ydelse</th><th>Udbetaling</th><th>Løbetid</th><th>Km/år</th><th></th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    </div>

    {articles_html}

    {compare_html}

    <div class="cta-box">
      <p>Sammenlign {maerke} {model} med andre modeller og mærker.</p>
      <a href="index.html#compare">Se fuld sammenligning \u2192</a>
    </div>
  </div>
</main>
{FOOTER}
</body>
</html>
"""
    return slug, html


def build_index_page(index_entries):
    cards = ""
    for e in sorted(index_entries, key=lambda x: (x["maerke"], x["model"])):
        icon = CAR_ICONS.get(e["type"], CAR_ICONS["hatchback"])
        cards += (
            f'<a class="model-card" href="{e["slug"]}">'
            f'<div class="model-card-icon"><svg viewBox="0 0 120 60"><defs>{icon}</defs><use href="#car-{e["type"]}"/></svg></div>'
            f'<div class="brand-tag">{e["maerke"]}</div>'
            f'<h3>{e["model"]}</h3>'
            f'<p>Fra {fmt_kr(e["fra_pris"])}/md. \u00b7 {e["antal_varianter"]} variant(er)</p>'
            f'</a>'
        )
    html = f"""<!DOCTYPE html>
<html lang="da">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Alle bilmodeller til privatleasing | CarForYou</title>
<meta name="description" content="Se alle {len(index_entries)} bilmodeller til privatleasing på CarForYou. Priser og specifikationer for hver model, opdateret direkte fra mærkerne.">
<style>
  @font-face {{
    font-family: 'Readex Pro';
    src: url('fonts/ReadexPro-Variable.ttf') format('truetype-variations'), url('fonts/ReadexPro-Variable.ttf') format('truetype');
    font-weight: 400 700;
    font-style: normal;
    font-display: swap;
  }}
  @font-face {{
    font-family: 'Inter';
    src: url('fonts/Inter-Variable.ttf') format('truetype-variations'), url('fonts/Inter-Variable.ttf') format('truetype');
    font-weight: 400 700;
    font-style: normal;
    font-display: swap;
  }}
  @font-face {{
    font-family: 'JetBrains Mono';
    src: url('fonts/JetBrainsMono-Variable.ttf') format('truetype-variations'), url('fonts/JetBrainsMono-Variable.ttf') format('truetype');
    font-weight: 400 700;
    font-style: normal;
    font-display: swap;
  }}
</style>
<style>{BASE_CSS}
  .model-grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(min(220px,100%),1fr)); gap:14px;}}
  .model-card{{display:block; text-decoration:none; color:inherit; background:var(--paper-raised); border:1px solid var(--line); border-radius:10px; padding:16px; transition:border-color 0.15s ease, transform 0.15s ease;}}
  .model-card:hover{{border-color:var(--fjord); transform:translateY(-2px);}}
  .model-card-icon{{width:56px; height:28px; margin-bottom:10px;}}
  .model-card-icon svg{{width:100%; height:100%;}}
  .model-card h3{{font-family:var(--display); font-size:16px; margin:2px 0 4px;}}
  .model-card p{{font-size:12.5px; color:var(--grey); margin:0;}}
  .wrap{{max-width:1080px;}}
</style>
</head>
<body>
{HEADER}
<main>
  <div class="wrap">
    <p class="breadcrumb"><a href="index.html">CarForYou</a> / Modeller</p>
    <h1>Alle bilmodeller til privatleasing</h1>
    <p class="from-price">{len(index_entries)} modeller p\u00e5 tv\u00e6rs af m\u00e6rker. Tjek priser og specifikationer for hver.</p>
    <div class="model-grid">{cards}</div>
  </div>
</main>
{FOOTER}
</body>
</html>
"""
    with open("modeller.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Built modeller.html")


def main():
    grouped = {}
    for r in DATA:
        key = (r["maerke"], r["model"])
        grouped.setdefault(key, []).append(r)

    index_entries = []
    for (maerke, model), records in sorted(grouped.items()):
        slug, html = build_model_page(maerke, model, records, all_grouped=grouped)
        with open(slug, "w", encoding="utf-8") as f:
            f.write(html)
        cheapest = min(r["ydelse_kr"] for r in records)
        index_entries.append({
            "maerke": maerke, "model": model, "slug": slug,
            "type": records[0].get("type", "hatchback"),
            "fra_pris": cheapest, "antal_varianter": len(records),
        })
        print(f"Built {slug} ({len(records)} variants, from {fmt_kr(cheapest)}/md.)")

    with open("model-index.json", "w", encoding="utf-8") as f:
        json.dump(index_entries, f, ensure_ascii=False, indent=2)

    with open("model-index.js", "w", encoding="utf-8") as f:
        f.write("// Auto-generated by build_model_pages.py -- do not hand-edit.\n")
        f.write("const MODEL_INDEX = ")
        f.write(json.dumps(index_entries, ensure_ascii=False, indent=2))
        f.write(";\n")

    print(f"\n{len(index_entries)} model pages built.")
    build_index_page(index_entries)


if __name__ == "__main__":
    main()
