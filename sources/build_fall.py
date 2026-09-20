#!/usr/bin/env python3
"""Fall 1810-1815: Bingham Vol III + Tarbell Fall + Josephine 1810-13."""
import json, sys
sys.path.insert(0, "sources")
from common import (clean, push, NAP, BINGHAM_URL, JOSEPHINE_URL, TARBELL_URL)

B3 = json.load(open("sources/bingham_vol3.json"))
J = json.load(open("sources/josephine1856.json"))
T = json.load(open("sources/tarbell.json"))

BARCH3 = "Bingham, Selection (London, 1884), Vol. III — public domain"
BURL3 = "https://archive.org/details/cu31924024332250"

def find_b(iso, key, place=None):
    import re as _re
    norm = lambda s: _re.sub(r"\s+", " ", (s or "").lower())
    c = [r for r in B3 if r["iso"] == iso and key in r["addr"]
         and (place is None or norm(place) in norm(r["place"]))]
    if not c:
        raise SystemExit(f"NO MATCH b3 {iso} {key} {place}")
    return c[0]

def find_t(frag, iso=None):
    c = [r for r in T if frag.lower() in r["title"].lower()]
    if iso:
        c = [r for r in c if r["iso"] == iso] or c
    if not c:
        raise SystemExit(f"NO MATCH t {frag}")
    return c[0]

out = []
NAPEMP = dict(NAP, faction="Empire")
NAPRU = dict(NAP, faction="Grande Armée")

SEL = [
 ("1810-03-22","CHAMPAGNY",None,"Compiègne","To Champagny","Empire","marie-louise-1810","Marie-Louise greeted at Compiègne."),
 ("1810-04-03","HOLLAND",None,"Paris","To Louis of Holland","Empire","holland-1810","Holland scolded toward annexation."),
 ("1810-05-16","RUSSIA",None,"Paris","To the Emperor of Russia","Empire","russia-friction","Erfurt promises fraying."),
 ("1810-06-20","RUSSIA",None,"St. Cloud","To the Emperor of Russia","Empire","russia-friction","Oldenburg and Poland: grievances listed."),
 ("1810-07-01","GAUDIN",None,"St. Cloud","To Gaudin","Empire","empire-admin","Finances of the great Empire."),
 ("1810-07-26","AUSTRIA",None,"St. Cloud","To the Emperor of Austria","Empire","marie-louise-1810","Father-in-law cultivated."),
 ("1810-08-02","RUSSIA",None,"St. Cloud","To the Emperor of Russia","Empire","russia-friction","Duchy of Warsaw arms: explained away."),
 ("1810-09-17","BERTHIER",None,"Fontainebleau","To Marshal Berthier","Empire","empire-admin","Army administration."),
 ("1810-09-20","DAVOUST",None,"St. Cloud","To Marshal Davout","Empire","empire-admin","The iron marshal instructed."),
 ("1810-10-01","SAVARY",None,"Fontainebleau","To Savary","Empire","empire-admin","Police minister's orders."),
 ("1810-11-04","SAVARY",None,"Fontainebleau","To Savary","Empire","empire-admin","Fouché's successor watched."),
 ("1811-06-07","BERTHIER",None,"Paris","To Marshal Berthier","Empire","russia-1812","Germany garrisoned for the coming war."),
 ("1811-08-02","MARET",None,"Trianon","To Maret","Empire","russia-1812","Diplomacy before the storm."),
 ("1811-08-16","DECRES",None,"St. Cloud","To Decrès","Empire","russia-1812","The navy in the northern scheme."),
 ("1811-08-23","DECRES",None,"St. Cloud","To Decrès","Empire","russia-1812","Baltic combinations."),
 ("1811-08-22","CLARKE",None,"St. Cloud","To Gen. Clarke","Empire","russia-1812","War ministry builds the invasion."),
 ("1811-09-03","MOLLIEN",None,"Compiègne","To Mollien","Empire","russia-1812","Treasury for 600,000 men."),
 ("1811-09-01","DAVOUST",None,"Compiègne","To Marshal Davout","Empire","russia-1812","Davout's corps prepared."),
 ("1811-11-01","BIGOT",None,"Wesel","To Bigot","Empire","russia-1812","Rhine logistics inspected."),
 ("1811-12-31","CHAMPAGNY",None,"Paris","To Champagny","Empire","russia-1812","New Year's diplomacy."),
 ("1812-03-07","MARET",None,"Paris","To Maret","Empire","russia-1812","Ultimatums drafted."),
 ("1812-04-06","BERTHIER",None,"St. Cloud","To Marshal Berthier","Grande Armée","russia-1812","The invasion staff work begins."),
 ("1812-06-16","BERTHIER",None,"Königsberg","To Marshal Berthier","Grande Armée","russia-1812","Niemen crossed: orders from Königsberg."),
 ("1812-07-02","MARET",None,"Biechenkovitchi","To Maret","Grande Armée","russia-1812","Vilna taken; politics follows."),
 ("1812-07-01","BERTHIER",None,"Wilna","To Marshal Berthier","Grande Armée","russia-1812","Wilna halt: the army reorganised."),
 ("1812-08-02","MONTESQUIOU",None,"Smolensk","To the Comtesse de Montesquiou","Grande Armée","russia-1812","Smolensk: news for the King of Rome's governess."),
 ("1812-08-07","MARET",None,"Vitebsk","To Maret","Grande Armée","russia-1812","Vitebsk halt debated."),
 ("1812-08-01","LAPLACE",None,"Vitebsk","To Laplace","Grande Armée","russia-1812","Savants amid invasion."),
 ("1812-08-29","MARET",None,"Viazma","To Maret","Grande Armée","russia-1812","Toward Moscow: Viazma."),
 ("1812-10-01","BERTHIER",None,"Moscow","To Marshal Berthier","Grande Armée","russia-1812","Moscow occupied; retreat looms."),
 ("1812-11-07","MARET",None,"Studienka","To Maret","Grande Armée","russia-1812","Berezina crossed: the wreck reports."),
 ("1812-12-14","AUSTRIA",None,"Paris","To the Emperor of Austria","Empire","russia-1812","Schwarzenberg thanked; alliance maintained."),
 ("1812-12-10","MARET",None,"Molodetchna","To Maret","Empire","russia-1812","Retreat bulletins from the snow."),
 ("1812-12-01","NARBONNE",None,"Smorgoni","To Narbonne","Empire","russia-1812","Smorgoni: command to Murat, sledge to Paris."),
 ("1813-01-01","EUGENE",None,"Fontainebleau","To Prince Eugène","Empire","leipzig-1813","Eugène holds the wreck together."),
 ("1813-01-26","EUGENE",None,"Fontainebleau","To Prince Eugène","Empire","leipzig-1813","New army ordered from nothing."),
 ("1813-03-02","EUGENE",None,"Trianon","To Prince Eugène","Empire","leipzig-1813","Spring campaign entrusted."),
 ("1813-03-12","JEROME",None,"Trianon","To King Jérôme","Empire","leipzig-1813","Westphalia mustered."),
 ("1813-04-26","SAVARY",None,"Erfurt","To Savary","Empire","leipzig-1813","Police for the German campaign."),
 ("1813-05-04","AUSTRIA",None,"Pegau","To the Emperor of Austria","Empire","leipzig-1813","Lützen won: Vienna courted."),
 ("1813-05-10","CAMBACERES",None,"Dresden","To Cambacérès","Empire","leipzig-1813","Paris governed from Dresden."),
 ("1813-05-12","AUSTRIA",None,"Wurchen","To the Emperor of Austria","Empire","leipzig-1813","Bautzen won: peace offered."),
 ("1813-05-07","CAULAINCOURT",None,"Paris","To Caulaincourt","Empire","leipzig-1813","Diplomat of the armistice."),
 ("1813-05-31","MARET",None,"Neumarkt","To Maret","Empire","leipzig-1813","Pläswitz armistice diplomacy."),
 ("1813-05-31","CLARKE",None,"Neumarkt","To Gen. Clarke","Empire","leipzig-1813","Armistice administration."),
 ("1813-06-01","DENMARK",None,"Paris","To the King of Denmark","Empire","leipzig-1813","Denmark kept in alliance."),
 ("1813-07-17","BIGOT",None,"Dresden","To Bigot","Empire","leipzig-1813","Dresden court business."),
 ("1813-08-17","MARET",None,"Bautzen","To Maret","Empire","leipzig-1813","Armistice ends: diplomacy fails."),
 ("1813-08-07","DAVOUST",None,"Paris","To Marshal Davout","Empire","leipzig-1813","Hamburg fortress held."),
 ("1813-08-01","DROUOT",None,"Dresden","To Gen. Drouot","Empire","leipzig-1813","Artillery genius employed."),
 ("1813-08-01","CAMBACERES",None,"Dresden","To Cambacérès","Empire","leipzig-1813","Paris in autumn crisis."),
 ("1813-08-26","VANDAMME",None,"Stolpen","To Gen. Vandamme","Empire","leipzig-1813","Kulm mission: cut the allies' rear."),
 ("1813-08-30","WIRTEMBERG",None,"Dresden","To the King of Württemberg","Empire","leipzig-1813","German ally steadied."),
 ("1813-09-02","BERTHIER",None,"Dresden","To Marshal Berthier","Empire","leipzig-1813","Staff work before Leipzig."),
 ("1813-09-01","NAPLES",None,"Dresden","To the King of Naples","Empire","leipzig-1813","Murat's loyalty tested."),
 ("1813-10-31","CAMBACERES",None,"Frankfort","To Cambacérès","Empire","leipzig-1813","Leipzig lost: Paris warned."),
 ("1813-11-10","SUSSY",None,"St. Cloud","To Sussy","Empire","france-1814","Bayonne frontier open; goods landed."),
 ("1813-11-10","CAULAINCOURT",None,"St. Cloud","To Caulaincourt","Empire","france-1814","Châtillon congress prepared."),
 ("1814-01-02","CLARKE",None,"St. Dizier","To Gen. Clarke","Empire","france-1814","Paris fortified on paper."),
 ("1814-01-10","MACDONALD",None,"Paris","To Marshal Macdonald","Empire","france-1814","Marshals summoned east."),
 ("1814-02-01","AUGEREAU",None,"Nogent","To Marshal Augereau","Empire","france-1814","Lyons must hold."),
 ("1814-02-02","JOSEPH",None,"Piney","To Prince Joseph","Empire","france-1814","Six Days open: Paris protected."),
 ("1814-02-06","CLARKE",None,"Troyes","To Gen. Clarke","Empire","france-1814","Troyes headquarters orders."),
 ("1814-02-10","JOSEPH",None,"Nogent","To Prince Joseph","Empire","france-1814","Champaubert won."),
 ("1814-02-14","JOSEPH",None,"Paris","To Prince Joseph","Empire","france-1814","Montmirail, Château-Thierry: victories wired home."),
 ("1814-02-07","EUGENE",None,"Nangis","To Prince Eugène","Empire","france-1814","Italy ordered to hold."),
 ("1814-02-20","JOSEPH",None,"Montereau","To Prince Joseph","Empire","france-1814","Montereau: bridges burned, enemy thrown."),
 ("1814-03-03","JOSEPH",None,"Soissons","To Prince Joseph","Empire","france-1814","Soissons lost and retaken."),
 ("1814-03-14","JOSEPH",None,"Rheims","To Prince Joseph","Empire","france-1814","Rheims retaken."),
 ("1814-03-15","MARMONT",None,"Rheims","To Marshal Marmont","Empire","france-1814","Marmont's corps directed."),
 ("1814-03-10","JOSEPH",None,"Chavignon","To Prince Joseph","Empire","france-1814","Last bulletins to Paris."),
 ("1814-03-20","JOSEPH",None,"Plancy","To Prince Joseph","Empire","france-1814","Arcis: outnumbered, unbroken."),
 ("1814-03-23","BEETHIER",None,"Plessis","To Marshal Berthier","Empire","france-1814","Eastward march decided."),
 ("1814-06-10","BERTRAND",None,"Porto Ferrajo","To Gen. Bertrand","Empire","elba-1814","Elba household orders."),
 ("1814-08-26","BERTRAND",None,"La Madone","To Gen. Bertrand","Empire","elba-1814","Elba summer administration."),
 ("1814-09-01","BERTRAND",None,"La Madone","To Gen. Bertrand","Empire","elba-1814","Escape plotted under routine."),
 ("1815-02-26","LAPI",None,"Porto Ferrajo","To Gen. Lapi","Empire","elba-1814","Farewell to Elba: embarking for France."),
 ("1815-03-01","DAVOUST",None,"Paris","To Marshal Davout","Empire","waterloo-1815","Soissons, La Fère, Château-Thierry to resist attack."),
 ("1815-04-10","DAVOUST",None,"Paris","To Marshal Davout","Empire","waterloo-1815","Efface Berthier, Marmont, Victor and the rest from the marshals' list."),
 ("1815-04-24","CARNOT",None,"Paris","To Carnot","Empire","waterloo-1815","Pikes in every department, against musket shortage."),
 ("1815-04-26","DAVOUST",None,"Paris","To Marshal Davout","Empire","waterloo-1815","Suchet to Lyons; commands distributed."),
 ("1815-05-01","DAVOUST",None,"Paris","To Marshal Davout","Empire","waterloo-1815","Soult's double salary approved."),
 ("1815-05-27","DAVOUST",None,"Paris","To Marshal Davout","Empire","waterloo-1815","Guard soon marching; Paris quarters must be ready."),
 ("1815-06-01","DAVOUST",None,"Paris","To Marshal Davout","Empire","waterloo-1815","Grouchy gets the cavalry; Suchet takes Montmélian."),
 ("1815-06-06","DAVOUST",None,"Paris","To Marshal Davout","Empire","waterloo-1815","200 guns at Paris gates and works."),
 ("1815-03-01","GOLFE",None,"Golfe-Juan","To the French People","Empire","waterloo-1815","Golfe-Juan landing proclamation."),
 ("1815-06-16","JOSEPH",None,"Charleroi","To Prince Joseph","Empire","waterloo-1815","Fleurus: Letort lost, Sambre forced."),
 ("1815-06-16","NEY",None,"Charleroi","To Marshal Ney","Empire","waterloo-1815","Fateful orders: Grouchy to Sombreffe, Guard to Fleurus; Brussels the prize."),
 ("1815-06-14","JOSEPHB",None,"Charleroi","To Prince Joseph","Empire","waterloo-1815","Beaumont headquarters; Charleroi tomorrow. Dateline corrected from content."),
 ("1814-04-05","ARMYFB",None,"Fontainebleau","To the Army","Empire","fontainebleau-1814","Bingham misfiles the Fontainebleau farewell."),
]

TARCH = "Tarbell, Napoleon's Addresses (1897) — public domain translations"
TURL = TARBELL_URL

def find_tp(frag, iso=None):
    TP = json.load(open("sources/tarbell_picked.json"))
    c = [r for r in TP if frag.lower() in (r["key"] + " " + r["title"]).lower()]
    if not c:
        raise SystemExit(f"NO MATCH tp {frag}")
    return c[0]

TSEL = [
 ("borodino", "1812-09-07", "certain", "Borodino", "russia-1812", "Borodino eve address.", "Address before Borodino"),
 ("alexander12", "1812-09-20", "certain", "Moscow", "russia-1812", "From burning Moscow to Alexander.", "Letter to Alexander I"),
 ("legis13f", "1813-02-14", "certain", "Paris", "leipzig-1813", "Opening discourse to the legislators.", "Discourse to the Legislative Body"),
 ("legis13d", "1813-12-01", "approximate", "Paris", "leipzig-1813", "Winter address to the legislators.", "Address to the Legislative Body"),
 ("abdication-speech", "1814-04-04", "certain", "Fontainebleau", "fontainebleau-1814", "Abdication declared; edition misdates it.", "Declaration of Abdication"),
 ("old-guard", "1814-04-20", "certain", "Fontainebleau", "fontainebleau-1814", "The courtyard farewell.", "Farewell to the Old Guard"),
 ("anniversary15", "1815-06-14", "certain", "Beaumont", "waterloo-1815", "Are we not still the same men?", "Proclamation of June 14, 1815"),
 ("belgians", "1815-06-17", "certain", "Ligny", "waterloo-1815", "Ligny victory announced.", "Proclamation to the Belgians"),
 ("bellerophon", "1815-08-04", "certain", "Plymouth", "sthelena-1815", "Guest, not prisoner: the protest.", "Bellerophon Protest"),
]

JSEL = [
 ("1810-01-17", None, "marie-louise-1810", "Divorce winter: fortitude failing."),
 ("1810-04-21", None, "marie-louise-1810", "Bad style, same affections."),
 ("1810-06-10", None, "marie-louise-1810", "Ocean-isle dangers pitied."),
 ("1810-07-20", None, "marie-louise-1810", "Waters doing good."),
 ("1810-09-14", None, "marie-louise-1810", "The Empress decidedly... (pregnant)."),
 ("1810-10-02", None, "marie-louise-1810", "Hortense mediates."),
 ("1810-11-14", None, "marie-louise-1810", "Contentment reported."),
 ("1811-01-08", None, "russia-1812", "New Year thanks."),
 ("1811-03-22", None, "russia-1812", "My son is stout: the King of Rome thrives."),
 ("1813-08-25", None, "leipzig-1813", "Trianon days amid armistice."),
]

out = []
GA_EVENTS = {"russia-1812", "leipzig-1813", "france-1814", "waterloo-1815"}

for iso, key, placekey, loc, toline, fac, eid, ctx in SEL:
    if key in ("JOSEPHB", "ARMYFB"):
        r = find_b("1815-06-01", "JOSEPH" if key == "JOSEPHB" else "ARMY", placekey)
    elif key == "GOLFE":
        r = find_b("1815-03-01", "FRENCH PEOPLE", placekey)
    else:
        r = find_b(iso, key, placekey)
    cert = "approximate" if (r.get("fuzzy_date") or key in ("JOSEPHB", "ARMYFB", "GOLFE")) else "certain"
    push(out, NAP, fac, iso, None, loc,
         "“" + clean(r["body"]) + "”",
         f"{toline}, {iso}",
         BARCH3, BURL3, "letter", ctx, eid, cert=cert)
print("bingham fall:", len(out))

for frag, iso, cert, loc, eid, ctx, dtitle in TSEL:
    r = find_tp(frag, None if cert == "approximate" else iso)
    fac = "Grande Armée" if eid in GA_EVENTS else "Empire"
    push(out, NAP, fac, iso, None, loc, "“" + clean(r["body"], 340) + "”",
         dtitle + f", {iso}", "Tarbell, Napoleon's Addresses (1897) — public domain translations",
         TARBELL_URL, "proclamation", ctx, eid, cert=cert)
print("total fall:", len(out))

def ev_label_hour(h):
    if not h:
        return None
    if "AM" in h:
        n = int(h.split()[0])
        return "MORNING" if n != 12 else None
    if "PM" in h:
        n = int(h.split()[0])
        return "EVENING" if (n >= 5 and n != 12) else "AFTERNOON"
    return None

J = json.load(open("sources/josephine1856.json"))
for iso, tlab, eid, ctx in JSEL:
    c = [r for r in J if r["iso"] == iso]
    if not c:
        raise SystemExit(f"NO MATCH j {iso}")
    r = c[0]
    lab = tlab or ev_label_hour(r.get("hour")) or "TIME UNCERTAIN"
    fac = "Grande Armée" if eid in GA_EVENTS else "Empire"
    push(out, dict(NAP, faction="Empire"), fac, iso, lab,
         r["place"].title(), "“" + clean(r["body"]) + "”",
         f"To Josephine, {r['place'].title()}, {iso}",
         "Confidential Correspondence of Napoleon and Josephine (London, 1856) — public domain",
         JOSEPHINE_URL, "love letter", ctx, eid)

json.dump(out, open("data/nap_fall.json", "w"), ensure_ascii=False, indent=1)
print("wrote nap_fall:", len(out))
