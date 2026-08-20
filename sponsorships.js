// sponsorships.js
//
// Paid placement config -- manually managed, separate from data.js (which
// is only ever scraped/factual price data). Keeping these apart means a
// sponsorship deal can never accidentally alter a real price, and a price
// update can never accidentally drop or add a sponsorship.
//
// HOW TO USE:
// - "hero": the single paid placement at the top of the page (the most
//   expensive inventory slot). Match it to a real offer via maerke/model/
//   variant so the price shown is always the live, accurate one -- never
//   hand-type a price here.
// - "featured": an array of paid placements inside the offers grid. Each
//   one is matched the same way. Matched offers are pinned to the top of
//   the grid (within whatever filters are currently active) and get a
//   visible "Sponsoreret" badge -- see CRITICAL NOTE below.
// - Every entry needs start_date/end_date (YYYY-MM-DD). Outside that
//   window, the placement is automatically treated as expired and the site
//   falls back to normal, unpaid behaviour -- so a lapsed contract can
//   never keep showing a "Sponsoreret" placement for free.
//
// CRITICAL: every placement funded by this file MUST render with a visible
// "Sponsoreret" label. This isn't just good practice -- paid placement
// presented as neutral comparison is a real legal problem under Danish
// marketing law (Forbrugerombudsmanden requires clear ad disclosure). Don't
// remove or hide the badge rendering in carforyou.html to "clean up" a
// sponsor's card.

const SPONSORSHIPS = {
  "hero": {
    "maerke": "Kia",
    "model": "EV4",
    "variant": "Prestige",
    "udbetaling_kr": 49995,
    "sponsor_label": "Kia Danmark",
    "start_date": "2026-08-01",
    "end_date": "2026-08-31"
  },
  "featured": [
    {
      "maerke": "Volkswagen",
      "model": "ID.4",
      "variant": "Move 286 hk",
      "udbetaling_kr": 20000,
      "sponsor_label": "Skandinavisk Motor Co.",
      "start_date": "2026-08-01",
      "end_date": "2026-08-31"
    },
    {
      "maerke": "Renault",
      "model": "5",
      "variant": "Evolution EV40",
      "udbetaling_kr": 14995,
      "sponsor_label": "Renault Danmark",
      "start_date": "2026-08-01",
      "end_date": "2026-09-15"
    }
  ]
};
