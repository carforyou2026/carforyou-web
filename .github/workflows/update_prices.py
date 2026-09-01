#!/usr/bin/env python3
"""
update_prices.py

Automated data-refresh script for CarForYou.

WHAT THIS DOES
--------------
1. Fetches live Volkswagen and Skoda leasing price pages -- both run through
   the same Skandinavisk Motor Co. A/S master price lists, extracting every
   km/year tier per variant (not just 10.000).
2. Fetches live Toyota campaign prices and Kia model-page prices.
3. Loads BMW, Hyundai, and the still-manually-maintained remainder of
   Toyota/Kia/Renault from manual_offers.json (update that file by hand, or
   build proper scraper functions for BMW/Hyundai the same way as VW/Skoda
   once you've confirmed their pages are similarly scrapeable on a schedule).
4. Merges everything and writes it to data.js in the exact format the website
   already expects.
5. SAFETY CHECK: if any automated brand returns suspiciously few offers (site
   likely changed structure, or the request got blocked), the script does NOT
   overwrite data.js. It exits with an error instead, so the site keeps
   showing the last known-good prices rather than silently going blank or
   wrong.

HOW TO RUN THIS
---------------
This needs to run somewhere with real internet access (your own laptop, or a
scheduled job -- see the note on GitHub Actions at the bottom of this file).
It will NOT run inside a sandboxed environment with no network access.

    pip install requests
    python3 update_prices.py

REQUIRED FOLLOW-UP
-------------------
- Check ToS / robots.txt for each brand's domain before running this against
  the live site regularly -- see the earlier discussion on this.
- Add scraper functions for Toyota, Kia, and Renault the same way as VW once
  you've confirmed those sites are similarly scrapeable (Renault, being a
  PDF, will need a PDF-text library like pdfplumber instead of this regex
  approach).
"""

import re
import sys
import json
import datetime

from diff_offers import diff_and_annotate

try:
    import requests
except ImportError:
    print("This script needs the 'requests' library: pip install requests", file=sys.stderr)
    sys.exit(1)

TODAY = datetime.date.today().isoformat()

# Minimum offers we expect back from VW combined. If we get fewer than this,
# something is wrong (blocked, redesigned page, network issue) and we should
# NOT trust the result enough to overwrite the live site's data.
# Minimum offers we expect back from VW combined. If we get fewer than this,
# something is wrong (blocked, redesigned page, network issue) and we should
# NOT trust the result enough to overwrite the live site's data.
# The all-tiers extraction typically yields 200+ VW offers (was ~30-46 when
# only the 10.000 km/år tier was kept) -- raised accordingly so a genuine
# site-structure change still gets caught, without false-alarming on normal
# fluctuation.
MIN_EXPECTED_VW_OFFERS = 150

# A single PDF covering VW's entire Danish leasing lineup (T-Roc, both ID.
# Buzz sizes, ID. Polo, ID.3 Neo, ID.4, ID.5, ID.7 Tourer) -- discovered
# 2026-08-08. Replaces the old approach of guessing individual model URLs.
VW_MASTER_PRICELIST_URL = "https://prislister.volkswagen.dk/leasingpriser"

# Pre-filtered to leasing-type campaigns only (avoids financing/cash-purchase
# and non-priced campaign noise mixed into the general /kampagner page).
TOYOTA_CAMPAIGNS_URL = (
    "https://www.toyota.dk/kampagner?types=Privatleasing+12+måneder,"
    "Privatleasing+36+måneder,Privatleasing"
)

MIN_EXPECTED_TOYOTA_OFFERS = 2

RENAULT_PRIVATLEASING_URL = "https://www.renault.dk/kob/privatleasing"
MIN_EXPECTED_RENAULT_OFFERS = 2

# Kia model landing pages (kiaonline.dk/biler/{slug}/) are ordinary
# server-rendered WordPress pages with the full price table inline -- no
# headless browser needed, unlike /konfigurator/ which is JS-only and blank
# on a plain fetch. EV2, EV4 Fastback, EV5, and both PV5 vans currently live
# on kia.com instead (different template, not yet verified/supported here).
KIA_MODELS = {
    "EV3": "https://kiaonline.dk/biler/ev3/",
    "EV4": "https://kiaonline.dk/biler/ev4/",
    "EV6": "https://kiaonline.dk/biler/ev6/",
    "EV9": "https://kiaonline.dk/biler/ev9/",
    "PV5 Passenger": "https://kiaonline.dk/biler/pv5-passenger/",
}
MIN_EXPECTED_KIA_OFFERS = 4

# Skoda's leasing is run through the same Skandinavisk Motor Co. A/S as VW,
# with an equivalent single master price-list PDF covering the whole lineup.
SKODA_MASTER_PRICELIST_URL = "https://prislister.skoda.dk/leasingpriser"
MIN_EXPECTED_SKODA_OFFERS = 100

HEADERS = {
    # A normal browser user-agent. Some sites block obviously bot-like requests.
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

# Generic body-type classification (hatchback/suv/mpv), used only to pick
# which original icon the site shows -- not tied to any manufacturer's
# specific design. Unknown models default to "hatchback".
MODEL_TYPES = {
    "T-Roc": "suv", "ID. Buzz Kort": "mpv", "ID. Buzz Lang": "mpv",
    "ID. Polo": "hatchback", "ID.3 Neo": "hatchback", "ID.4": "suv",
    "ID.5": "suv", "ID.7 Tourer": "suv",
    "C-HR+": "suv", "bZ4X": "suv", "bZ4X Touring": "suv", "Yaris": "hatchback",
    "EV3": "suv", "EV5": "suv", "EV6": "suv", "EV9": "suv",
    "PV5 Passenger": "mpv", "EV4": "hatchback", "4": "suv", "5": "hatchback",
    "Scenic": "suv", "Twingo": "hatchback",
    "Kamiq": "suv", "Scala": "hatchback", "Epiq": "hatchback", "Elroq": "suv",
    "Enyaq": "suv", "Enyaq Coupé": "suv", "Peaq": "suv",
}

SKODA_MODEL_URLS = {
    "Kamiq": "https://www.skoda.dk/modeller/kamiq/kamiq",
    "Scala": "https://www.skoda.dk/modeller/scala/scala",
    "Epiq": "https://www.skoda.dk/modeller/epiq/epiq",
    "Elroq": "https://www.skoda.dk/modeller/elroq/elroq",
    "Enyaq": "https://www.skoda.dk/modeller/enyaq/ny-enyaq",
    "Enyaq Coupé": "https://www.skoda.dk/modeller/enyaq/ny-enyaq-coupe",
    "Peaq": "https://www.skoda.dk/modeller/peaq/peaq",
}


def parse_vw_master_pricelist(text):
    """See parse_vw_all_tiers.py for the fully-commented, tested version of
    this function against real sample data. Kept in sync with it here.

    Extracts EVERY km/year tier per variant/down-payment combo (previously
    only 10.000 was kept -- expanded once the site's km/aar range filter
    existed to make real use of a fuller mileage spread).
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    records = []
    current_model = None
    current_variant = None
    row_pattern = re.compile(
        r"^([\d.]+) km/år (\d+) mdr\.\s+[\d.]+\s*kr\.\s+[\d.]+\s*kr\.\s+"
        r"([\d.]+)\s*kr\.\s+([\d.]+)\s*kr\.$"
    )
    for i, line in enumerate(lines):
        if line.endswith("leasingpriser"):
            current_model = line[: -len(" leasingpriser")].strip()
            current_variant = None
            continue
        if line.startswith("CO2:") or "kWh/100km" in line:
            current_variant = lines[i - 1] if i > 0 else None
            continue
        m = row_pattern.match(line)
        if m and current_model and current_variant:
            records.append({
                "maerke": "Volkswagen",
                "model": current_model,
                "variant": current_variant,
                "udbetaling_kr": int(m.group(3).replace(".", "")),
                "ydelse_kr": int(m.group(4).replace(".", "")),
                "loebetid_mdr": int(m.group(2)),
                "km_aar": int(m.group(1).replace(".", "")),
                "kilde_url": VW_MASTER_PRICELIST_URL,
                "sidst_tjekket": TODAY,
                "status": "Aktiv",
                "type": MODEL_TYPES.get(current_model, "hatchback"),
            })
    seen = {}
    for r in records:
        seen[(r["model"], r["variant"], r["udbetaling_kr"], r["km_aar"])] = r
    return list(seen.values())


def _debug_response(name, resp):
    """Prints diagnostic info about a fetched response so a failed run's
    log actually shows *why* parsing found nothing -- e.g. a bot-check page,
    a redirect to a cookie-consent wall, or a genuinely changed page
    structure all look different here, instead of just "0 offers" with no
    further clue.
    """
    snippet = resp.text[:300].replace("\n", " ")
    print(f"  [{name}] status={resp.status_code} final_url={resp.url} "
          f"content_length={len(resp.text)}", file=sys.stderr)
    print(f"  [{name}] first 300 chars: {snippet!r}", file=sys.stderr)


def fetch_vw_offers():
    try:
        resp = requests.get(VW_MASTER_PRICELIST_URL, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"WARNING: failed to fetch VW master price list: {e}", file=sys.stderr)
        return []
    offers = parse_vw_master_pricelist(resp.text)
    if not offers:
        _debug_response("VW", resp)
    print(f"  VW: parsed {len(offers)} offers across "
          f"{len(set(o['model'] for o in offers))} models", file=sys.stderr)
    return offers


def parse_skoda_master_pricelist(text):
    """See parse_skoda_master.py / the km/aar expansion work for the fully
    tested version of this against real sample data. Extracts EVERY km/year
    tier per variant/down-payment combo, same convention as VW above.

    Note: the source text sometimes has an encoding quirk around "Rækkevidde"
    -- detecting electric vs. petrol variants by "kWh/100km" in the spec line
    is more robust than matching the word itself.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    records = []
    current_model = None
    row_pattern = re.compile(
        r"^([\d.]+) km/år (\d+) mdr\.\s+[\d.]+\s*kr\.\s+[\d.]+\s*kr\.\s+"
        r"([\d.]+|0)\s*kr\.\s+([\d.]+)\s*kr\.$"
    )
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.endswith("leasingpriser"):
            current_model = line[: -len(" leasingpriser")].strip()
            i += 1
            continue
        if current_model and i + 2 < len(lines) and "Kørselsbehov" in lines[i + 2]:
            variant = line
            j = i + 3
            while j < len(lines) and re.match(r"^[\d.]+ km/år", lines[j]):
                m = row_pattern.match(lines[j])
                if m:
                    records.append({
                        "maerke": "Skoda",
                        "model": current_model,
                        "variant": variant,
                        "udbetaling_kr": int(m.group(3).replace(".", "")),
                        "ydelse_kr": int(m.group(4).replace(".", "")),
                        "loebetid_mdr": int(m.group(2)),
                        "km_aar": int(m.group(1).replace(".", "")),
                        "kilde_url": SKODA_MODEL_URLS.get(current_model, "https://www.skoda.dk/"),
                        "sidst_tjekket": TODAY,
                        "status": "Aktiv",
                        "type": MODEL_TYPES.get(current_model, "hatchback"),
                    })
                j += 1
            i = j
            continue
        i += 1
    seen = {}
    for r in records:
        seen[(r["model"], r["variant"], r["udbetaling_kr"], r["km_aar"])] = r
    return list(seen.values())


def fetch_skoda_offers():
    try:
        resp = requests.get(SKODA_MASTER_PRICELIST_URL, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"WARNING: failed to fetch Skoda master price list: {e}", file=sys.stderr)
        return []
    offers = parse_skoda_master_pricelist(resp.text)
    if not offers:
        _debug_response("Skoda", resp)
    print(f"  Skoda: parsed {len(offers)} offers across "
          f"{len(set(o['model'] for o in offers))} models", file=sys.stderr)
    return offers


def parse_kia_text(text, model_name):
    """See parse_kia.py for the fully-commented, tested version of this
    function against real sample data. Kept in sync with it here."""
    heading_pattern = re.compile(r"##\s+" + re.escape(model_name) + r"\s+(\S[^\n]*)")
    row_pattern = re.compile(
        r"(\d[\d.]*)\s*km\n([\d.]+)\s*kr\.\n(\d+)\s*mdr\.\n([\d.]+)\s*kr\.\n"
        r"[\d.]+\s*kr\.\s*/\s*halvår\n[\d.]+\s*kr\.\n[\d.]+\s*kr\.\n[\d.]+\s*kr\."
    )
    headings = list(heading_pattern.finditer(text))
    seen = {}
    for idx, h in enumerate(headings):
        variant = h.group(1).strip()
        section_end = headings[idx + 1].start() if idx + 1 < len(headings) else len(text)
        section = text[h.end():section_end]
        for m in row_pattern.finditer(section):
            km = int(m.group(1).replace(".", ""))
            if km != 10000:
                continue
            down = int(m.group(2).replace(".", ""))
            key = (variant, down)
            seen[key] = {
                "maerke": "Kia",
                "model": model_name,
                "variant": variant,
                "udbetaling_kr": down,
                "ydelse_kr": int(m.group(4).replace(".", "")),
                "loebetid_mdr": int(m.group(3)),
                "km_aar": km,
                "kilde_url": KIA_MODELS.get(model_name, f"https://kiaonline.dk/biler/{model_name.lower().replace(' ', '-')}/"),
                "sidst_tjekket": TODAY,
                "status": "Aktiv",
                "type": MODEL_TYPES.get(model_name, "hatchback"),
            }
    return list(seen.values())


def fetch_kia_offers():
    all_offers = []
    for model_name, url in KIA_MODELS.items():
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"WARNING: failed to fetch Kia {model_name}: {e}", file=sys.stderr)
            continue
        offers = parse_kia_text(resp.text, model_name)
        if not offers:
            _debug_response(f"Kia {model_name}", resp)
        print(f"  Kia {model_name}: parsed {len(offers)} offers", file=sys.stderr)
        all_offers.extend(offers)
    return all_offers


def parse_toyota_text(text):
    """See parse_toyota.py for the fully-commented, tested version of this
    function against real sample data. Kept in sync with it here."""
    pattern = re.compile(
        r"(?:\*\*([^*\n]+)\*\*|(?<!#)##(?!#)\s+([^\n]+))\s*"
        r".*?"
        r"Månedlig ydelse:\s*([\d.]+)\s*kr\.\s*pr\.\s*måned\.\s*"
        r"Førstegangsydelse:\s*([\d.]+)\s*kr\.\s*"
        r"Kilometer pr\. år:\s*([\d.,]+)\s*km\.\s*"
        r"Periode:\s*(\d+)\s*måneder",
        re.DOTALL,
    )
    url_pattern = re.compile(r"\[Se kampagnen her.*?\]\((https://[^\)]+)\)")

    seen = {}
    for m in pattern.finditer(text):
        variant = (m.group(1) or m.group(2)).strip()
        ydelse = int(m.group(3).replace(".", ""))
        udbetaling = int(m.group(4).replace(".", ""))
        km = int(m.group(5).replace(".", "").replace(",", ""))
        term = int(m.group(6))

        url_match = url_pattern.search(text, m.end())
        kilde_url = url_match.group(1) if url_match else TOYOTA_CAMPAIGNS_URL

        key = (variant, udbetaling, ydelse)
        seen[key] = {
            "maerke": "Toyota",
            "model": variant.split()[0],
            "variant": variant,
            "udbetaling_kr": udbetaling,
            "ydelse_kr": ydelse,
            "loebetid_mdr": term,
            "km_aar": km,
            "kilde_url": kilde_url,
            "sidst_tjekket": TODAY,
            "status": "Aktiv",
            "type": MODEL_TYPES.get(variant.split()[0], "hatchback"),
        }
    return list(seen.values())


def fetch_toyota_offers():
    try:
        resp = requests.get(TOYOTA_CAMPAIGNS_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"WARNING: failed to fetch Toyota campaigns: {e}", file=sys.stderr)
        return []
    offers = parse_toyota_text(resp.text)
    if not offers:
        _debug_response("Toyota", resp)
    print(f"  Toyota: parsed {len(offers)} offers", file=sys.stderr)
    return offers


def parse_renault_text(text):
    """See parse_renault.py for the fully-commented, tested version of this
    function against real sample data. Kept in sync with it here.

    NOTE ON COVERAGE: this page only shows ONE featured variant per model
    (the "frapris" / starting price) -- not the full matrix of trims and
    down-payment tiers. See manual_offers.json for the rest, and
    parse_renault.py's docstring for the PDF follow-up idea.
    """
    detail_pattern = re.compile(
        r"\*\*Den viste bil er en[^.]+\.\s*"
        r"Privatleasing via [^.]+\.\s*"
        r"(?P<variant>[^.]+)\.\s*"
        r"Leasingperiode\s*(?P<term>\d+)\s*mdr\.\s*og\s*"
        r"(?P<km>[\d.]+)\s*km\s*pr\.\s*år;\s*"
        r"Udbetaling kr\.\s*(?P<down>[\d.]+),-\.\s*"
        r"Fast leasingydelse pr\. mdr\. kr\.\s*(?P<price>[\d.]+),-\."
    )
    link_pattern = re.compile(
        r"\]\((?P<url>https://www\.renault\.dk/kob/privatleasing/[a-z0-9\-]+)\s*\"\"\)",
    )

    seen = {}
    for m in detail_pattern.finditer(text):
        variant = m.group("variant").strip()
        model = variant.split()[1] if variant.lower().startswith("renault") else variant.split()[0]
        down = int(m.group("down").replace(".", ""))
        price = int(m.group("price").replace(".", ""))
        km = int(m.group("km").replace(".", ""))
        term = int(m.group("term"))

        preceding = text[:m.start()]
        link_matches = list(link_pattern.finditer(preceding))
        kilde_url = link_matches[-1].group("url") if link_matches else RENAULT_PRIVATLEASING_URL

        key = (variant, down)
        seen[key] = {
            "maerke": "Renault",
            "model": model,
            "variant": variant,
            "udbetaling_kr": down,
            "ydelse_kr": price,
            "loebetid_mdr": term,
            "km_aar": km,
            "kilde_url": kilde_url,
            "sidst_tjekket": TODAY,
            "status": "Aktiv",
            "type": MODEL_TYPES.get(model, "hatchback"),
        }
    return list(seen.values())


def fetch_renault_offers():
    try:
        resp = requests.get(RENAULT_PRIVATLEASING_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"WARNING: failed to fetch Renault privatleasing page: {e}", file=sys.stderr)
        return []
    offers = parse_renault_text(resp.text)
    if len(offers) < 2:
        _debug_response("Renault", resp)
    print(f"  Renault: parsed {len(offers)} offers", file=sys.stderr)
    return offers


def main():
    print("Fetching live Volkswagen prices...", file=sys.stderr)
    vw_offers = fetch_vw_offers()

    print("Fetching live Skoda prices...", file=sys.stderr)
    skoda_offers = fetch_skoda_offers()

    print("Fetching live Toyota campaign prices...", file=sys.stderr)
    toyota_offers = fetch_toyota_offers()

    print("Fetching live Renault privatleasing prices...", file=sys.stderr)
    renault_offers = fetch_renault_offers()

    print("Fetching live Kia model pages...", file=sys.stderr)
    kia_offers = fetch_kia_offers()

    # Each brand is checked independently: one brand's site having a bad day
    # (or having changed its structure) shouldn't block the others' update.
    problems = []
    if len(vw_offers) < MIN_EXPECTED_VW_OFFERS:
        problems.append(f"VW: only {len(vw_offers)} offers (expected >= {MIN_EXPECTED_VW_OFFERS})")
    if len(skoda_offers) < MIN_EXPECTED_SKODA_OFFERS:
        problems.append(f"Skoda: only {len(skoda_offers)} offers (expected >= {MIN_EXPECTED_SKODA_OFFERS})")
    if len(toyota_offers) < MIN_EXPECTED_TOYOTA_OFFERS:
        problems.append(f"Toyota: only {len(toyota_offers)} offers (expected >= {MIN_EXPECTED_TOYOTA_OFFERS})")
    if len(renault_offers) < MIN_EXPECTED_RENAULT_OFFERS:
        problems.append(f"Renault: only {len(renault_offers)} offers (expected >= {MIN_EXPECTED_RENAULT_OFFERS})")
    if len(kia_offers) < MIN_EXPECTED_KIA_OFFERS:
        problems.append(f"Kia: only {len(kia_offers)} offers (expected >= {MIN_EXPECTED_KIA_OFFERS})")

    if problems:
        print(
            "ERROR: automated scrape looks unreliable this run:\n  - " +
            "\n  - ".join(problems) +
            "\nNOT overwriting data.js -- the site will keep showing the last "
            "known-good prices. Check whether the site structure changed, or "
            "whether the request got blocked, before re-running.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        with open("manual_offers.json", "r", encoding="utf-8") as f:
            manual_offers = json.load(f)
    except FileNotFoundError:
        print("WARNING: manual_offers.json not found, continuing without it.", file=sys.stderr)
        manual_offers = []

    all_records = vw_offers + skoda_offers + toyota_offers + renault_offers + kia_offers + manual_offers

    # Load the PREVIOUS data.js (this run's "before" snapshot) so we can flag
    # what changed -- new models, price moves, down-payment moves -- before
    # overwriting it. If this is the very first run, there's nothing to diff
    # against, so nothing gets a change disclaimer (correct: nothing "changed"
    # relative to an empty site).
    old_records = []
    try:
        with open("data.js", "r", encoding="utf-8") as f:
            old_text = f.read()
        old_json = old_text[old_text.index("["):old_text.rindex("]") + 1]
        old_records = json.loads(old_json)
    except (FileNotFoundError, ValueError):
        print("No previous data.js found -- first run, nothing to diff against.", file=sys.stderr)

    all_records = diff_and_annotate(all_records, old_records, TODAY)
    changed = [r for r in all_records if "change" in r]
    print(f"  {len(changed)} offer(s) changed since last run "
          f"({sum(1 for r in changed if 'new' in r['change']['types'])} new).", file=sys.stderr)

    with open("data.js", "w", encoding="utf-8") as f:
        f.write("// Auto-generated by update_prices.py -- do not hand-edit.\n")
        f.write(f"// Last run: {TODAY}\n")
        f.write("const CARFORYOU_DATA = ")
        f.write(json.dumps(all_records, ensure_ascii=False, indent=2))
        f.write(";\n")

    print(f"Wrote data.js with {len(all_records)} total offers "
          f"({len(vw_offers)} VW + {len(skoda_offers)} Skoda + {len(toyota_offers)} Toyota "
          f"+ {len(renault_offers)} Renault + {len(kia_offers)} Kia automated, "
          f"{len(manual_offers)} still manual "
          f"[BMW, Hyundai, Kia EV5, remaining Renault trims -- no scraper built yet]).",
          file=sys.stderr)


if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------
# RUNNING THIS ON A SCHEDULE (no server needed)
# ---------------------------------------------------------------------------
# A low-cost way to run this daily without managing a server:
#   1. Put this project in a GitHub repo (script + manual_offers.json +
#      carforyou.html + data.js).
#   2. Add a GitHub Actions workflow that runs on a daily schedule (cron),
#      executes `python update_prices.py`, and commits data.js if it changed.
#   3. Host the site itself on GitHub Pages or Netlify, pointed at the same
#      repo -- every time data.js updates, the live site updates automatically.
#   4. If the script exits with an error (see the safety check above), the
#      Action run fails and you get a notification -- rather than a silently
#      broken or empty price table going live.
# ---------------------------------------------------------------------------
