import re
import json
import sys

def parse_kia_text(text, model_name):
    """
    Parses https://kiaonline.dk/biler/{model}/ into structured leasing offer
    records. Unlike /konfigurator/ pages (JS-only, blank on fetch), these are
    ordinary server-rendered WordPress pages -- no headless browser needed.

    Structure: a "## {Model} {Variant}" heading per trim, followed (further
    down) by flattened row data repeating:
        {km} km
        {down} kr.
        {term} mdr.
        {monthly} kr.
        {green tax}
        {return fee}
        {total12}
        {total}
    once per (down-payment tier x km tier) combination. We keep only the
    10.000 km/år rows, matching the scope decision used for VW.
    """
    heading_pattern = re.compile(r"##\s+" + re.escape(model_name) + r"\s+(\S[^\n]*)")
    row_pattern = re.compile(
        r"(\d[\d.]*)\s*km\n([\d.]+)\s*kr\.\n(\d+)\s*mdr\.\n([\d.]+)\s*kr\.\n"
        r"[\d.]+\s*kr\.\s*/\s*halvår\n[\d.]+\s*kr\.\n[\d.]+\s*kr\.\n[\d.]+\s*kr\."
    )

    headings = list(heading_pattern.finditer(text))
    seen = {}
    for idx, h in enumerate(headings):
        variant = h.group(1).strip()
        section_start = h.end()
        section_end = headings[idx + 1].start() if idx + 1 < len(headings) else len(text)
        section = text[section_start:section_end]

        for m in row_pattern.finditer(section):
            km = int(m.group(1).replace(".", ""))
            if km != 10000:
                continue
            down = int(m.group(2).replace(".", ""))
            term = int(m.group(3))
            price = int(m.group(4).replace(".", ""))
            key = (variant, down)
            seen[key] = {
                "maerke": "Kia",
                "model": model_name,
                "variant": variant,
                "udbetaling_kr": down,
                "ydelse_kr": price,
                "loebetid_mdr": term,
                "km_aar": km,
                "kilde_url": f"https://kiaonline.dk/biler/{model_name.lower().replace(' ', '-')}/",
            }
    return list(seen.values())


if __name__ == "__main__":
    with open("kia_sample.txt", "r", encoding="utf-8") as f:
        text = f.read()
    results = parse_kia_text(text, "PV5 Passenger")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n--- Parsed {len(results)} offers from sample ---", file=sys.stderr)
