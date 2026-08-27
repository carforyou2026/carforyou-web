// articles.js: index of published articles. Each entry needs a matching
// HTML file (see filename). Adding a new article: write the page, then add
// one entry here so it appears on artikler.html and in any "related
// articles" listings. Kept as a separate small data file, same pattern as
// data.js and sponsorships.js, so the index never needs hand-editing HTML.
//
// `tags` drive the "related articles" matching on model pages (see
// build_model_pages.py); tag with brand names (lowercase, e.g. "volkswagen"),
// body types ("elbil", "plugin-hybrid"), or "alle-maerker" for anything
// broadly relevant regardless of brand.

const ARTICLES = [
  {
    slug: "bilafgifter-2026",
    filename: "artikel-bilafgifter-2026.html",
    title: "Sådan påvirker de nye bilafgifter din leasingpris i 2026",
    summary: "Registreringsafgiften på dyre elbiler fastfryses i 2026, men en ny EU-målemetode kan gøre plugin-hybrider markant dyrere at lease. Her er, hvad der faktisk ændrer sig, og hvilke biler det rammer.",
    date: "2026-01-15",
    tag: "Afgifter",
    tags: ["afgifter", "elbil", "plugin-hybrid", "alle-maerker"]
  },
  {
    slug: "leasingrente-2026",
    filename: "artikel-leasingrente-2026.html",
    title: "Leasing bliver billigere: Renten på restafgift falder til 3,8% i 2026",
    summary: "Motorstyrelsen sænker renten på den udskudte registreringsafgift fra 4,6% til 3,8% fra 1. januar 2026. Det gør flexleasing og anden leasing med forholdsmæssig afgift billigere. Her er hvorfor.",
    date: "2026-01-05",
    tag: "Priser",
    tags: ["priser", "rente", "alle-maerker"]
  },
  {
    slug: "gennemsnitspris-privatleasing-2026",
    filename: "artikel-gennemsnitspris-2026.html",
    title: "Hvad koster privatleasing i gennemsnit i 2026, og hvordan undgår du prisfælden?",
    summary: "4 ud af 10 danskere vælger leasing frem for bilkøb. Men en lav månedlig pris kan skjule en høj førstegangsydelse eller lavt kilometertal. Sådan sammenligner du tilbud reelt.",
    date: "2026-02-20",
    tag: "Guide",
    tags: ["guide", "priser", "alle-maerker"]
  },
  {
    slug: "billigste-leasingbiler-2026",
    filename: "artikel-billigste-leasingbiler-2026.html",
    title: "Billigste leasingbiler i 2026: De 5 laveste priser lige nu",
    summary: "Renault Twingo topper som billigste privatleasing i 2026 til 2.195 kr./md. Se de 5 billigste modeller på tværs af Volkswagen, Toyota, Kia og Renault, opdateret fra live priser.",
    date: "2026-08-22",
    tag: "Priser",
    tags: ["priser", "elbil", "alle-maerker", "renault", "volkswagen", "kia"]
  }
];
