#!/usr/bin/env python3
"""Empire 1803-1809 seed: Bingham Vol II + Tarbell proclamations + Josephine."""
import json, re, sys
sys.path.insert(0, "sources")
from common import (clean, push, NAP, BINGHAM_URL, JOSEPHINE_URL, TARBELL_URL)

B = json.load(open("sources/bingham_vol2.json"))
B1 = json.load(open("sources/bingham_vol1.json"))
J = json.load(open("sources/josephine1856.json"))
T = json.load(open("sources/tarbell_picked.json"))

NEL = {"author": "Horatio Nelson", "handle": "@horationelson", "accountType": "person"}

def find_b(iso, key, place=None):
    pool = B + B1
    norm = lambda s: re.sub(r"\s+", " ", (s or "").lower())
    c = [r for r in pool if r["iso"] == iso and key in r["addr"]
         and (place is None or norm(place) in norm(r["place"]))]
    if not c:
        raise SystemExit(f"NO MATCH b {iso} {key} {place}")
    return c[0]

def find_t(frag, iso=None):
    c = [r for r in T if frag.lower() in (r["key"] + " " + r["title"]).lower()]
    if iso:
        c = [r for r in c if r["iso"] == iso] or c
    if not c:
        raise SystemExit(f"NO MATCH t {frag}")
    return c[0]

def find_j(iso):
    c = [r for r in J if r["iso"] == iso]
    if not c:
        raise SystemExit(f"NO MATCH j {iso}")
    return c[0]

out = []
NAPC = dict(NAP)
NAPCONS = dict(NAP, faction="Consulate")
NAPEMP = dict(NAP, faction="Empire")
NAPGA = dict(NAP, faction="Grande Armée")

# (iso, addrkey, placekey, loc, to, faction, event, context)
SEL = [
 ("1803-05-01","TALLEYRAND",None,"St. Cloud","To Talleyrand","Consulate","consulate-1802","Amiens ruptured: the truce is over, the invasion army rises."),
 ("1803-08-01","DECRES","Sedan","Sedan","To Decrès","Consulate","boulogne-1803","Flotilla orders: flatboats, tides, Boulogne."),
 ("1803-09-01","TALLEYRAND",None,"Malmaison","To Talleyrand","Consulate","boulogne-1803","Invasion diplomacy between reviews."),
 ("1803-11-10","TALLEYRAND","Boulogne","Boulogne","To Talleyrand","Consulate","boulogne-1803","From the invasion camp."),
 ("1803-11-12","AUGEREAU",None,"Boulogne","To Gen. Augereau","Consulate","boulogne-1803","Boulogne camps: invasion of England prepared."),
 ("1804-02-14","SOULT",None,"Malmaison","To Gen. Soult","Consulate","empire-1804","Camp of Boulogne: Soult drills the invasion army."),
 ("1804-03-10","MURAT",None,"Malmaison","To Gen. Murat","Consulate","empire-1804","Murat governs Paris as the Enghien crisis breaks."),
 ("1804-04-10","POPE",None,"St. Cloud","To the Pope","Consulate","empire-1804","Invitation to Paris: crown me."),
 ("1804-05-10","TALLEYRAND",None,"St. Cloud","To Talleyrand","Empire","empire-1804","The new Empire's diplomacy opens."),
 ("1804-05-30","TALLEYRAND",None,"St. Cloud","To Talleyrand","Empire","empire-1804","Consolidating the throne."),
 ("1804-06-10","SOULT",None,"St. Cloud","To Marshal Soult","Empire","empire-1804","Marshals for the Empire."),
 ("1804-07-12","OTTO",None,"Paris","To M. Otto","Empire","empire-1804","England watched through Paris."),
 ("1804-07-21","JOSEPHINE",None,"Pont de Briques","To Josephine","Empire","empire-1804","From the invasion coast."),
 ("1804-09-01","DECRE",None,"Aix-la-Chapelle","To Decrès","Empire","boulogne-1803","The fleet must be ready."),
 ("1804-09-10","POPE",None,"Paris","To the Pope","Empire","empire-1804","Coronation details settled."),
 ("1804-09-14","FOUCHE",None,"Mayence","To Fouché","Empire","empire-1804","Police on the Rhine tour."),
 ("1804-09-16","FESCH",None,"Paris","To Cardinal Fesch","Empire","empire-1804","Family cardinal managed."),
 ("1804-10-01","JOSEPHINE",None,"Treves","To Josephine","Empire","empire-1804","On the road to the coronation."),
 ("1804-10-29","FOUCHE",None,"St. Cloud","To Fouché","Empire","empire-1804","Security for the sacred day."),
 ("1804-11-10","PRUSSIA",None,"St. Cloud","To the King of Prussia","Empire","empire-1804","Berlin courted before the storm."),
 ("1804-12-10","TALLEYRAND",None,"St. Cloud","To Talleyrand","Empire","empire-1804","Crowned: Europe notified."),
 ("1805-01-30","TURKEY",None,"Paris","To the Emperor of Turkey","Empire","austerlitz-1805","The eastern alliance cultivated."),
 ("1805-02-01","PORTUGAL",None,"Malmaison","To the Prince Regent of Portugal","Empire","austerlitz-1805","Lisbon pressed toward France."),
 ("1805-03-10","CHAMPAGNY",None,"St. Cloud","To Champagny","Empire","austerlitz-1805","Interior before the storm."),
 ("1805-04-01","MARMONT",None,"Lyons","To Gen. Marmont","Empire","austerlitz-1805","Italy armed for the coming war."),
 ("1805-04-10","TALLEYRAND","Chalon","Chalon","To Talleyrand","Empire","austerlitz-1805","Italy beckons; the Boulogne army eyes east."),
 ("1805-04-21","DECR",None,"Stupinigi","To Decrès","Empire","austerlitz-1805","Naval combinations for the invasion."),
 ("1805-05-06","MURAT",None,"Milan","To Prince Murat","Empire","austerlitz-1805","Milan: the Iron Crown taken."),
 ("1805-05-26","FOUCHE",None,"Paris","To Fouché","Empire","austerlitz-1805","Paris held while Italy crowns."),
 ("1805-05-29","CAMBACER",None,"Milan","To Cambacérès","Empire","austerlitz-1805","Paris governed from Milan."),
 ("1805-06-01","TALLEYRAND",None,"Milan","To Talleyrand","Empire","austerlitz-1805","Italian kingdom organised."),
 ("1805-07-20","BERTHIER",None,"St. Cloud","To Marshal Berthier","Empire","austerlitz-1805","Grande Armée staff work before the march."),
 ("1805-07-27","EUGENE",None,"St. Cloud","To Prince Eugène","Empire","austerlitz-1805","Italy entrusted to the stepson."),
 ("1805-07-31","TALLEYRAND",None,"St. Cloud","To Talleyrand","Empire","austerlitz-1805","Coalition forming: diplomacy races."),
 ("1805-08-10","DARU",None,"Boulogne","To Daru","Empire","austerlitz-1805","The camp breaks: administration turns toward the Rhine."),
 ("1805-08-10","ELIZA",None,"Boulogne","To Princess Eliza","Empire","austerlitz-1805","Family principality news from camp."),
 ("1805-08-10","TALLEYRAND","Boulogne","Boulogne","To Talleyrand","Empire","austerlitz-1805","Boulogne to Rhine: the turn decided."),
 ("1805-08-14","DECR",None,"Paris","To Decrès","Empire","austerlitz-1805","Villeneuve's fleet awaited in vain."),
 ("1805-09-01","JOSEPH",None,"Strasbourg","To Prince Joseph","Grande Armée","austerlitz-1805","Paris left to Joseph; the army marches."),
 ("1805-10-02","BAVARIA",None,"Ludwigsburg","To the Elector of Bavaria","Grande Armée","austerlitz-1805","Bavaria allied mid-march."),
 ("1805-10-02","JOSEPHINE",None,"Elchingen","To Josephine","Grande Armée","austerlitz-1805","Ulm encircled: Mack's army in the net."),
 ("1805-11-02","RUSSIA",None,"Linz","To the Emperor of Russia","Grande Armée","austerlitz-1805","A letter to the Tsar before the shock."),
 ("1805-11-01","TALLEYRAND",None,"Linz","To Talleyrand","Grande Armée","austerlitz-1805","Vienna taken; Austerlitz ahead."),
 ("1805-12-02","JOSEPH",None,"Schönbrunn","To Prince Joseph","Grande Armée","austerlitz-1805","Austerlitz eve, from imperial headquarters."),
 ("1805-12-02","TALLEYRAND",None,"Schönbrunn","To Talleyrand","Grande Armée","austerlitz-1805","Eve of battle diplomacy."),
 ("1805-12-01","JOSEPH",None,"Austerlitz","To Prince Joseph","Grande Armée","austerlitz-1805","After the sun of Austerlitz: victory announced. FIX3DEC"),
 ("1805-12-01","BERTHIER",None,"Schönbrunn","To Marshal Berthier","Grande Armée","austerlitz-1805","Orders after the victory."),
 ("1805-12-01","EUGENE",None,"Munich","To Prince Eugène","Grande Armée","austerlitz-1805","Italy secured by the Danube victory."),
 ("1805-12-25","JOSEPH",None,"Schönbrunn","To Prince Joseph","Grande Armée","austerlitz-1805","Christmas with Pressburg peace."),
 ("1805-12-14","TALLEYRAND",None,"Austerlitz","To Talleyrand","Grande Armée","austerlitz-1805","Austerlitz reported to diplomacy."),
 ("1806-01-01","EUGENE","Stuttgard","Stuttgart","To Prince Eugène","Empire","jena-1806","New kingdoms ordered from Stuttgart."),
 ("1806-01-12","JOSEPH",None,"Munich","To Prince Joseph","Empire","jena-1806","Pressburg peace: Austria pays, Naples falls to Joseph."),
 ("1806-01-24","AUGEREAU",None,"Paris","To Marshal Augereau","Empire","jena-1806","Marshals placed for peace."),
 ("1806-04-10","BERTHIER","St. Cloud","St. Cloud","To Marshal Berthier","Empire","jena-1806","Army administration in peace."),
 ("1806-04-22","NAPLES",None,"St. Cloud","To the King of Naples","Empire","jena-1806","Joseph's throne instructed from Paris."),
 ("1806-05-10","CHAMPIGNY",None,"St. Cloud","To Champagny","Empire","jena-1806","Interior administration."),
 ("1806-05-10","EUGENE",None,"St. Cloud","To Prince Eugène","Empire","jena-1806","Italy governed from Paris."),
 ("1806-05-01","ELIZA",None,"St. Cloud","To Princess Eliza","Empire","jena-1806","Tuscany's princess managed."),
 ("1806-05-10","NAPLES",None,"St. Cloud","To the King of Naples","Empire","jena-1806","Naples: taxes, troops, obedience."),
 ("1806-05-13","JUNOT",None,"Paris","To Gen. Junot","Empire","jena-1806","Portugal watched."),
 ("1806-05-16","FESCH",None,"Paris","To Cardinal Fesch","Empire","jena-1806","Rome and Paris: the Concordat strained."),
 ("1806-06-10","TALLEYRAND",None,"St. Cloud","To Talleyrand","Empire","jena-1806","Prussia drifting to war."),
 ("1806-06-10","NAPLES",None,"St. Cloud","To the King of Naples","Empire","jena-1806","More demands on Joseph."),
 ("1806-06-10","HOLLAND",None,"St. Cloud","To the King of Holland","Empire","jena-1806","Louis warned: Prussia chooses war."),
 ("1806-06-19","TALLEYRAND",None,"Paris","To Talleyrand","Empire","jena-1806","Ultimatum season."),
 ("1806-07-02","NAPLES",None,"St. Cloud","To the King of Naples","Empire","jena-1806","Summer orders to Naples."),
 ("1806-07-26","PORTALIS",None,"St. Cloud","To Portalis","Empire","jena-1806","Cults administered."),
 ("1806-08-14","EUGENE",None,"Paris","To Prince Eugène","Empire","jena-1806","Italy braced for war."),
 ("1806-08-07","TALLEYRAND",None,"St. Cloud","To Talleyrand","Empire","jena-1806","Prussian ultimatum answered."),
 ("1806-08-10","EUGENE",None,"St. Cloud","To Prince Eugène","Empire","jena-1806","War coming: Italy alerted."),
 ("1806-08-30","AUGUSTA",None,"St. Cloud","To Princess Augusta","Empire","jena-1806","Bavarian alliance flattered."),
 ("1806-09-10","BERTHIER",None,"St. Cloud","To Marshal Berthier","Empire","jena-1806","The army gathers for Prussia."),
 ("1806-09-07","NAPLES",None,"St. Cloud","To the King of Naples","Empire","jena-1806","Hold Naples while Prussia falls."),
 ("1806-09-10","HOLLAND",None,"St. Cloud","To the King of Holland","Empire","jena-1806","Louis: guard the coasts."),
 ("1806-10-14","TALLEYRAND","Dessau","Dessau","To Talleyrand","Grande Armée","jena-1806","Jena won: diplomacy follows cannon."),
 ("1806-10-15","EMPRESS",None,"Jena","To the Empress","Grande Armée","jena-1806","Jena eve: writing Josephine before the battle."),
 ("1806-10-01","FERDINAND",None,"Berlin","To Princess Ferdinand","Grande Armée","jena-1806","From occupied Berlin: courtesy to the defeated dynasty."),
 ("1806-10-25","NAPLES",None,"Paris","To the King of Naples","Grande Armée","jena-1806","Berlin's fall announced to Joseph."),
 ("1806-11-21","EMPRESS",None,"Küstrin","To the Empress","Grande Armée","jena-1806","Pursuit into Poland."),
 ("1806-11-27","Empress",None,"Paris","To the Empress","Grande Armée","jena-1806","Poland: mud, cold, billets."),
 ("1806-12-01","GAUDIN",None,"Posen","To Gaudin","Grande Armée","eylau-1807","Finances follow the eagles into Poland."),
 ("1806-12-01","SELIM",None,"Posen","To Sultan Selim","Grande Armée","eylau-1807","The eastern alliance: Paris courts Constantinople."),
 ("1806-12-14","EMPRESS",None,"Posen","To the Empress","Grande Armée","eylau-1807","Posen winter: love amid snow."),
 ("1806-12-31","EMPRESS",None,"Pultusk","To the Empress","Grande Armée","eylau-1807","Winter war: Pultusk's bloody snow."),
 ("1807-01-02","HOLLAND",None,"Warsaw","To the King of Holland","Grande Armée","eylau-1807","Louis ordered across winter Poland."),
 ("1807-01-16","EMPRESS",None,"Warsaw","To the Empress","Grande Armée","eylau-1807","Warsaw separation lengthens."),
 ("1807-01-14","NAPLES",None,"Warsaw","To the King of Naples","Grande Armée","eylau-1807","Joseph summoned east in thought."),
 ("1807-01-07","LEBRUN",None,"Paris","To Lebrun","Grande Armée","eylau-1807","Paris governed from Warsaw snow."),
 ("1807-01-01","BERTHIER",None,"Warsaw","To Marshal Berthier","Grande Armée","eylau-1807","Winter quarters staff work."),
 ("1807-01-01","CHAMPAGNY",None,"Warsaw","To Champagny","Grande Armée","eylau-1807","Interior from Poland."),
 ("1807-01-14","CAMBAC",None,"Warsaw","To Cambacérès","Grande Armée","eylau-1807","Arch-chancellor instructed."),
 ("1807-02-01","TALLEYRAND","Arensdorf","Arensdorf","To Talleyrand","Grande Armée","eylau-1807","Eylau eve diplomacy."),
 ("1807-02-05","CAMBAC",None,"Paris","To Cambacérès","Grande Armée","eylau-1807","Paris after Eylau's butchery."),
 ("1807-02-03","EMPRESS",None,"Eylau","To the Empress","Grande Armée","eylau-1807","Eylau: victory remains, at cost."),
 ("1807-02-01","PRUSSIA",None,"Eylau","To the King of Prussia","Grande Armée","eylau-1807","Peace offered to a beaten king."),
 ("1807-02-28","FOUCHE",None,"Osterode","To Fouché","Grande Armée","eylau-1807","Paris police from snowy Osterode."),
 ("1807-03-02","EUGENE",None,"Osterode","To Prince Eugène","Grande Armée","eylau-1807","Italy held while Poland bleeds."),
 ("1807-03-01","TALLEYRAND",None,"Osterode","To Talleyrand","Grande Armée","eylau-1807","Spring diplomacy from Osterode."),
 ("1807-03-01","NAPLES",None,"Osterode","To the King of Naples","Grande Armée","eylau-1807","Joseph reminded from the snow."),
 ("1807-03-14","FOUCHE",None,"Osterode","To Fouché","Grande Armée","eylau-1807","Conspiracies watched."),
 ("1807-03-01","LEFEBVRE",None,"Osterode","To Marshal Lefebvre","Grande Armée","eylau-1807","Danzig must fall: siege orders."),
 ("1807-03-22","DECRES",None,"Osterode","To Decrès","Grande Armée","eylau-1807","The navy ordered from a Polish mill town."),
 ("1807-03-25","DEJEAN",None,"Paris","To Gen. Dejean","Grande Armée","eylau-1807","War administration."),
 ("1807-04-04","EUGENE",None,"Finckenstein","To Prince Eugène","Grande Armée","friedland-1807","Italy governed from a Polish château."),
 ("1807-04-14","NAPLES",None,"Finckenstein","To the King of Naples","Grande Armée","friedland-1807","Joseph's kingdom supervised."),
 ("1807-04-01","FOUCHE",None,"Finckenstein","To Fouché","Grande Armée","friedland-1807","Police before the spring campaign."),
 ("1807-05-01","BERTHIER",None,"Finckenstein","To Marshal Berthier","Grande Armée","friedland-1807","Spring campaign prepared."),
 ("1807-05-01","CAMBAC",None,"Finckenstein","To Cambacérès","Grande Armée","friedland-1807","Paris briefed for Friedland."),
 ("1807-06-02","EMPRESS",None,"Tilsit","To the Empress","Grande Armée","tilsit-1807","Friedland eve from Tilsit."),
 ("1807-06-02","TALLEYRAND",None,"Tilsit","To Talleyrand","Grande Armée","tilsit-1807","Diplomacy ready for victory."),
 ("1807-06-22","CAMBAC",None,"Tilsit","To Cambacérès","Grande Armée","tilsit-1807","Friedland won: Paris told first."),
 ("1807-06-22","CAMBAC",None,"Tilsit","To Cambacérès","Grande Armée","tilsit-1807","Settlement drafting."),
 ("1807-06-25","SAVARY",None,"Tilsit","To Gen. Savary","Grande Armée","tilsit-1807","Niemen raft politics: emperors meet."),
 ("1807-07-14","RUSSIA",None,"Königsberg","To the Emperor of Russia","Grande Armée","tilsit-1807","New ally flattered after Tilsit."),
 ("1807-07-22","TALLEYRAND",None,"Dresden","To Talleyrand","Grande Armée","tilsit-1807","Return journey diplomacy."),
 ("1807-08-02","BERNADOTTE",None,"St. Cloud","To Marshal Bernadotte","Empire","tilsit-1807","Hanseatic governance."),
 ("1807-08-04","EUGENE",None,"Paris","To Prince Eugène","Empire","tilsit-1807","Italy after Tilsit."),
 ("1807-08-10","GAUDIN",None,"St. Cloud","To Gaudin","Empire","tilsit-1807","Tilsit indemnities banked."),
 ("1807-08-26","SAVARY",None,"St. Cloud","To Gen. Savary","Empire","tilsit-1807","Gendarmerie of the peace."),
 ("1807-09-22","CHAMPAGNY",None,"Fontainebleau","To Champagny","Empire","spain-1808","Portugal crisis brewing."),
 ("1807-09-24","NEUFCHATEL",None,"Paris","To the Prince of Neufchâtel","Empire","spain-1808","Berthier's principality confirmed."),
 ("1807-09-25","DUROC",None,"Fontainebleau","To Gen. Duroc","Empire","spain-1808","Palace marshal's errands."),
 ("1807-10-07","CLARKE",None,"Paris","To Gen. Clarke","Empire","spain-1808","War ministry before Portugal."),
 ("1807-10-14","JUNOT",None,"Fontainebleau","To Gen. Junot","Empire","spain-1808","Portugal doomed: Junot marches on Lisbon."),
 ("1807-11-01","EUGENE",None,"Fontainebleau","To Eugène","Empire","spain-1808","Italy steady for the Spanish venture."),
 ("1807-12-01","JOSEPH",None,"Milan","To King Joseph","Empire","spain-1808","Italy to Naples' king — soon Spain's."),
 ("1808-02-17","FOUCH",None,"Paris","To Fouché","Empire","spain-1808","Spain plotted by police reports."),
 ("1808-03-27","HOLLAND",None,"St. Cloud","To the King of Holland","Empire","spain-1808","Louis dragged toward Spain."),
 ("1808-04-01","TALLEYRAND",None,"Bayonne","To Talleyrand","Empire","spain-1808","The Spanish throne deals begin."),
 ("1808-04-12","BERG",None,"Bayonne","To the Grand Duke of Berg","Empire","spain-1808","Murat positioned for Madrid."),
 ("1808-04-01","NAPLES",None,"Bayonne","To the King of Naples","Empire","spain-1808","Joseph's fate decided at Bayonne."),
 ("1808-05-03","HOLLAND",None,"Bayonne","To the King of Holland","Empire","spain-1808","Dos de Mayo news reaches Bayonne."),
 ("1808-05-01","TALLEYRAND",None,"Bayonne","To Talleyrand","Empire","spain-1808","Ferdinand cajoled, Charles managed."),
 ("1808-05-01","CHAMPAGNY",None,"Bayonne","To Champagny","Empire","spain-1808","Bayonne paperwork of usurpation."),
 ("1808-06-03","CAULAINCOURT",None,"Bayonne","To Caulaincourt","Empire","spain-1808","Russia watched while Spain burns."),
 ("1808-07-07","RUSSIA",None,"Bayonne","To the Emperor of Russia","Empire","erfurt-1808","Tilsit anniversary greetings to Alexander."),
 ("1808-08-10","CHAMPAGNY",None,"Nantes","To Champagny","Empire","spain-1808","Bailén shock administered from Nantes."),
 ("1808-09-14","PRUSSIA",None,"Paris","To the Queen of Prussia","Empire","erfurt-1808","Erfurt prologue: courtesy before the congress."),
 ("1808-09-10","RUSSIA",None,"St. Cloud","To the Emperor of Russia","Empire","erfurt-1808","Alexander summoned to Erfurt."),
 ("1808-10-02","HOLLAND",None,"Erfurt","To the King of Holland","Empire","erfurt-1808","From the congress: Louis instructed."),
 ("1808-10-01","EMPRESS",None,"Erfurt","To the Empress","Empire","erfurt-1808","Congress splendour described."),
 ("1808-10-14","SPAIN",None,"Erfurt","To the King of Spain","Empire","erfurt-1808","Joseph's Spanish crown confirmed from Erfurt."),
 ("1808-11-01","SPAIN",None,"Bayonne","To the King of Spain","Empire","spain-1808","Return to finish Spain in person."),
 ("1808-11-26","CLARKE",None,"Paris","To Gen. Clarke","Empire","spain-1808","War ministry before the Spanish march."),
 ("1808-12-01","JOSEPHINE",None,"Benavente","To Josephine","Empire","spain-1808","Madrid retaken: writing from the pursuit."),
 ("1809-01-01","CHAMPAGNY",None,"Benavente","To Champagny","Empire","wagram-1809","Austria rearms: Paris warned at New Year."),
 ("1809-01-01","EUGENE",None,"Paris","To Prince Eugène","Empire","wagram-1809","Italy braced for Austria."),
 ("1809-03-21","HOLLAND",None,"Malmaison","To Louis of Holland","Empire","wagram-1809","Louis scolded: blockade and conscription."),
 ("1809-05-01","JOSEPHINE",None,"Enns","To Josephine","Empire","wagram-1809","Danube campaign: Enns, then Vienna."),
 ("1809-05-19","CLARKE",None,"Paris","To Gen. Clarke","Empire","wagram-1809","Essling's cost counted."),
 ("1809-07-01","JOSEPHINE",None,"Schönbrunn","To Josephine","Empire","wagram-1809","Lobau island: Wagram prepared."),
 ("1809-06-01","CLARKE",None,"Schönbrunn","To Gen. Clarke","Empire","wagram-1809","After Essling: holding the Danube."),
 ("1809-07-14","DENMARK",None,"Schönbrunn","To the King of Denmark","Empire","wagram-1809","Northern ally kept."),
 ("1809-07-01","FOUCH",None,"Schönbrunn","To Fouché","Empire","wagram-1809","Wagram aftermath policed."),
 ("1809-07-10","LEFEBVRE",None,"Schönbrunn","To Marshal Lefebvre","Empire","wagram-1809","Bavaria rewarded."),
 ("1809-07-22","AUSTRIA",None,"Schönbrunn","To the Emperor of Austria","Empire","wagram-1809","Wagram won: peace feelers to Vienna."),
 ("1809-08-01","CLARKE",None,"Schönbrunn","To Gen. Clarke","Empire","wagram-1809","Occupation administration."),
 ("1809-08-18","CHAMPAGNY",None,"Paris","To Champagny","Empire","wagram-1809","Schönbrunn dictated, Paris executed."),
 ("1809-09-01","FOUCH",None,"Schönbrunn","To Fouché","Empire","wagram-1809","Walcheren scare managed."),
 ("1809-09-01","MARINE",None,"Schönbrunn","To the Marine Minister","Empire","wagram-1809","Antwerp saved by the navy."),
 ("1809-10-28","ALDINI",None,"Paris","To Count Aldini","Empire","wagram-1809","Italy settled after Wagram."),
 ("1809-11-22","VICEROY",None,"Varis","To the Viceroy of Italy","Empire","wagram-1809","Eugène instructed for the new order."),
 ("1797-02-01","THE DIRECTORY","TOLENTINO","Tolentino","To the Directory","Army of Italy","campo-1797","Tolentino: the Pope pays for peace."),
 ("1797-03-21","GORITZ",None,"Gorizia","To the people of Gorizia","Army of Italy","campo-1797","Carinthia entered: proclamation to Gorizia."),
 ("1797-09-13","FOREIGN AFFAIRS",None,"Passariano","To the Foreign Minister","Army of Italy","campo-1797","Corfu maxim: never abandon the Mediterranean."),

]

BARCH = "Bingham, Selection (London, 1884), Vols. II–III — public domain"
BURL2 = "https://archive.org/details/cu31924024332243"
BURL3 = "https://archive.org/details/cu31924024332250"

BARCH1 = "Bingham, Selection (London, 1884), Vol. I — public domain"
BURL1 = "https://archive.org/details/acp7797.0001.001.umich.edu"

for iso, key, placekey, loc, toline, fac, eid, ctx in SEL:
    r = find_b(iso, key, placekey)
    cert = "approximate" if r.get("fuzzy_date") else "certain"
    if "FIX3DEC" in ctx:
        ctx = ctx.replace(" FIX3DEC", "")
        iso, cert = "1805-12-03", "certain"
        ctx = "Dateline OCR reads Dec 1; content ('decisive battle yesterday' = 2 Dec) fixes to 3 Dec. " + ctx
    arch, url = (BARCH1, BURL1) if iso < "1803" else (BARCH, BURL2 if iso < "1810" else BURL3)
    push(out, NAP, fac, iso, None, loc if loc != "Headquarters" or r["place"] else (r["place"] or "Headquarters"),
         "“" + clean(r["body"]) + "”",
         f"{toline}, {r['place'] or loc}, {iso}",
         arch, url,
         "letter", ctx, eid, cert=cert)
print("bingham empire:", len(out))

# ---------- Tarbell proclamations ----------
T = json.load(open("sources/tarbell_picked.json"))

def find_t(frag, iso=None):
    c = [r for r in T if frag.lower() in (r["key"] + " " + r["title"]).lower()]
    if iso:
        c = [r for r in c if r["iso"] == iso] or c
    if not c:
        raise SystemExit(f"NO MATCH t {frag}")
    return c[0]

TARCH = "Tarbell, Napoleon's Addresses (1897) — public domain translations"
TURL = TARBELL_URL

# (title-frag, iso, cert, loc, event, context, display-title)
TSEL = [
 ("milan", "1796-05-15", "certain", "Milan", "italy-1796", "Milan entered: the proclamation posted.", "Proclamation on Entering Milan"),
 ("brescia", "1796-05-28", "certain", "Brescia", "italy-1796", "Brescia entered.", "Proclamation on Entering Brescia"),
 ("mantua", "1796-11-06", "certain", "Mantua", "italy-1796", "Mantua besieged: address to the troops.", "Address During the Siege of Mantua"),
 ("cisalpine", "1797-11-17", "certain", "Milan", "campo-1797", "A sister republic proclaimed.", "Proclamation to the Cisalpine Republic"),
 ("egypt-embark", "1798-06-01", "approximate", "Toulon", "egypt-1798", "Embarkation address; month certain, day approximate.", "Proclamation on Embarking for Egypt"),
 ("egyptians", "1798-07-01", "approximate", "Alexandria", "egypt-1798", "To the Egyptians: liberation proclaimed.", "Proclamation to the Egyptians"),
 ("egypt-govt", "1798-07-27", "certain", "Cairo", "egypt-1798", "Occupation organised by decree.", "Order on the Government of Egypt"),
 ("acre-abandon", "1799-05-01", "approximate", "Acre", "egypt-1798", "Acre abandoned: proclamation to the army.", "Proclamation on Abandoning Acre"),
 ("departure-fr", "1799-08-01", "approximate", "Alexandria", "egypt-1798", "Farewell to the army of Egypt.", "Proclamation on Departure for France"),
 ("army-east", "1799-11-01", "approximate", "Paris", "brumaire-1799", "Consulate: address to the army of the East.", "Proclamation to the Army of the East"),
 ("marengo-eve", "1800-06-01", "approximate", "Marengo", "marengo-1800", "Marengo eve proclamation.", "Proclamation before Marengo"),
 ("marengo-eve", "1800-06-01", "approximate", "Marengo", "marengo-1800", "Marengo eve proclamation.", "Proclamation before Marengo"),
 ("marengo-austria", "1800-06-01", "approximate", "Marengo", "marengo-1800", "To Austria, on the field.", "Letter to the Emperor of Austria"),
 ("colors", "1804-12-03", "certain", "Paris", "empire-1804", "Eagles presented: 'Behold your colors!'", "Address on Presenting the Colors"),
 ("england-king", "1805-01-02", "certain", "Paris", "austerlitz-1805", "Peace offered to England: 'my brother'.", "Letter to the King of England"),
 ("jerome", "1805-05-06", "certain", "Paris", "austerlitz-1805", "Jérôme's American marriage forbidden.", "Letter to Jérôme Bonaparte"),
 ("third-coalition", "1805-09-01", "approximate", "Strasbourg", "austerlitz-1805", "Third Coalition war proclaimed.", "Proclamation on the Third Coalition"),
 ("ulm", "1805-10-01", "approximate", "Ulm", "austerlitz-1805", "Ulm fallen: address to the Austrians.", "Address after Ulm"),
 ("austerlitz-after", "1805-12-03", "certain", "Austerlitz", "austerlitz-1805", "'I am satisfied with you': the bulletin-proclamation.", "Proclamation after Austerlitz"),
 ("tippoo", "1799-01-25", "certain", "Cairo", "egypt-1798", "To Mysore against England.", "Letter to Tippoo Sahib"),
 ("pressburg", "1805-12-26", "certain", "Schönbrunn", "austerlitz-1805", "Pressburg peace announced.", "Address on Peace with Austria"),
 ("feb1806", "1806-02-01", "approximate", "Paris", "jena-1806", "1806 proclamation to the soldiers.", "Proclamation to the Soldiers"),
 ("captive", "1806-10-15", "certain", "Jena", "jena-1806", "Magnanimity after Jena.", "Address to the Captive Officers"),
 ("warsaw", "1807-01-01", "approximate", "Warsaw", "eylau-1807", "Warsaw proclamation.", "Proclamation before Entering Warsaw"),
 ("prussia-eylau", "1807-02-01", "approximate", "Eylau", "eylau-1807", "Peace offered to Prussia after Eylau; month certain.", "Letter to the King of Prussia"),
 ("friedland", "1807-06-24", "certain", "Friedland", "tilsit-1807", "Friedland victory proclaimed.", "Proclamation after Friedland"),
 ("champagny07", "1807-11-15", "certain", "Fontainebleau", "tilsit-1807", "Tilsit settlement administered.", "Letter to Champagny"),
 ("spaniards", "1808-06-02", "certain", "Bayonne", "spain-1808", "Joseph's crown announced to Spain.", "Proclamation to the Spaniards"),
 ("austria08", "1808-10-01", "approximate", "Erfurt", "erfurt-1808", "Erfurt letter to Austria.", "Letter to the Emperor of Austria"),
 ("spanish-people", "1808-12-01", "approximate", "Madrid", "spain-1808", "Madrid taken: address to Spaniards.", "Proclamation to the Spanish People"),
 ("morla", "1808-12-03", "certain", "Madrid", "spain-1808", "Madrid summoned: surrender by 6 a.m.", "Summons to Morla"),
 ("eckmuhl", "1809-04-01", "approximate", "Eckmühl", "wagram-1809", "Eckmühl proclamation.", "Proclamation before Eckmühl"),
 ("ratisbon", "1809-04-01", "approximate", "Ratisbon", "wagram-1809", "Ratisbon proclamation.", "Proclamation at Ratisbon"),
 ("vienna09", "1809-05-01", "approximate", "Vienna", "wagram-1809", "Vienna entered.", "Address on Entering Vienna"),
 ("hungarians", "1809-05-01", "approximate", "Vienna", "wagram-1809", "Hungarians summoned against Austria.", "Proclamation to the Hungarians"),
]

for frag, iso, cert, loc, eid, ctx, dtitle in TSEL:
    r = find_t(frag, iso if not cert == "approximate" else None)
    push(out, NAP, "Grande Armée" if eid in ("austerlitz-1805","jena-1806","eylau-1807","tilsit-1807","wagram-1809","spain-1808","erfurt-1808") else "Empire",
         iso, None, loc, "“" + clean(r["body"], 340) + "”", dtitle + f", {iso}",
         TARCH, TURL, "proclamation", ctx, eid, cert=cert)

# ---------- Josephine 1804-1809 ----------
J = json.load(open("sources/josephine1856.json"))

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

JSEL = [
 ("1804-08-03", None, "empire-1804", "Boulogne waters: hoping they do her good."),
 ("1804-10-06", None, "empire-1804", "Treves road: audiences refused on his behalf."),
 ("1805-10-23", None, "austerlitz-1805", "Augsburg: rested, off to Munich."),
 ("1805-11-16", None, "austerlitz-1805", "Vienna: arranging her journey east."),
 ("1805-12-03", None, "austerlitz-1805", "Austerlitz eve dispatch: Lebrun carries the news."),
 ("1805-12-05", None, "austerlitz-1805", "Truce concluded; Russians going home."),
 ("1805-12-07", None, "austerlitz-1805", "Armistice; peace within eight days."),
 ("1806-10-23", None, "jena-1806", "Wittenberg: prosperous affairs, off to Potsdam."),
 ("1806-11-02", None, "jena-1806", "Berlin: superb weather, bulletins tell the rest."),
 ("1806-12-02", None, "eylau-1807", "Posen, Austerlitz anniversary: ball, rain, love."),
 ("1806-12-15", None, "eylau-1807", "Posen: off to Warsaw, back in a fortnight."),
 ("1806-12-20", None, "eylau-1807", "Warsaw two days: affairs go well."),
 ("1806-12-29", None, "eylau-1807", "Golymin barn: beaten Russians, thirty guns."),
 ("1807-01-18", None, "eylau-1807", "Warsaw: separation prolonged, return deferred."),
 ("1807-02-09", None, "eylau-1807", "Eylau, day after: victory remains, many men lost."),
 ("1807-02-11", None, "eylau-1807", "Eylau: memorable battle, at cost."),
 ("1807-02-14", None, "eylau-1807", "Still at Eylau: dead and wounded as far as eyes see."),
 ("1807-03-02", None, "eylau-1807", "Osterode: reproaching himself for silence."),
 ("1807-06-25", None, "tilsit-1807", "Tilsit: just met Emperor Alexander — handsome, amiable, youthful."),
 ("1808-04-16", None, "spain-1808", "Bayonne: melancholy rough road."),
 ("1808-04-23", None, "spain-1808", "Bayonne: Hortense a mother again."),
 ("1808-09-29", None, "erfurt-1808", "Erfurt: slight cold, pleased with the Emperor."),
 ("1809-04-18", None, "wagram-1809", "Donauwörth, 4 a.m.: everything in motion."),
 ("1809-05-12", None, "wagram-1809", "Schönbrunn: master of Vienna."),
 ("1809-08-26", None, "wagram-1809", "Schönbrunn: fleshy, fresh and blooming reports."),
]

for iso, tlab, eid, ctx in JSEL:
    c = [r for r in J if r["iso"] == iso]
    if not c:
        raise SystemExit(f"NO MATCH j {iso}")
    r = c[0]
    lab = tlab or ev_label_hour(r.get("hour")) or "TIME UNCERTAIN"
    push(out, dict(NAP, faction="Empire"), "Empire", iso, lab,
         r["place"].title(), "“" + clean(r["body"]) + "”",
         f"To Josephine, {r['place'].title()}, {iso}",
         "Confidential Correspondence of Napoleon and Josephine (London, 1856) — public domain",
         JOSEPHINE_URL, "love letter", ctx, eid)

import sys as _s
json.dump(out, open("data/nap_empire.json", "w"), ensure_ascii=False, indent=1)
print("empire records:", len(out))
