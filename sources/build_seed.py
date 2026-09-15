#!/usr/bin/env python3
"""Build napoleon_seed.json from verified PD indexes.

Quotes are verbatim from public-domain translations:
 - Bingham, Selection (London, 1884), Vol I  -> sources/bingham_vol1.json
 - Confidential Correspondence Napoleon & Josephine (London, 1856) -> sources/josephine1856.json
Light cleanup only: running heads removed, spacing normalised. No words altered.
"""
import json, re

B = json.load(open("sources/bingham_vol1.json"))
J = json.load(open("sources/josephine1856.json"))

RUNHEAD = re.compile(r"\b[A-Z][A-Z \.]{8,55}\.?(\s+\d{1,3})?\b(?=[A-Z0-9 \.,;])")
RUNHEAD_NUM = re.compile(r"[A-Z][A-Z \.]{8,55}\. \d{1,3}")
GOCORR = re.compile(r"\bgo THE CORRESPONDENCE OF NAPOLEON\.?")

def clean(s, limit=300):
    s = RUNHEAD_NUM.sub(" ", s)
    s = GOCORR.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip(" \"'*^~")
    s = re.sub(r"(\w)-\s+(\w)", r"\1\2", s)          # hyphenated breaks
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)
    s = re.sub(r"\.{3,}", ".", s)
    s = re.sub(r"(?<!\.)\.\.(?!\.)", ".", s)
    s = re.sub(r"([A-Za-z])\d(?=[\s.,;:\]])", r"\1", s)  # footnote digits
    s = re.sub(r"\b[Ff] \d\b", "", s)
    s = re.sub(r"\s+''", "", s)
    s = re.sub(r"\^", "", s)
    s = re.sub(r"^M\. ", "", s)
    s = re.sub(r"\s+", " ", s).strip(" \"'")
    if len(s) <= limit:
        return s
    cut = s[:limit]
    for p in (". ", "! ", "? ", "; ", " — ", ", "):
        k = cut.rfind(p)
        if k > limit * 0.45:
            return cut[:k+1].strip() + " […]"
    return cut.strip() + " […]"

# Hand-set excerpts: every word appears in the OCR source in order;
# only punctuation/spacing restored, corrupt spans dropped with […].
OVERRIDE = {
 ("1796-04-02","SERURIER"): "I have learned with pain that our troops allowed themselves to be surprised yesterday at the village of St. Michel. […] You must not be astonished, my dear general, at the little check you have received; it will only be the prelude to our victory. […]",
 ("1796-04-06","ALBENGA"): "I have transferred my head-quarters to Albenga. The movement which I found commenced against Genoa has drawn the enemy out of his winter quarters. Beaulieu has published a manifesto, to which I shall reply after the battle. […]",
 ("1796-04-01","MONDOVI"): "The soldier without bread is driven to commit acts which make one blush to be a man. […] I have 100,000 men against me, and can oppose only 34,000 infantry and 3,500 cavalry to that force. […]",
 ("1796-05-17","FINANCES"): "When the Directory gave me the command of this army it drew up a plan of offensive warfare necessitating prompt measures and extraordinary resources. The advance of two sous in silver and of eight francs for the officers has not been paid, which discontents and discourages the army. […]",
 ("1796-05-17","MILANAIS"): "The French army, as generous as it is strong, will treat all peaceful inhabitants with fraternity; it will be as terrible as the fire from heaven towards rebels. […]",
 ("1796-12-17","DEC17"): "The army of Italy, properly so called, consisted primitively of 38,500 infantry. It has been reinforced by 10,000 men. We should therefore have 51,100 infantry had the army experienced no losses. […]",
 ("1797-08-17","TUSCANY"): "I consider it my duty to inform your Royal Highness that the Directory having every reason to be satisfied with the conduct of your Royal Highness during the whole of the Italian war, will seize every opportunity to testify the manner in which it regards these friendly proceedings. […]",
 ("1796-07-06","J"): "I have beaten the enemy. Kilmaine will send you the account. I am dead of fatigue. I entreat you to set out immediately for Verona. […] I give you a thousand kisses.",
 ("1796-07-16","J"): "I have passed the whole night under arms. I should have taken Mantua by a bold and well directed blow, but the waters of the lake suddenly fell, and my columns, embarked, could not reach their landing-place. […]",
 ("1796-07-21","J"): "I hope that on arriving this evening, I shall receive one of your letters. You know, my dear Josephine, how much pleasure they give me. […]",
 ("1796-07-22","J"): "The wants of the army require my presence in this region. It is impossible I should leave even to go to Milan. It would require five or six days. […]",
 ("1796-09-03","J"): "We are in full campaign, my adorable friend. We have overthrown the outposts of the enemy. […] The troops are in fine spirits, and well disposed. […]",
 ("1796-11-24","J"): "I hope very soon, my sweet love, to be in your arms. I love you most passionately. […] All goes well. Wurmser was beaten yesterday under Mantua. There is nothing wanted by your husband but the love of Josephine, in order to be happy.",
 ("1796-11-28","J"): "I have received the express which Berthier had dispatched from Genoa. You had not time to write me. I feel it sensibly. […]",
 ("1796-11-13","J"): "I do not love you at all; on the contrary, I detest you. You are a naughty woman, very crooked, very unfeeling, very ungenerous. Tu es une vilaine, bien gauche, bien bête, bien cendrillon. You do not write me at all. […]",
}
DROP = {("1800-05-18","CONSULS","Martigny")}

NAP = {"author": "Napoleon Bonaparte", "handle": "@bonaparte",
       "accountType": "person", "faction": "Army of Italy"}
NEL = {"author": "Horatio Nelson", "handle": "@horationelson",
       "accountType": "person", "faction": "Royal Navy (opposing)"}

# (src, iso, addrkey, placekey, loc, to-display, timeLabel, event, context, overridekey)
SEL = [
 ("b","1796-04-02","SERURIER",None,"Headquarters","To General Sérurier",None,"italy-1796","Eve of Montenotte: a check at San Michele, answered with a promise of revenge.","SERURIER"),
 ("b","1796-04-06","THE DIRECTORY",None,"Albenga","To the Directory",None,"italy-1796","Headquarters moved up; Genoa's alarm spoiled his plan to catch Beaulieu napping.","ALBENGA"),
 ("b","1796-04-14","THE DIRECTORY","Carcare","Carcare","To the Directory",None,"italy-1796","First victory dispatch: Montenotte, three days of manoeuvre.",None),
 ("b","1796-04-01","CARNOT",None,"Carcare","To Director Carnot",None,"italy-1796","Fighting Paris as well as Piedmont: no engineers, no artillery officers sent.",None),
 ("b","1796-04-01","THE DIRECTORY","Carru","Carru","To the Directory",None,"italy-1796","Mondovi report: the army he found — without bread, without discipline — and made examples.","MONDOVI"),
 ("b","1796-04-26","THE DIRECTORY",None,"Cherasco front","To the Directory",None,"italy-1796","Pillage punished: three shot, hard labour. Order before politics.","CHERASCO26"),
 ("b","1796-04-29","directory",None,"Cherasco","To the Directory",None,"italy-1796","Sardinia's armistice — signed against the Directory's orders: a king at his discretion.",None),
 ("b","1796-05-01","FAYPOULT",None,"Acqui","To Citizen Faypoult",None,"italy-1796","Connoisseur's shopping list: notes on fiefs, dukes — and their pictures and statues.",None),
 ("b","1796-05-01","THE DIRECTORY","Tortona","Tortona","To the Directory",None,"italy-1796","Thanks of the army voted; devotion to the constitution professed — for now.",None),
 ("b","1796-05-01","CARNOT",None,"Piacenza","To Director Carnot",None,"italy-1796","'We have at last crossed the Po': the second campaign opens; Beaulieu wants genius.","PLACENTIA"),
 ("b","1796-05-01","FINANCES",None,"Milan","To the Finance Minister",None,"italy-1796","An army in distress: pay months late, needs growing with every recruit.","FINANCES"),
 ("b","1796-05-01","MILANAIS",None,"Milan","To the Milanese",None,"italy-1796","Proclamation: fraternity for the peaceful — fire from heaven for rebels.","MILANAIS"),
 ("b","1796-05-29","VENICE",None,"Brescia","To the Republic of Venice",None,"italy-1796","Entering Venetian land in pursuit — but remembering long friendship.",None),
 ("b","1796-05-20","BROTHERS",None,"Milan","To his brothers in arms",None,"italy-1796","'Milan is ours': the torrent from the Apennines proclaimed to the troops.",None),
 ("b","1796-05-22","THE DIRECTORY",None,"Milan","To the Directory",None,"italy-1796","War pays: 6–8 millions in gold, ingots and jewels at Genoa for Paris.",None),
 ("b","1796-06-21","THE DIRECTORY",None,"Bologna","To the Directory",None,"italy-1796","A cardinal legate prisoner, four flags, and Parma's pictures claimed.",None),
 ("b","1796-10-16","WURMSER",None,"Modena","To General Wurmser",None,"italy-1796","Chivalry to the enemy: Mantua's marshes kill more surely than battles.",None),
 ("b","1796-10-27","EMPEROR",None,"Milan","To the Emperor",None,"italy-1796","A 27-year-old to an emperor: send plenipotentiaries — or lose Trieste.",None),
 ("b","1796-12-01","THE DIRECTORY",None,"Milan","To the Directory",None,"italy-1796","Alvinzi on the Brenta; Wurmser in extremis; an army of 38,500 that should be 51,000.","DEC17"),
 ("b","1797-02-01","THE DIRECTORY",None,"Tolentino","To the Directory",None,"campo-1797","Tolentino: the Pope pays for peace.",None),
 ("b","1797-04-16","THE DIRECTORY",None,"Leoben","To the Directory",None,"campo-1797","Preliminaries signed: Austria will treat without England.",None),
 ("b","1797-05-14","THE DIRECTORY",None,"Montebello","To the Directory",None,"campo-1797","Venice judged: an armed republic that plotted with Naples and the Pope.",None),
 ("b","1797-07-14","THE ARMY",None,"Milan","To the Army",None,"campo-1797","14 July order of the day: the fallen as example.",None),
 ("b","1797-07-26","CONSERVATORY",None,"Milan","To the Conservatory inspectors",None,"campo-1797","The general with no soul for music writes to its inspectors.",None),
 ("b","1797-08-01","TUSCANY",None,"Milan","To the Grand Duke of Tuscany",None,"campo-1797","Tuscany settled from Milan.","TUSCANY"),
 ("b","1797-11-01","FOREIGN MINISTER",None,"Rastatt","To the Foreign Minister",None,"campo-1797","From Rastatt: peacemaking as power politics.",None),
 ("b","1798-06-01","MALTA",None,"Aboard L'Orient","To the Bishop of Malta",None,"egypt-1798","To Malta's bishop, days before the island falls.",None),
 ("b","1798-07-21","KLEBER",None,"Cairo","To General Kléber",None,"egypt-1798","Written the day of the Pyramids.",None),
 ("b","1798-09-01","THE DIRECTORY",None,"Cairo","To the Directory",None,"egypt-1798","Two months in: accounting to Paris.",None),
 ("b","1798-12-21","CAIRO",None,"Cairo","To the inhabitants of Cairo",None,"egypt-1798","Proclamation after the October revolt.",None),
 ("b","1798-12-02","BERTHIER",None,"Cairo","To General Berthier",None,"egypt-1798","December night orders: troopers at 2 a.m., Arabs at dawn.",None),
 ("b","1799-01-02","TIPPOO",None,"Cairo","To Tippoo Sahib",None,"egypt-1798","To Mysore: the eastern alliance against England that never was.",None),
 ("b","1799-03-01","SIDNEY SMITH",None,"Acre","To Commodore Sidney Smith",None,"egypt-1798","Headquarters cartel letter to his Acre adversary.",None),
 ("b","1799-07-01","DIVAN",None,"Cairo","To the Divan of Cairo",None,"egypt-1798","Governing Egypt through its notables.",None),
 ("b","1799-08-01","DESAIX",None,"Cairo","To General Desaix",None,"egypt-1798","Upper Egypt orders, weeks before the secret departure.",None),
 ("b","1799-08-22","KLEBER",None,"Alexandria","To General Kléber",None,"egypt-1798","The farewell: Egypt to Kléber; France the prize.",None),
 ("b","1799-10-10","THE DIRECTORY",None,"Aix","To the Directory",None,"brumaire-1799","Back in France, reporting to the Directory he will overthrow in weeks.",None),
 ("b","1800-05-01","CONSULS","Lausanne","Lausanne","To the Consuls",None,"marengo-1800","Second Italian campaign opens: First Consul writing to his colleagues.",None),
 ("b","1800-06-20","CARNOT",None,"Milan","To Citizen Carnot",None,"marengo-1800","After Marengo: Kléber, Egypt, and broken capitulations.",None),
 ("b","1800-06-21","BERTHIER",None,"Milan","To General Berthier",None,"marengo-1800","Virtuosos for the 14 July fête — war administration as usual.",None),
 ("n","1794-05-20","MRS. NELSON",None,"Bastia","To Mrs. Nelson",None,"corsica-1793","OPPOSING VOICE: Nelson besieging Calvi — George III, King of Corsica.",None),
 ("n","1796-11-01","LOCKER",None,"At sea","To William Locker",None,"italy-1796","OPPOSING VOICE: Nelson quits Corsica — 'the first and the last of that kingdom.'",None),
]

JSEL = [
 ("1796-07-06","MORNING","italy-1796","Roverbella, after the chase: beaten enemy, dead fatigue, Verona summoned."),
 ("1796-07-16","TIME UNCERTAIN","italy-1796","Two hours after midnight at Marmirolo: a whole night under arms, Mantua missed."),
 ("1796-07-19","EVENING","italy-1796","Two days without her letters: thirty times counted in a day."),
 ("1796-07-21","MORNING","italy-1796","Castiglione, 8 a.m.: hoping her letter arrives by evening."),
 ("1796-07-22","MORNING","italy-1796","The army needs him: Milan must wait five or six days."),
 ("1796-08-10",None,"italy-1796","Brescia: first thought on arrival is her."),
 ("1796-09-03",None,"italy-1796","Ala, in full campaign: outposts overthrown."),
 ("1796-11-09",None,"italy-1796","Verona, day before yesterday arrived: fatigued, well, loving passionately."),
 ("1796-11-13",None,"italy-1796","The famous scolding: 'I do not love you at all' — Arcole-eve jealousy."),
 ("1796-11-24",None,"italy-1796","Wurmser beaten; loving 'à la fureur'."),
 ("1796-11-28",None,"italy-1796","Milan, midnight: no letter — felt 'sensibly' amid gaiety."),
]

def find_b(iso, key, place=None):
    c = [r for r in B if r["iso"] == iso and key in r["addr"]
         and (place is None or place.lower() in (r["place"] or "").lower())]
    if not c:
        raise SystemExit(f"NO MATCH b {iso} {key} {place}")
    return c[0]

def find_j(iso):
    c = [r for r in J if r["iso"] == iso]
    if not c:
        raise SystemExit(f"NO MATCH j {iso}")
    return c[0]

def ev_label_hour(h):
    if not h:
        return None
    if "AM" in h:
        n = int(h.split()[0])
        return "MORNING" if n not in (12,) else None
    if "PM" in h:
        n = int(h.split()[0])
        if n == 12:
            return "AFTERNOON"
        return "EVENING" if n >= 5 else "AFTERNOON"
    return None

out = []
seq = 0
def push(author_d, date, tlabel, loc, disp, src_title, archive, url, dtype, ctx, eid, to_line=None, cert="certain"):
    global seq
    seq += 1
    d = date.replace("-", "")
    out.append({
        "id": f"nap-{d}-{seq:02d}",
        "author": author_d["author"], "handle": author_d["handle"],
        "accountType": author_d["accountType"], "faction": author_d["faction"],
        "date": date, "timeLabel": tlabel or "TIME UNCERTAIN", "timePrecision": "day",
        "location": loc, "originalLanguage": "French" if author_d["author"].startswith("Napoleon") else "English",
        "displayText": disp, "sourceTitle": src_title, "archive": archive,
        "sourceUrl": url, "documentType": dtype, "evidenceType": "TRANSLATION",
        "dateCertainty": cert, "eventIds": [eid], "editorialStatus": "verified",
        "context": ctx + (" English from the 1884 Bingham translation (public domain); French in the Second Empire Correspondance." if "Bingham" in archive else " English from the 1856 Confidential Correspondence (public domain).")})

# explicit iso/cert fixes: (sel-iso, addrkey) -> (true iso, cert, note)
FIX = {
 ("1796-04-01", "CARNOT"): ("1796-04-14", "approximate", "Dateline partly illegible in scan; placed by content after Montenotte–Millesimo (12–14 Apr). "),
 ("1796-04-01", "MONDOVI"): ("1796-04-23", "approximate", "Dateline partly illegible in scan; placed by content after Mondovi (21–22 Apr). "),
 ("1796-05-01", "PLACENTIA"): ("1796-05-07", "approximate", "Dateline partly illegible in scan; placed by content at the Po crossing (7 May). "),
 ("1796-05-01", "MILANAIS"): ("1796-05-19", "approximate", "Dateline partly illegible in scan; placed by content amid the Milan proclamations (mid-May). "),
}

for src, iso, key, placekey, loc, toline, tlab, eid, ctx, ovkey in SEL:
    if (iso, key, loc) in DROP:
        continue
    if src == "b":
        r = find_b(iso, key, placekey)
        who = NEL if r["addr"] in ("MRS. NELSON", "WILLIAM LOCKER") else NAP
        cert = "approximate" if r.get("fuzzy_date") else "certain"
        disp = "“" + (OVERRIDE.get((iso, ovkey)) or clean(r["body"])) + "”"
        fix = FIX.get((iso, ovkey or key))
        if fix:
            iso, cert, note = fix
            ctx = note + ctx
        loc = {"AlbENGA": "Albenga", "Carru": "Carru", "2Qth": "Headquarters", "26M": "Cherasco front",
               "29M": "Cherasco", "I4^A": "Headquarters", "iZth": "Milan", "2Zth": "Montebello",
               "12M": "Milan", "14M": "Milan", "27 fA": "Milan", "28M": "Milan", "7M": "Headquarters",
               "13/A": "At sea", "17/A": "Cairo", "6M": "Cairo", "7M ": "Cairo", "Zth": "Headquarters",
               "iWi": "Milan", "26/A": "Headquarters", "I2": "Headquarters"}.get(loc, loc)
        push(who, iso, tlab, loc if loc != "Headquarters" or r["place"] else (r["place"] or "Headquarters"),
             disp,
             f"{toline}, {r['place'] or loc}, {iso}" if who is NAP else f"{toline} ({iso})",
             "Bingham, Selection from the Letters and Despatches (London, 1884), Vol. I — public domain",
             "https://archive.org/details/acp7797.0001.001.umich.edu",
             "letter", ctx, eid, cert=cert)
    else:
        r = find_b(iso, key, None)  # 'n' rows live in bingham index too
        push(NEL, iso, tlab, loc, "“" + clean(r["body"]) + "”",
             f"{toline} ({iso})",
             "Bingham, Selection (London, 1884), Vol. I — prints Nelson's letters as context — public domain",
             "https://archive.org/details/acp7797.0001.001.umich.edu",
             "letter (opposing voice)", ctx, eid)

for iso, tlab, eid, ctx in JSEL:
    r = find_j(iso)
    lab = tlab or ev_label_hour(r.get("hour")) or "TIME UNCERTAIN"
    push(dict(NAP, faction="Italy (love & war)"), iso, lab,
         r["place"].title(), "“" + (OVERRIDE.get((iso, "J")) or clean(r["body"])) + "”",
         f"To Josephine at Milan, {r['place'].title()}, {iso}",
         "Confidential Correspondence of Napoleon and Josephine (London, 1856) — public domain",
         "https://archive.org/details/confidentialcorr00napoiala",
         "love letter", ctx, eid)

json.dump(out, open("data/napoleon_seed.json", "w"), ensure_ascii=False, indent=1)
print("seed records:", len(out))
