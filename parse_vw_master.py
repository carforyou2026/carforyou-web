import re
import json
import sys

def parse_vw_master_pricelist(text):
    """
    Parses https://prislister.volkswagen.dk/leasingpriser -- a single PDF
    covering VW's ENTIRE Danish leasing lineup (T-Roc, both ID. Buzz sizes,
    ID. Polo, ID.3 Neo, ID.4, ID.5, ID.7 Tourer), every variant, every
    down-payment tier, every km/year option -- in one document.

    This replaces the old per-model VW_MODELS approach: one fetch now covers
    every VW model instead of guessing individual model-page URLs.

    SCOPE DECISION: the source has up to 8 km/year tiers per variant/down-
    payment combo. To keep the site's card count sane (and consistent with
    how every other brand's data is currently shown), we only extract the
    10.000 km/år row here -- the standard tier used everywhere else on the
    site. The full matrix is genuinely in the source if a "choose your
    km/year" filter gets built later; this is a deliberate v1 scope cut, not
    a technical limitation.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    records = []
    current_model = None
    current_variant = None

    row_pattern = re.compile(
        r"^10\.000 km/år (\d+) mdr\.\s+[\d.]+\s*kr\.\s+[\d.]+\s*kr\.\s+"
        r"([\d.]+)\s*kr\.\s+([\d.]+)\s*kr\.$"
    )

    for i, line in enumerate(lines):
        if line.endswith("leasingpriser"):
            current_model = line[: -len(" leasingpriser")].strip()
            current_variant = None
            continue
        if line.startswith("Rækkevidde") or line.startswith("CO2:"):
            current_variant = lines[i - 1] if i > 0 else None
            continue
        m = row_pattern.match(line)
        if m and current_model and current_variant:
            term = int(m.group(1))
            down = int(m.group(2).replace(".", ""))
            price = int(m.group(3).replace(".", ""))
            records.append({
                "maerke": "Volkswagen",
                "model": current_model,
                "variant": current_variant,
                "udbetaling_kr": down,
                "ydelse_kr": price,
                "loebetid_mdr": term,
                "km_aar": 10000,
                "kilde_url": "https://prislister.volkswagen.dk/leasingpriser",
            })

    # Dedupe on (model, variant, down) -- source repeats identical blocks
    # sometimes, same pattern seen on the individual model pages before.
    seen = {}
    for r in records:
        key = (r["model"], r["variant"], r["udbetaling_kr"])
        seen[key] = r
    return list(seen.values())


if __name__ == "__main__":
    with open("vw_master_raw.txt", "r", encoding="utf-8") as f:
        text = f.read()
    results = parse_vw_master_pricelist(text)
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n--- Parsed {len(results)} offers from sample ---", file=sys.stderr)
