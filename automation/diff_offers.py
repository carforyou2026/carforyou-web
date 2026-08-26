"""
diff_offers.py

Compares a freshly-scraped dataset against the previous data.js and
annotates any offer whose price or down payment changed -- or that's
entirely new -- with a `change` field the website renders as a disclaimer.

MATCHING LOGIC (read this before changing it):
Offers are tracked by (maerke, model, variant) -- not including udbetaling_kr,
since the down payment is one of the things we want to detect changes in,
not part of an offer's identity. Some trims have several simultaneous
down-payment options (e.g. VW's "30.000 kr. down" vs "15.000 kr. down" for
the same trim) -- these are matched old-to-new by SORTING each trim's rows
by udbetaling_kr and pairing by position (rank matching). This is a
deliberate, documented approximation: if the *number* of down-payment tiers
offered for a trim changes between runs, the pairing can be imprecise. Good
enough for a "here's roughly what changed" disclaimer; not a claim of
perfect entity tracking.
"""

from collections import defaultdict


def fmt_kr(n):
    sign = "-" if n < 0 else "+" if n > 0 else ""
    return f"{sign}{abs(n):,.0f}".replace(",", ".") + " kr."


def fmt_abs_kr(n):
    return f"{n:,.0f}".replace(",", ".") + " kr."


def _group(records):
    g = defaultdict(list)
    for r in records:
        g[(r["maerke"], r["model"], r["variant"])].append(r)
    for key in g:
        g[key].sort(key=lambda r: r["udbetaling_kr"])
    return g


def diff_and_annotate(new_records, old_records, run_date):
    """Mutates and returns new_records, adding a `change` dict to any
    offer that's new or whose price/down payment differs from last run.
    Offers with no detected change are left untouched (no `change` key).

    `run_date` (ISO string, e.g. "2026-08-09") is stamped onto every change
    as `date` -- the site uses this to hide disclaimers older than 30 days,
    checked client-side against the viewer's current date so it stays
    correct even if the scraper hasn't run in a while."""
    old_groups = _group(old_records)

    for key, new_list in _group(new_records).items():
        old_list = old_groups.get(key)
        for i, r in enumerate(new_list):
            old = old_list[i] if old_list and i < len(old_list) else None

            if old is None:
                r["change"] = {
                    "types": ["new"],
                    "notes": ["Ny model/variant tilføjet siden sidste opdatering."],
                    "date": run_date,
                }
                continue

            notes = []
            types = []
            if r["ydelse_kr"] != old["ydelse_kr"]:
                delta = r["ydelse_kr"] - old["ydelse_kr"]
                types.append("price_up" if delta > 0 else "price_down")
                notes.append(
                    f"Månedlig ydelse ændret fra {fmt_abs_kr(old['ydelse_kr'])} til "
                    f"{fmt_abs_kr(r['ydelse_kr'])} ({fmt_kr(delta)})."
                )
            if r["udbetaling_kr"] != old["udbetaling_kr"]:
                delta = r["udbetaling_kr"] - old["udbetaling_kr"]
                types.append("down_up" if delta > 0 else "down_down")
                notes.append(
                    f"Udbetaling (engangsgebyr) ændret fra {fmt_abs_kr(old['udbetaling_kr'])} til "
                    f"{fmt_abs_kr(r['udbetaling_kr'])} ({fmt_kr(delta)})."
                )
            if notes:
                r["change"] = {"types": types, "notes": notes, "date": run_date}

    return new_records
